from aws_cdk import (
    core,
    aws_dynamodb as ddb,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_iam as iam,
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
            code=_lambda.Code.asset("lambda"),
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