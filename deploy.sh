#!/bin/bash
# Deployment Script for HarshScalable
# Deploys backend Lambda and frontend to AWS

set -e

echo "=========================================="
echo "HarshScalable Deployment Script"
echo "=========================================="

# Check for required tools
command -v aws >/dev/null 2>&1 || { echo "AWS CLI required. Install: pip install awscli"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm required for frontend build"; exit 1; }

# Configuration
LAMBDA_FUNCTION_NAME="inventory-backend"
S3_FRONTEND_BUCKET="inventory-app-prod-1774347597"
CLOUDFRONT_DISTRIBUTION="EMOM4155W74KN"
REGION="eu-west-1"

echo ""
echo "Step 1: Package Backend Lambda"
echo "------------------------------"

# Create deployment package
cd "$(dirname "$0")"
mkdir -p dist

# Copy Lambda handler
cp backend-lambda.py dist/lambda_function.py

# Copy backend modules
cp -r backend/*.py dist/ 2>/dev/null || true

# Install dependencies to package
pip install requests -t dist/ --quiet

# Create zip
cd dist
zip -r ../lambda-deployment.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

echo "✅ Lambda package created: lambda-deployment.zip"

echo ""
echo "Step 2: Deploy Backend to AWS Lambda"
echo "------------------------------------"

# Update Lambda function
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file fileb://lambda-deployment.zip \
    --region "$REGION" \
    --no-cli-pager || {
    echo "⚠️  Lambda update failed. You may need to:"
    echo "   1. Create the Lambda function first"
    echo "   2. Configure AWS credentials: aws configure"
    echo "   3. Check function name: $LAMBDA_FUNCTION_NAME"
}

echo ""
echo "Step 3: Build Frontend"
echo "----------------------"

cd frontend
npm install --silent
npm run build

echo "✅ Frontend built successfully"

echo ""
echo "Step 4: Deploy Frontend to S3"
echo "-----------------------------"

# Upload to S3
aws s3 sync dist/ "s3://$S3_FRONTEND_BUCKET/" \
    --delete \
    --region "$REGION" \
    --no-cli-pager || {
    echo "⚠️  S3 upload failed. Check bucket name and permissions."
}

echo ""
echo "Step 5: Invalidate CloudFront Cache"
echo "-----------------------------------"

aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION" \
    --paths "/*" \
    --region "$REGION" \
    --no-cli-pager || {
    echo "⚠️  CloudFront invalidation failed."
}

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Frontend URL: https://d27v9w88lyu3ua.cloudfront.net"
echo "Backend API:  http://54.194.174.117:8001/api/v1"
echo ""
echo "New Features Deployed:"
echo "  ✅ External APIs (Weather, Currency, Countries)"
echo "  ✅ Parallel Processing (Batch operations)"
echo "  ✅ SQS Event Publishing"
echo ""

# Cleanup
rm -rf dist lambda-deployment.zip
