import boto3
from time import sleep
from crhelper import CfnResource
from bs4 import BeautifulSoup

helper = CfnResource()
s3 = boto3.client("s3")

MAX_RETRIES, BACKOFF = 3, 100


@helper.create
@helper.update
def update_html(event, context):

    for num_retry in range(MAX_RETRIES):
        try:
            # Read the HTML file from S3
            get_response = s3.get_object(
                Bucket=event["ResourceProperties"]["S3_BUCKET"],
                Key=event["ResourceProperties"]["S3_KEY"],
            )

            html = get_response["Body"].read()

            # Update the AJAX POST URL in the HTML file with the APIGW Shorten endpoint
            soup = BeautifulSoup(html, "html.parser")
            post_url = soup.find("div", id="post_url")
            post_url.string = event["ResourceProperties"]["POST_URL"]

            # Upload the HTML file back to the S3 bucket
            put_response = s3.put_object(
                Bucket=event["ResourceProperties"]["S3_BUCKET"],
                Key=event["ResourceProperties"]["S3_KEY"],
                Body=soup.prettify(),
                ContentType=get_response["ContentType"],
            )

            if put_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return

        except Exception as e:
            print(f"Encountered the below exception while processing the request. Retrying..\n{e}")

        finally:
            # Exponential Backoff before retrying
            sleep((num_retry * BACKOFF) / 1000)

    print(f"Couldn't complete the request after {MAX_RETRIES} retries. Returning an error back to CloudFormation.")

    raise Exception("There was an error in updating the HTML file in S3 with API GW endpoint. See the Lambda Custom Resource CW Logs for more details.")


@helper.delete
def no_op(event, context):
    pass


def lambda_handler(event, context):
    print(f"CloudFormation Event: {event}")
    helper(event, context)
