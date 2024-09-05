from aws_cdk import (
    Stack,
    App,
    aws_cognito as cognito,
    CfnOutput
)
from constructs import Construct

class Cognito(Construct):

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        
    def build(self):
        pool = cognito.UserPool(self, "Pool")
        client = pool.add_client("app-client",
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL,cognito.OAuthScope.OPENID],
                #callback_urls=["https://my-app-domain.com/welcome"],
                #logout_urls=["https://my-app-domain.com/signin"]
            )
        )
        CfnOutput(self, "UserPoolId", value=pool.user_pool_id).override_logical_id('UserPoolId')
        CfnOutput(self, "UserPoolClientId", value=client.user_pool_client_id).override_logical_id('UserPoolAppClientId')
        return pool
