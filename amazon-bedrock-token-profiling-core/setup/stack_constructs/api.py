from constructs import Construct
from aws_cdk import (
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda as lambda_
)

class API(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        api_gw: apigw.LambdaRestApi,
        dependencies: list = []
    ):
        super().__init__(scope, id)

        self.id = id
        self.api_gw = api_gw
        self.dependencies = dependencies

    def build(
        self,
        lambda_function: lambda_.Function,
        route: str,
        method: str,
        auth: apigw.CfnAuthorizer,
        validator: bool = False
    ):
        # Add method/route

        lambda_function.add_permission(
            id=f"{self.id}_{route}_permission",
            action="lambda:InvokeFunction",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=self.api_gw.arn_for_execute_api(
                stage="*",
                method=method,
                path=f"/{route}"
            )
        )

        resourse = self.api_gw.root.add_resource(route)
        authorizer_id=auth.attr_authorizer_id

        if validator:
            method = resourse.add_method(
                http_method=method,
                #authorization_type=apigw.AuthorizationType.COGNITO,
                #authorizer=authorizer_id,
                integration=apigw.LambdaIntegration(lambda_function),
                api_key_required=False,
                request_parameters={
                    "method.request.header.Auth": True,
                    #"method.request.header.streaming": False,
                    #"method.request.header.type": False
                },
                request_validator_options={
                    "request_validator_name": "parameter-validator",
                    "validate_request_parameters": True,
                    "validate_request_body": False
                },
                method_responses=[
                    apigw.MethodResponse(
                        status_code="401",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                        },
                        response_models={
                            "application/json": apigw.Model.ERROR_MODEL,
                        }
                    )
                ]
            )
            method_resource = method.node.find_child('Resource')
            method_resource.add_property_override('AuthorizationType', 'COGNITO_USER_POOLS')
            method_resource.add_property_override('AuthorizerId', authorizer_id)
        else:
            method = resourse.add_method(
                http_method=method,
                #authorization_type=apigw.AuthorizationType.COGNITO,
                #authorizer=authorizer_id,
                integration=apigw.LambdaIntegration(lambda_function),
                api_key_required=False,
                method_responses=[
                    apigw.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Origin": True,
                        },
                        response_models={
                            "application/json": apigw.Model.EMPTY_MODEL,
                        }
                    )
                ]
            )
            method_resource = method.node.find_child('Resource')
            method_resource.add_property_override('AuthorizationType', 'COGNITO_USER_POOLS')
            method_resource.add_property_override('AuthorizerId', authorizer_id)

        return resourse
