from constructs import Construct
from aws_cdk import (
    aws_iam as iam
)

class IAM(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            dependencies: list = []
    ):
        super().__init__(scope, id)

        self.id = id
        self.dependencies = dependencies

    def build(self):
        # ==================================================
        # ================= IAM ROLE =======================
        # ==================================================
        s3_policy_doc = iam.PolicyDocument()
        s3_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowS3Access',
                effect=iam.Effect.ALLOW,
                actions=['s3:PutObject', 's3:DeleteObject', 's3:ListBucket', 's3:GetObject'],
                resources=['*']))
        s3_policy = iam.ManagedPolicy(
            self,
            'S3IAMPolicy',
            managed_policy_name='S3Policy',
            document=s3_policy_doc,
            description='S3 IAM Policy')

        ec2_policy_doc = iam.PolicyDocument()
        ec2_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowEC2Access',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ec2:AssignPrivateIpAddresses',
                    'ec2:CreateNetworkInterface',
                    'ec2:DeleteNetworkInterface',
                    'ec2:DescribeNetworkInterfaces',
                    'ec2:DescribeSecurityGroups',
                    'ec2:DescribeSubnets',
                    'ec2:DescribeVpcs',
                    'ec2:UnassignPrivateIpAddresses',
                    'ec2:*VpcEndpoint*'
                ],
                resources=['*']))
        ec2_policy = iam.ManagedPolicy(
            self,
            'EC2IAMPolicy',
            managed_policy_name='EC2Policy',
            document=ec2_policy_doc,
            description='EC2 IAM Policy')

        lambda_policy_doc = iam.PolicyDocument()
        lambda_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowLambdaInvoke',
                effect=iam.Effect.ALLOW,
                actions=['lambda:InvokeFunction'],
                resources=['*']))
        lambda_policy = iam.ManagedPolicy(
            self,
            'LambdaIAMPolicy',
            managed_policy_name='LambdaPolicy',
            document=lambda_policy_doc,
            description='Lambda IAM Policy')

        dynamodb_policy_doc = iam.PolicyDocument()
        dynamodb_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowDynamoDBAccess',
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:BatchGetItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Scan"
                    ],
                resources=['*']))
        dynamodb_policy = iam.ManagedPolicy(
            self,
            'DynamoDBIAMPolicy',
            managed_policy_name='DynamoDBPolicy',
            document=dynamodb_policy_doc,
            description='DynamoDB IAM Policy')

        bedrock_policy_doc = iam.PolicyDocument()
        bedrock_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowSTSAssumeRole',
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                resources=['*']),
            iam.PolicyStatement(
                sid='AllowBedrockAccess',
                effect=iam.Effect.ALLOW,
                actions=["bedrock:*"],
                resources=['*']))
        bedrock_policy = iam.ManagedPolicy(
            self,
            'BedrockIAMPolicy',
            managed_policy_name='BedrockPolicy',
            document=bedrock_policy_doc,
            description='Bedrock IAM Policy')

        sagemaker_policy_doc = iam.PolicyDocument()
        sagemaker_policy_doc.add_statements(
            iam.PolicyStatement(
                sid='AllowSageMakerAccess',
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:*"],
                resources=['*']))
        sagemaker_policy = iam.ManagedPolicy(
            self,
            'SageMakerIAMPolicy',
            managed_policy_name='SageMakerPolicy',
            document=sagemaker_policy_doc,
                description='SageMaker IAM Policy')

        lambda_role = iam.Role(
            self,
            id=f"{self.id}_role",
            assumed_by=iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambdaExecute"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess"),
                s3_policy,
                ec2_policy,
                lambda_policy,
                dynamodb_policy,
                bedrock_policy,
                sagemaker_policy
            ],
        )

        for el in self.dependencies:
            lambda_role.node.add_dependency(el)

        return lambda_role
