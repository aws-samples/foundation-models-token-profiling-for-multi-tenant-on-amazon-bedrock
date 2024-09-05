from aws_cdk import (
    # Duration,
    Stack,
    App,
    aws_s3 as s3,
    aws_cloudfront as cf,
    RemovalPolicy,
    aws_s3_deployment as s3deploy,
    aws_cloudfront_origins as origins,
    CfnOutput
)
from constructs import Construct

class StaticExampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self,"site_bucket",
                           encryption=s3.BucketEncryption.S3_MANAGED,
                           block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                           auto_delete_objects=True,
                           removal_policy=RemovalPolicy.DESTROY
                           )
        s3deploy.BucketDeployment(self, "DeployWebsite",
                                      sources=[s3deploy.Source.asset("./../website")],
                                      destination_bucket=bucket
                                  )
        oai = cf.OriginAccessIdentity( self,"My-OAI",comment="My OAI for the S3 Website")
        bucket.grant_read(oai)
        cdn = cf.Distribution(self, "CDN",
                        default_root_object='index.html',
                        price_class=cf.PriceClass.PRICE_CLASS_ALL,
                        default_behavior=cf.BehaviorOptions(
                            origin=origins.S3Origin(
                                bucket, 
                                origin_path=None, 
                                origin_access_identity=oai, 
                                custom_headers={"Access-Control-Allow-Origin":"*"}
                                ),
                            origin_request_policy=cf.OriginRequestPolicy.CORS_S3_ORIGIN, 
                            viewer_protocol_policy=cf.ViewerProtocolPolicy.ALLOW_ALL,
                            response_headers_policy=cf.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT,
                            cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
                            allowed_methods=cf.AllowedMethods.ALLOW_GET_HEAD)
                        )
        CfnOutput(self, "CloudfrontDomainName", value=cdn.distribution_domain_name)
