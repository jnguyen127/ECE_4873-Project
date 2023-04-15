#!flask/bin/python
import boto3
import time
import random
from datetime import datetime, timedelta
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, USER_TABLE

############################################################################################
##################################### Useful variables #####################################
############################################################################################
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
USER_TABLE = dynamodb.Table(USER_TABLE)

if __name__ == '__main__':
    while True:
        email = ""
        tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
            'Items'][0]['Device Name'].upper() + "_TABLE"
        DATA_TABLE = dynamodb.Table(tableName) # - timedelta(seconds=<offset>) 
        # Current time - (optional) timedelta. 
        # Make sure that whatever is printed is the correct time zone as the web application. 
        # Similarly to the microcontroller, the time zone could be off.
        # Just uncomment "- timedelta(seconds=<offset>)" and replace "<offset>" 
        # with the number of seconds you want to offset by.
        offsetTime = datetime.now()
        offsetTime = str(offsetTime.strftime(
            "%m-%d-%y %H:%M:%S"))  # Time Formated
        print(offsetTime)
        random_number = str(random.uniform(829.3499756, 831.249939))
        DATA_TABLE.put_item(
            Item={
                "Timestamp": offsetTime,
                "Location": "Room 1",
                "Power": random_number,
            }
        )
        time.sleep(1)
