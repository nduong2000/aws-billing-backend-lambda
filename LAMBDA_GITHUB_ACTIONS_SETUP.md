# AWS Lambda GitHub Actions Deployment Setup

This guide will help you set up automated deployment of your Medical Billing Lambda function to AWS using GitHub Actions.

## 🚀 Overview

The GitHub Actions workflow will automatically:
- Build your Python Lambda function as a Docker container
- Push the image to Amazon ECR
- Deploy/update the Lambda function
- Configure Function URLs and permissions
- Run health checks and provide deployment summaries

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **GitHub Repository** with your Lambda code
3. **Existing AWS IAM User**: `github-actions-medical-billing`

## 🔧 Setup Instructions

### Step 1: Update IAM Permissions

Your existing IAM user `github-actions-medical-billing` needs additional permissions for Lambda deployment. 

**Current Policy** (S3 + CloudFront only):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket",
                "s3:PutBucketPolicy", "s3:GetBucketLocation", "s3:CreateBucket",
                "s3:PutBucketWebsite", "s3:PutBucketPublicAccessBlock", "s3:GetBucketAcl"
            ],
            "Resource": [
                "arn:aws:s3:::medical-billing-frontend-*",
                "arn:aws:s3:::medical-billing-frontend-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation",
                "cloudfront:GetDistribution",
                "cloudfront:ListDistributions"
            ],
            "Resource": "*"
        }
    ]
}
```

**Updated Policy** (Add Lambda + ECR permissions):

1. Go to AWS Console → IAM → Users → `github-actions-medical-billing`
2. Click "Add permissions" → "Attach policies directly"
3. Create a new policy with the content from `github-actions-lambda-policy.json`
4. Or use the AWS CLI:

```bash
aws iam put-user-policy \
  --user-name github-actions-medical-billing \
  --policy-name LambdaDeploymentPolicy \
  --policy-document file://github-actions-lambda-policy.json
```

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

**Required Secrets:**
- `AWS_ACCESS_KEY_ID` - Your existing AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - Your existing AWS secret access key

**Note**: You can reuse the same credentials from your frontend deployment since we've added the Lambda permissions to the same user.

### Step 3: Verify Current Configuration

Your current Lambda function details:
- **Function Name**: `medical-billing-api`
- **Current URL**: `https://phslqkfk47zphdmvbufwi3oiz40ugscg.lambda-url.us-east-1.on.aws/`
- **Region**: `us-east-1`
- **Memory**: 3008 MB
- **Timeout**: 900 seconds

The GitHub Actions workflow will update this existing function.

### Step 4: Test the Workflow

1. **Commit and push** the workflow file:
   ```bash
   git add .github/workflows/deploy-lambda.yml
   git add github-actions-lambda-policy.json
   git add LAMBDA_GITHUB_ACTIONS_SETUP.md
   git commit -m "feat: add GitHub Actions Lambda deployment workflow"
   git push origin main
   ```

2. **Monitor the deployment**:
   - Go to GitHub → Actions tab
   - Watch the "Deploy Lambda Function" workflow
   - Check the deployment summary for the new Function URL

3. **Manual trigger** (optional):
   - Go to Actions → Deploy Lambda Function
   - Click "Run workflow"

## 🔄 Workflow Triggers

### Automatic Deployment
- **Push to main/master**: Deploys to production
- **Pull Request**: Runs tests only (no deployment)

### Manual Deployment
- **Workflow Dispatch**: Manual trigger via GitHub UI

## 📁 Workflow Features

### 🐳 **Container Deployment**
- Builds Docker image for Lambda
- Pushes to Amazon ECR
- Uses multi-platform builds (linux/amd64)
- Implements layer caching for faster builds

### 🔧 **Infrastructure Management**
- Creates ECR repository if needed
- Creates Lambda execution role if needed
- Configures Function URLs automatically
- Sets up proper permissions

### 🧪 **Testing & Validation**
- Runs basic import tests
- Performs health checks post-deployment
- Provides detailed deployment summaries

### 🔐 **Security**
- Uses least-privilege IAM policies
- Secure credential handling via GitHub Secrets
- Proper role-based access for Lambda execution

## 🚨 Troubleshooting

### Common Issues:

1. **Permission Errors**:
   ```
   Error: User: arn:aws:iam::ACCOUNT:user/github-actions-medical-billing is not authorized to perform: lambda:UpdateFunctionCode
   ```
   **Solution**: Ensure the updated IAM policy is attached

2. **ECR Authentication Issues**:
   ```
   Error: no basic auth credentials
   ```
   **Solution**: Check AWS credentials in GitHub secrets

3. **Docker Build Failures**:
   ```
   Error: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
   ```
   **Solution**: Check requirements.txt and Dockerfile syntax

4. **Lambda Function Not Found**:
   ```
   Error: The resource you requested does not exist
   ```
   **Solution**: The workflow will create the function automatically

### Debug Commands:

```bash
# Test AWS credentials locally
aws sts get-caller-identity

# Check Lambda function status
aws lambda get-function --function-name medical-billing-api

# Check ECR repository
aws ecr describe-repositories --repository-names medical-billing-lambda

# Test Function URL
curl https://your-function-url.lambda-url.us-east-1.on.aws/health
```

## 📈 Advanced Configuration

### Environment Variables

The workflow sets these environment variables:
```json
{
  "CLAUDE_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "CLAUDE_HAIKU_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0",
  "BEDROCK_REGION": "us-east-1"
}
```

### Custom Configuration

You can modify the workflow to:
- Change memory/timeout settings
- Add additional environment variables
- Configure VPC settings
- Set up CloudWatch alarms

### Multiple Environments

To deploy to staging/production:
1. Create separate workflows for each environment
2. Use different function names and ECR repositories
3. Configure environment-specific secrets

## 🎉 Expected Results

After successful deployment:

1. **Updated Lambda Function**: Your existing function will be updated with the latest code
2. **Function URL**: Same URL will continue working (or new one if recreated)
3. **ECR Repository**: `medical-billing-lambda` repository created in ECR
4. **Deployment Summary**: Detailed information in GitHub Actions summary

### Sample Deployment Summary:
```
🚀 Lambda Deployment Successful!

📱 Function Details:
- Function Name: medical-billing-api
- Function URL: https://xyz.lambda-url.us-east-1.on.aws/
- Region: us-east-1
- Image: 123456789.dkr.ecr.us-east-1.amazonaws.com/medical-billing-lambda:abc123

🔧 Configuration:
- Memory: 3008 MB
- Timeout: 900 seconds
- Runtime: Python (Container)

🧪 Testing:
- Health Check: https://xyz.lambda-url.us-east-1.on.aws/health
- API Docs: https://xyz.lambda-url.us-east-1.on.aws/docs
```

## 🔐 Security Best Practices

1. **Rotate AWS access keys** regularly
2. **Use least privilege** IAM policies
3. **Monitor CloudWatch logs** for security events
4. **Enable AWS CloudTrail** for audit logging
5. **Review deployment logs** regularly

## 📞 Support

If you encounter issues:

1. Check the GitHub Actions logs
2. Review AWS CloudWatch logs for the Lambda function
3. Verify IAM permissions are correctly configured
4. Test AWS credentials locally

---

**Happy Deploying! 🚀** 