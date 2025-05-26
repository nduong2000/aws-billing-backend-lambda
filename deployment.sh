#!/bin/bash

# Build and deploy Lambda function
set -e

# Variables
AWS_ACCOUNT_ID="734846753975"
AWS_REGION="us-east-1"
ECR_REPO_NAME="medical-billing-api"
FUNCTION_NAME="medical-billing-api"
LAMBDA_ROLE_ARN="arn:aws:iam::734846753975:role/medical-billing-lambda-role"

# Step 1: Login to ECR first
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 2: Create ECR repository if it doesn't exist
echo "Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION}

# Step 3: Build and push Docker image directly to ECR
echo "Building and pushing Docker image for linux/amd64..."

# Remove any existing builder and create a new one
docker buildx rm lambda-builder 2>/dev/null || true
docker buildx create --name lambda-builder --driver docker-container --use --bootstrap

# Build and push with explicit output format
docker buildx build \
    --platform linux/amd64 \
    --output type=image,name=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest,push=true \
    --provenance=false \
    --sbom=false \
    .

# Step 4: Create the environment variables file
echo "Creating environment variables file..."
cat > env-vars.json << EOF
{
  "Variables": {
    "BEDROCK_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0",
    "AUDIT_MODEL": "anthropic.claude-3-haiku-20240307-v1:0",
    "NODE_ENV": "production",
    "LOG_LEVEL": "INFO"
  }
}
EOF

# Step 5: Check if function exists and create or update accordingly
echo "Checking if Lambda function exists..."
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
    echo "Function exists, updating code..."
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --image-uri ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest \
        --region ${AWS_REGION}
    
    # Wait for the function to be updated
    echo "Waiting for function to be active..."
    aws lambda wait function-updated \
        --function-name ${FUNCTION_NAME} \
        --region ${AWS_REGION}
    
    # Update function configuration
    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --environment file://env-vars.json \
        --memory-size 3008 \
        --timeout 900 \
        --region ${AWS_REGION}
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --package-type Image \
        --code ImageUri=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest \
        --role ${LAMBDA_ROLE_ARN} \
        --memory-size 3008 \
        --timeout 900 \
        --environment file://env-vars.json \
        --region ${AWS_REGION} \
        --architectures x86_64
fi

# Step 6: Wait for the function to be active
echo "Waiting for function to be active..."
aws lambda wait function-active \
    --function-name ${FUNCTION_NAME} \
    --region ${AWS_REGION}

# Step 7: Create a function URL (optional, for testing)
echo "Creating function URL..."
aws lambda create-function-url-config \
    --function-name ${FUNCTION_NAME} \
    --auth-type NONE \
    --cors '{
        "AllowCredentials": false,
        "AllowHeaders": ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token"],
        "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "AllowOrigins": ["*"],
        "ExposeHeaders": ["date", "keep-alive"],
        "MaxAge": 86400
    }' \
    --region ${AWS_REGION} 2>/dev/null || \
echo "Function URL already exists"

# Get the function URL
FUNCTION_URL=$(aws lambda get-function-url-config \
    --function-name ${FUNCTION_NAME} \
    --region ${AWS_REGION} \
    --query 'FunctionUrl' --output text 2>/dev/null || echo "No function URL configured")

echo "Deployment complete!"
echo "Function URL: ${FUNCTION_URL}"
echo ""
echo "Test the function with:"
echo "curl -X GET ${FUNCTION_URL}"
echo ""
echo "Or test the health endpoint:"
echo "curl -X GET ${FUNCTION_URL}health"

# Clean up
rm -f env-vars.json
