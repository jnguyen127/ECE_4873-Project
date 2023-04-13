import json
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, USER_TABLE

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
USER_TABLE = dynamodb.Table(USER_TABLE)

def lambda_handler(event, context):
    results = USER_TABLE.scan()['Items']
    for x in results:
        if x['Creation Time'] <= time.time() - 86400 and x['Status'] != "Confirmed": # Checks the past 24 hours
            USER_TABLE.delete_item(
                Key= {
                    'Email': x['Email']
                }
            )
    return {
        'statusCode': 200,
        'body': json.dumps('Checked accounts')
    }
