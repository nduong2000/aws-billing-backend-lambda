from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
import boto3
import json
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("ollama_routes")

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Import model configuration from audit_routes
from .audit_routes import SUPPORTED_MODELS, DEFAULT_MODEL, get_model_config, create_request_body, parse_model_response

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
    Generate text using AWS Bedrock with model selection support
    """
    try:
        prompt = request_data.get("prompt")
        requested_model = request_data.get("model")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Get model configuration
        model_config = get_model_config(requested_model)
        actual_model_id = model_config["model_id"]
        
        # Debug logging
        logger.info(f"🔍 OLLAMA DEBUG: Generate text request")
        logger.info(f"📋 OLLAMA DEBUG: Requested model: {requested_model or 'None (using default)'}")
        logger.info(f"🤖 OLLAMA DEBUG: Selected model: {actual_model_id} ({model_config['name']})")
        logger.info(f"📏 OLLAMA DEBUG: Prompt length: {len(prompt)} characters")
        
        # Get AWS Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Create model-specific request body
        request_body = create_request_body(prompt, model_config)
        
        logger.info(f"📤 OLLAMA DEBUG: Sending request to AWS Bedrock")
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=actual_model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        model_response = parse_model_response(response_body, model_config)
        
        logger.info(f"📥 OLLAMA DEBUG: Received response from {model_config['name']}")
        logger.info(f"📏 OLLAMA DEBUG: Response length: {len(model_response)} characters")
        
        # Format response to match expected structure
        formatted_response = {
            "model": actual_model_id,
            "model_name": model_config["name"],
            "model_provider": model_config["provider"],
            "response": model_response,
            "done": True,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ OLLAMA DEBUG: Text generation completed successfully")
        
        return formatted_response
    except Exception as e:
        logger.error(f"❌ OLLAMA DEBUG: Error in generate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit", response_model=Dict[str, Any])
@router.post("/audit/", response_model=Dict[str, Any])  # Handle with trailing slash
async def audit_claim_ollama(audit_request: AuditRequest):
    """
    Audit a claim using AWS Bedrock with model selection support
    """
    try:
        claim_data = audit_request.claim_data
        requested_model = audit_request.model
        
        if not claim_data:
            raise HTTPException(status_code=400, detail="Claim data is required")
        
        # Get model configuration
        model_config = get_model_config(requested_model)
        actual_model_id = model_config["model_id"]
        
        # Debug logging
        logger.info(f"🔍 OLLAMA AUDIT DEBUG: Processing audit request")
        logger.info(f"📋 OLLAMA AUDIT DEBUG: Requested model: {requested_model or 'None (using default)'}")
        logger.info(f"🤖 OLLAMA AUDIT DEBUG: Selected model: {actual_model_id} ({model_config['name']})")
        logger.info(f"📏 OLLAMA AUDIT DEBUG: Claim data length: {len(claim_data)} characters")
        
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
        
        logger.info(f"📤 OLLAMA AUDIT DEBUG: Sending audit request to AWS Bedrock")
        logger.info(f"📏 OLLAMA AUDIT DEBUG: Prompt length: {len(prompt)} characters")
        
        # Get AWS Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Create model-specific request body
        request_body = create_request_body(prompt, model_config)
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=actual_model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        model_response = parse_model_response(response_body, model_config)
        
        logger.info(f"📥 OLLAMA AUDIT DEBUG: Received response from {model_config['name']}")
        logger.info(f"📏 OLLAMA AUDIT DEBUG: Response length: {len(model_response)} characters")
        
        logger.info(f"✅ OLLAMA AUDIT DEBUG: Audit completed successfully using {model_config['name']}")
        
        return {
            "audit_result": model_response,
            "success": True,
            "model_used": actual_model_id,
            "model_name": model_config["name"],
            "model_provider": model_config["provider"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ OLLAMA AUDIT DEBUG: Error in audit_claim: {str(e)}")
        return {
            "audit_result": f"An error occurred while processing the audit using {requested_model or 'default model'}: {str(e)}",
            "success": False,
            "error": str(e),
            "model_requested": requested_model or "default",
            "timestamp": datetime.now().isoformat()
        }
