# Amazon Bedrock Token Profiling For Multi Tenant

## Architecture

![Architecture](images/architecture.png)

## Getting started

### Deployment
1. Install the required module
```
cd ./amazon-bedrock-token-profiling-for-multi-tenant/amazon-bedrock-token-profiling-core
pip install -r requirements.txt
```

2. Edit ./setup/configs.json to type the STACK_PREFIX
```
[
  {
    "STACK_PREFIX": "<type your prefix here>",
    "BEDROCK_ENDPOINT": "https://bedrock.{}.amazonaws.com",
    "BEDROCK_RUNTIME_ENDPOINT": "https://bedrock-runtime.{}.amazonaws.com",
    "BEDROCK_REQUIREMENTS": "boto3>=1.34.94 awscli>=1.32.94 botocore>=1.34.94",
    "LANGCHAIN_REQUIREMENTS": "aws-lambda-powertools langchain==0.1.16 pydantic PyYaml",
    "PANDAS_REQUIREMENTS": "pandas",
    "SAGEMAKER_ENDPOINTS": "",
    "VPC_CIDR": "10.10.0.0/16",
    "API_THROTTLING_RATE": 10000,
    "API_BURST_RATE": 5000
  }
]
```


3. Deploy the core components. After deploy successfully, your API URL will show in the output. Please record it for later use. 
```
chmod +x deploy_stack.sh
./deploy_stack.sh
```
The core components includes the following resources:
* VPC endpoints and networking configuration
* IAM role
* Cognito user pool with app client
* API gateway
* Lambda layers and functions
* DynamoDB table
* EventBridge scheduler

4. Deploy the demo website components
```
cd ./amazon-bedrock-token-profiling-for-multi-tenant/amazon-bedrock-token-profiling-web
chmod +x deploy_stack.sh
./deploy_stack.sh
```
The demo website components includes the following resources:
* Cloudfront distribution
* S3 bucket for web hosting
* A demo website

5. After deploy successfully, you can navigate to [API Gateway Console](https://us-east-1.console.aws.amazon.com/apigateway/main/apis?api=unselected&region=us-east-1) to check your API, the name would be  **[your stack prefix]_bedrock_api_gw**. You can found there are three resources for this API Gateway: invoke_model, cost_track_manual and ddb_cost_retrieval.  

![api gateway resources](images/api-gw.png)

6. Navigate to the [Cognito User Pool](https://us-east-1.console.aws.amazon.com/cognito/v2/idp/user-pools?region=us-east-1), you should see a user pool be created and named with your prefix in the beginning.

![cognito user pool 1](images/cognito-user-pool-1.png)

7. Click into the cognito user pool record its user pool id, app client id for later used.

![cognito user pool 2](images/cognito-user-pool-2.png)

![cognito user pool 3](images/cognito-user-pool-3.png)

8. Create the users by yourself. You need to create two general users and one admin user id with the email `admin@amazon.com` for later demo used.

![cognito user pool 4](images/cognito-user-pool-4.png)

9. Navigate to the [CloudFront Distribution](https://us-east-1.console.aws.amazon.com/cloudfront/v4/home?region=us-east-1#/distributions), you should see a distrubution be created and named with your prefix in the beginning. 

10. Copy the distribution domain name then open in your browser. You can see the demo website.

![cloudfront](images/cloudfront.png)

![website-index](images/website-index.png)

11. On the demo website, click the **Credential** button on the top-right. Then field your user pool id, app client id and api url. Then click save.

![website-credential](images/website-credential.png)

12. Expand the action menu on the top-left. Select **sign in** to login. You will see some basic information if login successfully.

![website-login](images/website-login.png)

13. You can type the question in the text field to check the response.

![website-invoke-model](images/website-invoke-model.png)

14. If you would like to check the cost for each user, you need to login as admin user.

15. As you login as admin, you can see the **Manually aggregate the metrics** and **Check the cost** buttons.

![website-login-admin](images/website-login-admin.png)

16. Click **Manually aggregate the metrics** button to aggregate the cost, you should see the "Calculation Finished" message.

![website-aggregate-cost](images/website-aggregate-cost.png)

17. Click **Check the cost** button to check the results.

![website-check-cost](images/website-check-cost.png)

### Experiance with API

1. Please download the [Postman](https://www.postman.com/downloads/) for experiancing.

2. Let's try the **invoke_model** api first.  For this solution, you can invoke two models from Amazon Bedrock by the following model ids.

- amazon.titan-embed-text-v1

- anthropic.claude-3-sonnet-20240229-v1:0


3. Create a POST request on Postman and paste the API URL. The URL should be `https://{API URL}/invoke_model?model_id={model_id}`.

4. Put the **Auth*** in the header. Paste the id token you got from the Cognito after login.

![postman-invoke-model-1](images/postman-invoke-model-1.png)

5. Type the following body content then send the request. You will see the model response.

```
{"inputs": "What is Amazon.com?", "parameters": {"maxTokenCount": 4096, "temperature": 0.8}}
```

![postman-invoke-model-2](images/postman-invoke-model-2.png)

6. You can change the model_id or auth for other users to check the different response.

7. Now, we can use **cost_track_manual** api to aggregate the cost for each user. Type the API URL for request as the following. You do not need to type user_id and body content for this api. You can get the "Calculation Finished!" as response.

`https://{API URL}/cost_track_manual`

![postman-cost-track-manual](images/postman-cost-track-manual.png)

8. Now, the cost should be aggregated then record into the dynamoDB table. Let's use **ddb_cost_retrieval** api to get the cost result. Type the API URL for request as the following. You do not need to type user_id and body content for this api. You can get the cost result as response.

`https://{API URL}/ddb_cost_retrieval`

![postman-ddb-cost-retrieval](images/postman-ddb-cost-retrieval.png)

## Reference

* https://github.com/aws-samples/bedrock-multi-tenant-saas

# amazon-bedrock-token-profiling-for-multi-tenant
