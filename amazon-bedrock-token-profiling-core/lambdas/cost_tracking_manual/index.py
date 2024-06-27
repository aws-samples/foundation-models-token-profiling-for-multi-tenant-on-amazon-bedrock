import boto3
import datetime
from io import StringIO
import logging
import os
import pytz
import traceback
from utils import run_query, results_to_df, calculate_cost
import json

logger = logging.getLogger(__name__)
if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

log_group_name_api = os.environ.get("LOG_GROUP_API", None)
s3_bucket = os.environ.get("S3_BUCKET", None)

s3_resource = boto3.resource('s3')

QUERY_API = """
fields 
message.tenant_id as tenant_id,
message.requestId as request_id,
message.region as region,
message.model_id as model_id,
message.inputTokens as input_tokens,
message.outputTokens as output_tokens
| filter level = "INFO"
"""

def process_event(event):
    print(event)
    try:
        date = datetime.datetime.now(pytz.UTC)
        date = date.strftime("%Y-%m-%d")
        print(date)

        # querying the cloudwatch logs from the API
        query_results_api = run_query(QUERY_API, log_group_name_api, date)
        df_bedrock_cost_tracking = results_to_df(query_results_api)

        if len(df_bedrock_cost_tracking) > 0:
            # Apply the calculate_cost function to the DataFrame
            df_bedrock_cost_tracking[["input_tokens", "output_tokens", "input_cost", "output_cost", "invocations"]] = df_bedrock_cost_tracking.apply(
                calculate_cost, axis=1, result_type="expand"
            )

            # aggregate cost for each model_id
            df_bedrock_cost_tracking_aggregated = df_bedrock_cost_tracking.groupby(["tenant_id", "model_id"]).sum()[
                ["input_tokens", "output_tokens", "input_cost", "output_cost", "invocations"]
            ]

            df_bedrock_cost_tracking_aggregated["date"] = date

            flat_df = df_bedrock_cost_tracking_aggregated.reset_index()
            print(df_bedrock_cost_tracking_aggregated)
            dynamodb_client = boto3.client('dynamodb')
            ddb_table = os.environ.get("TABLE_NAME")
            for index, row in flat_df.iterrows():
                #print({"tenant_id": row[0], "model_id": row[1], 'input_tokens': row[2], "output_tokens": row[3], 'input_cost': row[4], "output_cost": row[5], "invocations": row[6], 'date': row[7]})
                pk=str(row[0])+"-"+str(row[1])
                dynamodb_client.put_item(
                    TableName=ddb_table,
                    Item={
                        'pk': {'S': pk},
                        'name': {'S': str(row[0])},
                        'model_id': {'S': str(row[1])},
                        'input_tokens': {'S': str(row[2])},
                        'output_tokens': {'S': str(row[3])},
                        'input_cost': {'S': str(row[4])},
                        'output_cost': {'S': str(row[5])},
                        'invocations': {'S': str(row[6])},
                        'date': {'S': str(row[7])},
                    }
                )
            logger.info(df_bedrock_cost_tracking_aggregated.to_string())

            csv_buffer = StringIO()
            df_bedrock_cost_tracking_aggregated.to_csv(csv_buffer)

            file_name = f"{date}.csv"
            s3_resource.Object(s3_bucket, file_name).put(Body=csv_buffer.getvalue())
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)

        raise e

def lambda_handler(event, context):
    try:
        process_event(event)
        return {
            "statusCode": 200, 
            'headers': {
                    'Access-Control-Allow-Origin': '*'
            }, 
            "body": json.dumps({"body": "Calculation Finished!"}) 
            
        }
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)
        return {"statusCode": 500, "body": str(e)}
