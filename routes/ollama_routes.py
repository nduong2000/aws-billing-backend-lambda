from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
import boto3
import json
import os
from dotenv import load_dotenv
import logging

router = APIRouter()
logger = logging.getLogger("ollama_routes")

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

# Pydantic model for audit requests
class AuditRequest(BaseModel):
    claim_data: str
    model: Optional[str] = None

# Initialize AWS Bedrock client
def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION
    )

@router.post("/generate", response_model=Dict[str, Any])
async def generate_text(request_data: Dict[str, Any] = Body(...)):
    """
    Generate text using AWS Bedrock
    """
    try:
        prompt = request_data.get("prompt")
        model = request_data.get("model", BEDROCK_MODEL_ID)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"Sending request to AWS Bedrock with model: {model}")
        
        # Get AWS Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Prepare payload for Claude model
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Format response to match expected structure
        formatted_response = {
            "model": model,
            "response": response_body.get("content", [{"text": "No response generated"}])[0].get("text", ""),
            "done": True
        }
        
        return formatted_response
    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit", response_model=Dict[str, Any])
@router.post("/audit/", response_model=Dict[str, Any])  # Handle with trailing slash
async def audit_claim_ollama(audit_request: AuditRequest):
    """
    Audit a claim using AWS Bedrock
    """
    try:
        claim_data = audit_request.claim_data
        model = audit_request.model or BEDROCK_MODEL_ID
        
        if not claim_data:
            raise HTTPException(status_code=400, detail="Claim data is required")
        
        # Format the claim data for the LLM
        prompt = f"""
        Please audit the following medical claim for accuracy and potential issues:
        
        {claim_data}
        
        Provide your analysis with the following structure:
        1. Overall assessment
        2. Coding accuracy
        3. Documentation issues
        4. Compliance concerns
        5. Recommendations
        """
        
        logger.info(f"Auditing claim with AWS Bedrock model: {model}")
        
        # Get AWS Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Prepare payload for Claude model
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        model_response = response_body.get("content", [{"text": "No audit generated"}])[0].get("text", "")
        
        return {
            "audit_result": model_response,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in audit_claim: {str(e)}")
        return {
            "audit_result": "An error occurred while processing the audit.",
            "success": False,
            "error": str(e)
        }
