#!/bin/bash

# Quick fix for Lambda ECR permissions
# This script adds ECR permissions to your existing Lambda execution role

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Fixing Lambda ECR Permissions${NC}"
echo "=================================="

ROLE_NAME="medical-billing-lambda-role"
POLICY_NAME="LambdaECRPolicy"

# Check if role exists
if ! aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    echo -e "${RED}❌ Lambda execution role '$ROLE_NAME' not found${NC}"
    echo "Please create the role first or run the GitHub Actions workflow."
    exit 1
fi

echo -e "${GREEN}✅ Found Lambda execution role: $ROLE_NAME${NC}"

# Create ECR policy document
cat > lambda-ecr-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
EOF

echo "Adding ECR permissions to Lambda execution role..."

# Add the policy to the role
if aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name $POLICY_NAME \
    --policy-document file://lambda-ecr-policy.json; then
    echo -e "${GREEN}✅ ECR permissions added successfully${NC}"
else
    echo -e "${RED}❌ Failed to add ECR permissions${NC}"
    exit 1
fi

# Clean up
rm -f lambda-ecr-policy.json

echo ""
echo -e "${YELLOW}🧪 Testing permissions...${NC}"

# List role policies to verify
echo "Current policies attached to role:"
aws iam list-role-policies --role-name $ROLE_NAME --query 'PolicyNames' --output table

echo ""
echo -e "${GREEN}✅ Fix complete!${NC}"
echo "Your Lambda function should now be able to pull images from ECR."
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Re-run your GitHub Actions workflow"
echo "2. Or manually update the Lambda function:"
echo "   aws lambda update-function-code \\"
echo "     --function-name medical-billing-api \\"
echo "     --image-uri 734846753975.dkr.ecr.us-east-1.amazonaws.com/medical-billing-lambda:dc9a5beca514658a692973cbce4f1497e1753d5e" 