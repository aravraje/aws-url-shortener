import os
import boto3
import json
from time import sleep
from hashlib import blake2b

MAX_RETRIES, BACKOFF = int(os.environ['MAX_RETRIES']), int(os.environ['BACKOFF'])

ddb = boto3.client('dynamodb')

def lambda_handler(event, context):
    # If the request is GET, unshorten and return the long URL
    if event['httpMethod'] == 'GET':
        return unshorten(event)
    
    multiValueHeaders = event['multiValueHeaders']
    body = json.loads(event['body'])
    
    long_url = body['url_long']
    cdn_prefix = body['cdn_prefix']
    client_ip = multiValueHeaders['X-Forwarded-For'][0].split(",")[0]  #CloudFront appends Client IP to the 'X-Forwarded-For' header
    
    # Shorten the long URL
    return shorten(long_url, cdn_prefix, client_ip)
    
def shorten(long_url, cdn_prefix, client_ip):
    ''' 
    Initialize blake2b hashing with a custom digest size;
    salt and personalization are added for more randomized hashing;
    '''
    h = blake2b(digest_size=int(os.environ['HASH_DIGEST_SIZE']), salt=long_url[:16].encode(), person=client_ip.encode())
    
    # Get the global counter value from DDB
    res = ddb_helper("UPDATE")
    
    if not res[0]:
        return res[1]
            
    # Use the global counter value to generate randomized hash value    
    h.update(res[0].encode())
    
    payload = {
        'short_url': {
            'S': h.hexdigest()  # Randomized hash value is used as the short_url
        },
        'long_url': {
            'S': long_url
        }
    }
    
    # Store the Long and Short URL in the DDB table
    result = ddb_helper("PUT", payload)
    
    # If DDB PUT is successful, return the Long and Short URL back to the client
    if result['statusCode'] == '200':
        result['body'] = json.dumps(
            {
                "url_long": long_url,
                "url_short": cdn_prefix + "/" + h.hexdigest()
            }
        )
    
    return result
        
def unshorten(event):
    payload = {
        'short_url': {
            'S': event['path'].split('/')[2]
        }
    }
    
    # Get the Long URL from the DDB table
    return ddb_helper("GET", payload)
    
def ddb_helper(method, payload=None):
    for num_retry in range(MAX_RETRIES):
        try:
            if method == "PUT":
                response = ddb.put_item(
                    TableName=os.environ['URL_SHORTENER_MAPPING_TABLE'],
                    Item=payload
                )
                
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {
                        'statusCode': '200',
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*' 
                        }
                    }
            
            if method == "GET":
                response = ddb.get_item(
                    TableName=os.environ['URL_SHORTENER_MAPPING_TABLE'],
                    Key=payload
                )
                
                # If DDB response is empty
                if 'Item' not in response:
                    return {
                        'statusCode': '404',
                        'headers': {
                            'Access-Control-Allow-Origin': '*' 
                        }
                    }
                
                # Return the Long URL as a redirect request
                return {
                    'statusCode': '301',
                    'headers': {
                        'Location': response['Item']['long_url']['S'],
                        'Access-Control-Allow-Origin': '*' 
                    }
                }
            
            if method == "UPDATE":
                # Increment the atomic counter by 1 and return its updated value
                response = ddb.update_item(
                    TableName=os.environ["URL_SHORTENER_COUNTER_TABLE"],
                    Key={
                        "id": {
                            "S": "counter"
                        }
                    },
                    UpdateExpression="ADD val :q",
                    ExpressionAttributeValues={
                        ':q': {"N": "1"}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                
                # Return the counter value in the form of [success, failure] 
                return [response['Attributes']['val']['N'], None]
        
        except Exception as e:
            print(f"Encountered the below exception during DynamoDB {method} API. Retrying..\n{e}")
            
        finally:
            # Exponential Backoff before retrying
            sleep((num_retry * BACKOFF) / 1000)
            
    print(f"Couldn't complete the request after {MAX_RETRIES} retries. Returning HTTP 500 back to the client.")
        
    failure = {
        'statusCode': '500',
        'headers': {
            'Access-Control-Allow-Origin': '*' 
        }
    }
    
    if method == "UPDATE":
        return [None, failure]
    
    return failure