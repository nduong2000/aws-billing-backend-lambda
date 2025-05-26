import os
import sys
from mangum import Mangum
from application import app

# Set environment variables
os.environ['AWS_LAMBDA_FUNCTION_MEMORY_SIZE'] = '3008'  # Max memory for better performance

# Configure the handler for AWS Lambda
handler = Mangum(
    app,
    lifespan="off",  # Disable lifespan for Lambda
    api_gateway_base_path="/api"  # Set base path for API Gateway
)
