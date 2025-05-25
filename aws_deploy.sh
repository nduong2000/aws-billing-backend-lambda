#!/bin/bash

# Configure AWS CLI
aws configure set aws_access_key_id AKIASAXGHXN7QIKIR34X
aws configure set aws_secret_access_key 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
aws configure set default.region us-east-1

echo "AWS CLI configured."

# Create IAM policy for Bedrock access
aws iam create-policy \
  --policy-name MedicalBillingBedrockPolicy \
  --policy-document file://aws-policy.json

echo "IAM policy created."

# Create Elastic Beanstalk application
aws elasticbeanstalk create-application \
  --application-name medical-billing-api \
  --description "Medical Billing Backend API"

echo "Elastic Beanstalk application created."

# Create application version
zip -r application.zip . -x "*.git*" "*.DS_Store" "node_modules/*" "__pycache__/*" "*.pyc" "venv/*" "env/*"

echo "Application files zipped."

# Create S3 bucket for deployment packages
aws s3 mb s3://medical-billing-api-deploy

echo "S3 bucket created."

# Upload application to S3
aws s3 cp application.zip s3://medical-billing-api-deploy/

echo "Application uploaded to S3."

# Create application version in Elastic Beanstalk
aws elasticbeanstalk create-application-version \
  --application-name medical-billing-api \
  --version-label v1 \
  --source-bundle S3Bucket="medical-billing-api-deploy",S3Key="application.zip"

echo "Application version created in Elastic Beanstalk."

# Create environment and deploy
aws elasticbeanstalk create-environment \
  --application-name medical-billing-api \
  --environment-name medical-billing-api-prod \
  --solution-stack-name "64bit Amazon Linux 2 v3.5.0 running Python 3.8" \
  --version-label v1 \
  --option-settings file://eb-options.json

echo "Elastic Beanstalk environment creation started."

# Wait for environment to be ready
aws elasticbeanstalk wait environment-updated \
  --environment-name medical-billing-api-prod

echo "Environment ready!"

# Get the environment URL
url=$(aws elasticbeanstalk describe-environments \
  --environment-names medical-billing-api-prod \
  --query "Environments[0].CNAME" \
  --output text)

echo "Deployment complete! Your application is available at: http://$url"
