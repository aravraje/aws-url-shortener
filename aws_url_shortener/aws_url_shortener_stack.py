from aws_cdk import (
    core,
    aws_dynamodb as ddb,
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