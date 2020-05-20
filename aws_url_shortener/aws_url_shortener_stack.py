from aws_cdk import (
    core,
    aws_dynamodb as ddb,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cf,
)

class AwsUrlShortenerStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # DDB table to store the Long and Short URLs with Short URL as the partition key
        url_mapping_table = ddb.Table(
            self,
            "url_shortener_mapping_table",
            partition_key=ddb.Attribute(
                name="short_url", 
                type=ddb.AttributeType.STRING
            ),
            read_capacity=10,
            write_capacity=10,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        # AutoScaling of RCUs with a Target Utilization of 70%
        url_mapping_table.auto_scale_read_capacity(
            min_capacity=10, max_capacity=40000
        ).scale_on_utilization(target_utilization_percent=70)

        # AutoScaling of WCUs with a Target Utilization of 70%
        url_mapping_table.auto_scale_write_capacity(
            min_capacity=10, max_capacity=40000
        ).scale_on_utilization(target_utilization_percent=70)

        # DDB table to keep track of an Atomic Counter used for generating Short URLs
        url_counter_table = ddb.Table(
            self,
            "url_shortener_counter_table",
            partition_key=ddb.Attribute(
                name="id",
                type=ddb.AttributeType.STRING
            ),
            read_capacity=10,
            write_capacity=10,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        # AutoScaling of RCUs with a Target Utilization of 70%
        url_counter_table.auto_scale_read_capacity(
            min_capacity=10, max_capacity=40000
        ).scale_on_utilization(target_utilization_percent=70)

        # AutoScaling of WCUs with a Target Utilization of 70%
        url_counter_table.auto_scale_write_capacity(
            min_capacity=10, max_capacity=40000
        ).scale_on_utilization(target_utilization_percent=70)

        # Lambda function with custom code to handle shortening/unshortening logic
        url_lambda = _lambda.Function(
            self,
            "url_shortener_lambda",
            code=_lambda.Code.asset("lambda_proxy"),
            handler="lambda_function.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            timeout=core.Duration.seconds(10),
            environment={
                "BACKOFF": "25",
                "HASH_DIGEST_SIZE": "8",
                "MAX_RETRIES": "3",
                "URL_SHORTENER_MAPPING_TABLE": url_mapping_table.table_name,
                "URL_SHORTENER_COUNTER_TABLE": url_counter_table.table_name,
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        # A Custom IAM Policy statement to grant DDB access to the Lambda function
        ddb_policy_statement = iam.PolicyStatement(
            actions=["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem"],
            effect=iam.Effect.ALLOW,
            resources=[url_mapping_table.table_arn, url_counter_table.table_arn],
        )

        # Attaching DDB Policy statement with the Lambda IAM Role
        url_lambda.add_to_role_policy(ddb_policy_statement)

        # Including X-Requested-With to the default CORS headers list
        headers = apigw.Cors.DEFAULT_HEADERS
        headers.append('X-Requested-With')

        # API Gateway endpoint to serve Shorten/Unshorten APIs
        url_rest_api = apigw.RestApi(
            self,
            "url_shortener_API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_headers=headers,
                allow_methods=["POST", "GET", "OPTIONS"],
                status_code=200,
            ),
        )

        # Shorten API using POST and Lambda proxy
        url_rest_api.root.add_resource(
            path_part="shorten",
        ).add_method(
            http_method="POST",
            request_models={
                "application/json": apigw.Model.EMPTY_MODEL,
            },
            integration=apigw.LambdaIntegration(
                handler=url_lambda,
                proxy=True,
                allow_test_invoke=True,
            ),
        )

        # Unshorten API using GET and Lambda proxy
        url_rest_api.root.add_resource(
            path_part="unshorten",
        ).add_resource(
            path_part="{shorturl}"
        ).add_method(
            http_method="GET",
            request_models={
                "application/json": apigw.Model.EMPTY_MODEL,
            },
            integration=apigw.LambdaIntegration(
                handler=url_lambda,
                proxy=True,
                allow_test_invoke=True,
            ),
        )

        # S3 bucket to host the URL Shortener Static Website
        s3_web_hosting = s3.Bucket(
            self,
            "url_shortener_web_hosting_bucket",
            website_index_document="index.html",
        )

        # Uploading HTML and ICO files from local directory to S3 Static Website bucket
        s3_deploy = s3deploy.BucketDeployment(
            self,
            "website_source_files",
            sources=[s3deploy.Source.asset(
                path="website",
            )],
            destination_bucket=s3_web_hosting,
        )

        # Lambda function to integrate the API GW Shorten endpoint with the HTML file stored in S3
        cr_provider = _lambda.Function(
            self,
            "cr_provider",
            code=_lambda.Code.asset("custom_resource"),
            handler="lambda_function.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_8,
            timeout=core.Duration.minutes(1),
        )

        # A Custom IAM Policy statement to grant S3 access to the Lambda function
        lambda_cr_statement = iam.PolicyStatement(
            actions=["s3:List*", "s3:Get*", "s3:Put*"],
            effect=iam.Effect.ALLOW,
            resources=[s3_web_hosting.bucket_arn, s3_web_hosting.bucket_arn + "/*"]
        )

        cr_provider.add_to_role_policy(lambda_cr_statement)

        # CFN Custom Resource backed by Lambda
        lambda_cr = core.CustomResource(
            self,
            "lambda_cr",
            service_token=cr_provider.function_arn,
            properties={
                "S3_BUCKET": s3_web_hosting.bucket_name,
                "S3_KEY": "index.html",
                "POST_URL": url_rest_api.url + "shorten",
            },
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        # Adding dependency so that Custom Resource creation happens after files are uploaded to S3
        lambda_cr.node.add_dependency(s3_deploy)

        # CloudFront Distribution with S3 and APIGateway origins
        url_cf_distribution = cf.CloudFrontWebDistribution(
            self,
            "url_shortener_distribution",
            origin_configs=[
                cf.SourceConfiguration(
                    s3_origin_source=cf.S3OriginConfig(
                        s3_bucket_source=s3_web_hosting,
                        origin_access_identity=cf.OriginAccessIdentity(
                            self,
                            id="OAI",
                            comment="OAI that allows CloudFront to access the S3 bucket"
                        ),
                    ),
                    behaviors=[
                        cf.Behavior(
                            is_default_behavior=False,
                            path_pattern="/index.html",
                        ),
                        cf.Behavior(
                            is_default_behavior=False,
                            path_pattern="/favicon.ico",
                        ),
                    ]
                ),
                cf.SourceConfiguration(
                    custom_origin_source=cf.CustomOriginConfig(
                        domain_name=url_rest_api.url.lstrip("https://").split("/")[0],
                    ),
                    origin_path="/" + url_rest_api.deployment_stage.stage_name + "/unshorten",
                    behaviors=[
                        cf.Behavior(
                            is_default_behavior=True,
                            allowed_methods=cf.CloudFrontAllowedMethods.GET_HEAD_OPTIONS,
                        )
                    ]
                )
            ],
            price_class=cf.PriceClass.PRICE_CLASS_ALL,
            default_root_object="index.html",
        )

        # Adding the CloudFront Distribution endpoint to CFN Output
        core.CfnOutput(
            self,
            "URLShortenerWebsite",
            value=url_cf_distribution.domain_name,
        )