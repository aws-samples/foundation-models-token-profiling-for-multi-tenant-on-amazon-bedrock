#!/usr/bin/env bash

# export JSII_SILENCE_WARNING_DEPRECATED_NODE_VERSION=true

# npm install -g aws-cdk
# python3 -m venv .venv
# source .venv/bin/activate
# pip3 install -r requirements.txt


ACCOUNT_ID=$(aws sts get-caller-identity --query Account | tr -d '"')
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
GET_REGION_CMD="curl -H \"X-aws-ec2-metadata-token: $TOKEN\" http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/\(.*\)[a-z]/\1/'"
AWS_REGION=$(eval "$GET_REGION_CMD")
cd ./setup
cdk bootstrap aws://${ACCOUNT_ID}/${AWS_REGION}
cdk deploy --require-approval never
