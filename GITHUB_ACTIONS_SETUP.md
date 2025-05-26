# GitHub Actions Deployment Setup

This guide will help you set up automated deployment of your Medical Billing Frontend to AWS CloudFront using GitHub Actions.

## 🚀 Overview

The GitHub Actions workflows will automatically:
- Build your React/Vite application
- Deploy to AWS S3
- Invalidate CloudFront cache
- Provide deployment summaries and notifications

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **GitHub Repository** with your frontend code
3. **Existing AWS Infrastructure**:
   - S3 bucket for hosting
   - CloudFront distribution
   - IAM user with deployment permissions

## 🔧 Setup Instructions

### Step 1: Create AWS IAM User for GitHub Actions

Create an IAM user with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::your-production-bucket-name",
                "arn:aws:s3:::your-production-bucket-name/*",
                "arn:aws:s3:::your-staging-bucket-name",
                "arn:aws:s3:::your-staging-bucket-name/*"
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

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following **Repository Secrets**:

#### Required for Production Deployment:
- `AWS_ACCESS_KEY_ID` - Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `S3_BUCKET_NAME` - Your production S3 bucket name
- `CLOUDFRONT_DISTRIBUTION_ID` - Your production CloudFront distribution ID
- `VITE_API_URL` - Your production API URL (e.g., `https://your-api-domain.com/api`)

#### Optional for Staging Deployment:
- `S3_BUCKET_NAME_STAGING` - Your staging S3 bucket name
- `CLOUDFRONT_DISTRIBUTION_ID_STAGING` - Your staging CloudFront distribution ID
- `VITE_API_URL_STAGING` - Your staging API URL

### Step 3: Update Your Current Configuration

Based on your current `.env` file, here are the values you should use:

```bash
# Production secrets (add these to GitHub)
VITE_API_URL=https://phslqkfk47zphdmvbufwi3oiz40ugscg.lambda-url.us-east-1.on.aws/api
CLOUDFRONT_DISTRIBUTION_ID=EZWL4L4PFCCLN
S3_BUCKET_NAME=medical-billing-frontend-20250525  # Update with your actual bucket name
```

### Step 4: Create S3 Bucket (if needed)

If you need to create a new S3 bucket for production:

```bash
# Create production bucket
aws s3 mb s3://medical-billing-frontend-prod --region us-east-1

# Create staging bucket (optional)
aws s3 mb s3://medical-billing-frontend-staging --region us-east-1
```

### Step 5: Configure Branch Protection (Recommended)

1. Go to Settings → Branches
2. Add a branch protection rule for `main`/`master`
3. Enable:
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Include administrators

## 🔄 Workflow Triggers

### Production Deployment (`deploy.yml`)
- **Triggers on:**
  - Push to `main` or `master` branch
  - Manual trigger via GitHub Actions UI
- **Deploys to:** Production environment

### Staging Deployment (`deploy-staging.yml`)
- **Triggers on:**
  - Push to `develop` or `staging` branch
  - Manual trigger via GitHub Actions UI
- **Deploys to:** Staging environment

## 📁 File Structure

After setup, your repository should have:

```
.github/
└── workflows/
    ├── deploy.yml              # Production deployment
    └── deploy-staging.yml      # Staging deployment
```

## 🧪 Testing the Setup

1. **Test Staging Deployment:**
   ```bash
   git checkout -b develop
   git push origin develop
   ```

2. **Test Production Deployment:**
   ```bash
   git checkout main
   git push origin main
   ```

3. **Manual Deployment:**
   - Go to Actions tab in GitHub
   - Select the workflow
   - Click "Run workflow"

## 🔍 Monitoring Deployments

### GitHub Actions Dashboard
- View deployment status in the Actions tab
- Check logs for any errors
- Review deployment summaries

### AWS CloudWatch
- Monitor S3 upload metrics
- Check CloudFront invalidation status
- Review any error logs

## 🚨 Troubleshooting

### Common Issues:

1. **AWS Permissions Error:**
   - Verify IAM user has correct permissions
   - Check AWS credentials in GitHub secrets

2. **Build Failures:**
   - Check Node.js version compatibility
   - Verify all dependencies are in package.json
   - Review build logs for specific errors

3. **S3 Upload Issues:**
   - Verify bucket name is correct
   - Check bucket permissions
   - Ensure bucket exists in the correct region

4. **CloudFront Issues:**
   - Verify distribution ID is correct
   - Check distribution status (must be deployed)
   - Wait for invalidation to complete (5-15 minutes)

### Debug Commands:

```bash
# Test AWS credentials locally
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket-name

# Test CloudFront access
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID
```

## 🔐 Security Best Practices

1. **Use least privilege IAM policies**
2. **Rotate AWS access keys regularly**
3. **Use GitHub environments for additional protection**
4. **Enable branch protection rules**
5. **Review deployment logs regularly**

## 📈 Advanced Configuration

### Environment-Specific Builds

You can customize builds for different environments by modifying the environment files:

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com
VITE_ENVIRONMENT=production
VITE_DEBUG=false

# .env.staging
VITE_API_URL=https://staging-api.yourdomain.com
VITE_ENVIRONMENT=staging
VITE_DEBUG=true
```

### Custom Domain Setup

If you want to use a custom domain:

1. Set up Route 53 hosted zone
2. Create SSL certificate in ACM
3. Configure CloudFront to use custom domain
4. Update CNAME records

## 📞 Support

If you encounter issues:

1. Check the GitHub Actions logs
2. Review AWS CloudWatch logs
3. Verify all secrets are correctly configured
4. Test AWS permissions locally

## 🎉 Next Steps

After successful setup:

1. **Set up monitoring** with AWS CloudWatch
2. **Configure alerts** for deployment failures
3. **Set up custom domain** (optional)
4. **Add automated testing** to the workflow
5. **Configure staging environment** for testing

---

**Happy Deploying! 🚀** 