from aws_lambda_powertools import Logger
import boto3
from botocore.config import Config
import json
from langchain_community.llms.bedrock import LLMInputOutputAdapter
import logging
import math
import os
import traceback

logger = logging.getLogger(__name__)
if len(logging.getLogger().handlers) > 0:
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

cloudwatch_logger = Logger()

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

bedrock_region = os.environ.get("BEDROCK_REGION", "us-east-1")
bedrock_url = os.environ.get("BEDROCK_URL", None)
iam_role = os.environ.get("IAM_ROLE", None)
table_name = os.environ.get("TABLE_NAME", None)
s3_bucket = os.environ.get("S3_BUCKET", None)


class BedrockInference:
    def __init__(self, bedrock_client, model_id, model_arn=None, messages_api="false"):
        self.bedrock_client = bedrock_client
        self.model_id = model_id
        self.model_arn = model_arn
        self.messages_api = messages_api
        self.input_tokens = 0
        self.output_tokens = 0

    def get_input_tokens(self):
        return self.input_tokens

    def get_output_tokens(self):
        return self.output_tokens

    def invoke_text(self, body, model_kwargs):
        try:
            provider = self.model_id.split(".")[0]
            print("provider:", provider)
            
            modelId = self.model_arn if self.model_arn is not None else self.model_id
            print("modelId:", modelId)

            if(provider=="anthropic"):
                response = self.bedrock_client.invoke_model(
                    modelId=modelId,
                    body=json.dumps(
                        {
                            "anthropic_version": "bedrock-2023-05-31",    
                            "max_tokens": 1000,
                            "messages": [{
                                    "role": "user",
                                    "content": [{ "type": "text", "text": body["inputs"]}]
                                    
                                }]
                        }),
                )
            else:
                request_body = LLMInputOutputAdapter.prepare_input(
                    provider=provider,
                    prompt=body["inputs"],
                    model_kwargs=model_kwargs)
                request_body = json.dumps(request_body)
                print("request_body:", request_body)
                response = self.bedrock_client.invoke_model(
                    body=request_body,
                    modelId=modelId,
                    accept="application/json",
                    contentType="application/json"
                )
            print("response:", response)

            response = LLMInputOutputAdapter.prepare_output(provider, response)
            answer = response["text"]
            self.input_tokens = response['usage']['prompt_tokens']
            self.output_tokens = response['usage']['completion_tokens']
            print('response before return:', answer)
            return answer
        except Exception as e:
            stacktrace = traceback.format_exc()

            logger.error(stacktrace)

            raise e



def _get_bedrock_client():
    try:
        logger.info(f"Create new client\n  Using region: {bedrock_region}")
        session_kwargs = {"region_name": bedrock_region}
        client_kwargs = {**session_kwargs}

        retry_config = Config(
            region_name=bedrock_region,
            retries={
                "max_attempts": 10,
                "mode": "standard",
            },
        )
        session = boto3.Session(**session_kwargs)

        if iam_role is not None:
            logger.info(f"Using role: {iam_role}")
            sts = session.client("sts")

            response = sts.assume_role(
                RoleArn=str(iam_role),  #
                RoleSessionName="amazon-bedrock-assume-role"
            )

            client_kwargs = dict(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken']
            )

        if bedrock_url:
            client_kwargs["endpoint_url"] = bedrock_url

        bedrock_client = session.client(
            service_name="bedrock-runtime",
            config=retry_config,
            **client_kwargs
        )

        logger.info("boto3 Bedrock client successfully created!")
        logger.info(bedrock_client._endpoint)
        return bedrock_client

    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)

        raise e

def _get_tokens(string):
    logger.info("Counting approximation tokens")

    return math.floor(len(string) / 4)

def bedrock_handler(event):
    logger.info("Bedrock Endpoint")

    model_id = event["queryStringParameters"]["model_id"]
    model_arn = event["queryStringParameters"].get("model_arn")
    tenant_id = event['requestContext']['authorizer']['claims']['cognito:username']
    bedrock_client = _get_bedrock_client()

    bedrock_inference = BedrockInference(
        bedrock_client=bedrock_client,
        model_id=model_id,
        model_arn=model_arn,
        messages_api="false"
    )


    request_id = event["requestContext"]["requestId"]

    logger.info(f"Model ID: {model_id}")
    logger.info(f"Request ID: {request_id}")

    body = json.loads(event["body"])
    model_kwargs = body.get("parameters", {})

    response = bedrock_inference.invoke_text(body, model_kwargs)
    results = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps([{"generated_text": response}])
    }
        
    logs = {
        "tenant_id": tenant_id,
        "requestId": request_id,
        "region": bedrock_region,
        "model_id": model_id,
        "inputTokens": bedrock_inference.get_input_tokens(),
        "outputTokens": bedrock_inference.get_output_tokens()
    }
    cloudwatch_logger.info(logs)
    return results

def lambda_handler(event, context):
    logger.info(str(event))
    try:
        tenant_id = event['requestContext']['authorizer']['claims']['cognito:username']
        if not tenant_id:
            logger.error("Bad Request: Header 'tenant_id' is missing")
            return {"statusCode": 400, "body": "Bad Request"}

        return bedrock_handler(event)

    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)
        return {"statusCode": 500, "body": json.dumps([{"generated_text": stacktrace}])}
