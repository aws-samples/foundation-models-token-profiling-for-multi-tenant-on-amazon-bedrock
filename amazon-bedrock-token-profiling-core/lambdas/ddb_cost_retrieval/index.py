import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr

ddb_table = os.environ.get("TABLE_NAME","saas-bedrock-cost-tracking")
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(ddb_table)
    response = table.scan()
    print(response)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({"body": response['Items']}) 
    }
