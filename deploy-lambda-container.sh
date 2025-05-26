#!/bin/bash

# Medical Billing API - Lambda Container Deployment
# This script builds and deploys the FastAPI app as a Lambda container

set -e

# Configuration
AWS_REGION="us-east-1"  # Uncommented this line
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="medical-billing-api"
LAMBDA_FUNCTION_NAME="medical-billing-api"
LAMBDA_ROLE_NAME="medical-billing-lambda-role"
API_GATEWAY_NAME="medical-billing-api-gateway"

echo "🏥 Medical Billing API - Lambda Container Deployment"
echo "================================================="
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

# Step 1: Create ECR Repository
echo "📦 Step 1: Creating ECR Repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION

# Get the repository URI
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)
echo "ECR Repository URI: $ECR_URI"

# Step 2: Login to ECR
echo ""
echo "🔐 Step 2: Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Step 3: Build Docker Image
echo ""
echo "🐳 Step 3: Building Docker Image..."
docker build --platform linux/amd64 -t $ECR_REPOSITORY_NAME:latest .

# Step 4: Tag and Push to ECR
echo ""
echo "📤 Step 4: Pushing to ECR..."
docker tag $ECR_REPOSITORY_NAME:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Step 5: Create Lambda Execution Role
echo ""
echo "🔑 Step 5: Creating Lambda Execution Role..."

# Create trust policy
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name $LAMBDA_ROLE_NAME \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --region $AWS_REGION 2>/dev/null || echo "Role already exists"

# Attach policies
aws iam attach-role-policy \
  --role-name $LAMBDA_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name $LAMBDA_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Wait for role to propagate
echo "Waiting for IAM role to propagate..."
sleep 10

# Step 6: Create or Update Lambda Function
echo ""
echo "⚡ Step 6: Creating/Updating Lambda Function..."

LAMBDA_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$LAMBDA_ROLE_NAME"

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --image-uri $ECR_URI:latest \
        --region $AWS_REGION
    
    # Wait for update to complete
    aws lambda wait function-updated \
        --function-name $LAMBDA_FUNCTION_NAME \
        --region $AWS_REGION
    
    # Update configuration - REMOVED AWS_REGION from environment variables
    aws lambda update-function-configuration \
        --function-name $LAMBDA_FUNCTION_NAME \
        --memory-size 3008 \
        --timeout 900 \
        --environment Variables="{
            BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0,
            NODE_ENV=production
        }" \
        --region $AWS_REGION
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_URI:latest \
        --role $LAMBDA_ROLE_ARN \
        --memory-size 3008 \
        --timeout 900 \
        --environment Variables="{
            BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0,
            NODE_ENV=production
        }" \
        --region $AWS_REGION
fi

# Wait for function to be active
echo "Waiting for Lambda function to be active..."
aws lambda wait function-active \
    --function-name $LAMBDA_FUNCTION_NAME \
    --region $AWS_REGION

# Step 7: Create API Gateway
echo ""
echo "🌐 Step 7: Setting up API Gateway..."

# Create REST API
API_ID=$(aws apigateway create-rest-api \
    --name $API_GATEWAY_NAME \
    --description "Medical Billing API Gateway" \
    --region $AWS_REGION \
    --query 'id' \
    --output text 2>/dev/null || \
    aws apigateway get-rest-apis \
        --region $AWS_REGION \
        --query "items[?name=='$API_GATEWAY_NAME'].id" \
        --output text | head -n1)

echo "API Gateway ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query "items[?path=='/'].id" \
    --output text)

# Create {proxy+} resource
PROXY_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part "{proxy+}" \
    --region $AWS_REGION \
    --query 'id' \
    --output text 2>/dev/null || \
    aws apigateway get-resources \
        --rest-api-id $API_ID \
        --region $AWS_REGION \
        --query "items[?pathPart=='{proxy+}'].id" \
        --output text)

# Create ANY method for {proxy+}
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $AWS_REGION

# Create Lambda integration
LAMBDA_ARN="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME"

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROXY_RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $AWS_REGION

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:$API_ID/*/*" \
    --region $AWS_REGION 2>/dev/null || echo "Permission already exists"

# Deploy API Gateway
echo "Deploying API Gateway..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $AWS_REGION

# Get the API URL
API_URL="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod"

# Clean up
rm lambda-trust-policy.json

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "API Gateway URL: $API_URL"
echo ""
echo "Your API endpoints are now available at:"
echo "  - $API_URL/api/patients"
echo "  - $API_URL/api/providers"
echo "  - $API_URL/api/claims"
echo "  - $API_URL/api/audit"
echo "  - etc."
echo ""
echo "⚠️  Update your frontend .env file:"
echo "VITE_API_URL=$API_URL/api"
echo ""
echo "📊 Monitor your Lambda function:"
echo "https://console.aws.amazon.com/lambda/home?region=$AWS_REGION#/functions/$LAMBDA_FUNCTION_NAME"