import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bedrock():
    # Initialize client
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    
    # Define the prompt
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": "Write a short poem about medical billing"}
        ]
    }
    
    try:
        # Make request to the model
        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response["body"].read().decode("utf-8"))
        
        # Print response
        print("Response from Claude 3 Haiku:")
        print(response_body["content"][0]["text"])
        return True
    except Exception as e:
        print(f"Error testing Bedrock connection: {e}")
        return False

if __name__ == "__main__":
    test_bedrock()
