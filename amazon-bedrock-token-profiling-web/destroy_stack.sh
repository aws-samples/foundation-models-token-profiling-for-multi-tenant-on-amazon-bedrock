#!/usr/bin/env bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account | tr -d '"')
AWS_REGION=$(aws configure get region)
cd ./setup
cdk destroy
