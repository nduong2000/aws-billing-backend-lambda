from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import json
import os
import boto3
import asyncio
from datetime import date, datetime
from decimal import Decimal
from config import db

# Custom JSON encoder to handle dates and decimals
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

router = APIRouter()
logger = logging.getLogger("audit_routes")

# Supported models configuration
SUPPORTED_MODELS = {
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {
        "name": "Claude Sonnet 4",
        "provider": "anthropic",
        "type": "claude",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "us.anthropic.claude-3-7-sonnet-20250109-v1:0": {
        "name": "Claude 3.7 Sonnet",
        "provider": "anthropic",
        "type": "claude",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "name": "Claude 3 Haiku",
        "provider": "anthropic",
        "type": "claude", 
        "max_tokens": 3000,
        "temperature": 0.7
    },
    "us.meta.llama4-scout-17b-instruct-v1:0": {
        "name": "Llama 4 Scout 17B Instruct",
        "provider": "meta",
        "type": "llama",
        "max_tokens": 2048,
        "temperature": 0.7
    },
    "us.meta.llama4-maverick-17b-instruct-v1:0": {
        "name": "Llama 4 Maverick 17B Instruct",
        "provider": "meta",
        "type": "llama",
        "max_tokens": 2048,
        "temperature": 0.7
    }
}

# Default model - using Claude Sonnet 4 as requested
DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"

# Pydantic models for validation
class AuditRequest(BaseModel):
    claim_data: str
    model_id: Optional[str] = None

class AuditResponse(BaseModel):
    audit_result: str
    success: bool
    details: Optional[Dict[str, Any]] = None

# Initialize AWS Bedrock client
def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

# Check if model is available in Bedrock
async def check_model_availability(model_id: str) -> bool:
    """Check if a model is available for invocation in AWS Bedrock"""
    try:
        bedrock_runtime = get_bedrock_client()
        
        # Try a minimal test request to see if the model is available
        test_config = get_model_config(model_id)
        test_body = create_request_body("Test", test_config)
        
        # This will fail if the model isn't available, but we catch the specific error
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(test_body)
        )
        return True
    except Exception as e:
        error_str = str(e)
        if "ValidationException" in error_str and "inference profile" in error_str:
            logger.warning(f"Model {model_id} requires inference profile - not directly available")
            return False
        elif "AccessDeniedException" in error_str:
            logger.warning(f"Access denied for model {model_id} - may need to request access")
            return False
        elif "ResourceNotFoundException" in error_str:
            logger.warning(f"Model {model_id} not found in this region")
            return False
        else:
            logger.warning(f"Unknown error checking model {model_id}: {error_str}")
            return False

# Get model configuration with availability check
def get_model_config(model_id: str = None) -> Dict[str, Any]:
    """Get model configuration with fallback to default"""
    if not model_id:
        model_id = os.getenv("AUDIT_MODEL", DEFAULT_MODEL)
    
    if model_id not in SUPPORTED_MODELS:
        logger.warning(f"Unsupported model {model_id}, falling back to default: {DEFAULT_MODEL}")
        model_id = DEFAULT_MODEL
    
    config = SUPPORTED_MODELS[model_id].copy()
    config["model_id"] = model_id
    return config

# Create model-specific request body
def create_request_body(prompt: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create request body based on model type"""
    model_type = model_config["type"]
    
    if model_type == "claude":
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    elif model_type == "llama":
        return {
            "prompt": prompt,
            "max_gen_len": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "top_p": 0.9
        }
    elif model_type == "mistral":
        return {
            "prompt": prompt,
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "top_p": 0.9,
            "top_k": 50
        }
    else:
        # Fallback to Claude format
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

# Parse model-specific response
def parse_model_response(response_body: Dict[str, Any], model_config: Dict[str, Any]) -> str:
    """Parse response based on model type"""
    model_type = model_config["type"]
    
    try:
        if model_type == "claude":
            return response_body.get("content", [{"text": ""}])[0].get("text", "")
        elif model_type == "llama":
            return response_body.get("generation", "")
        elif model_type == "mistral":
            outputs = response_body.get("outputs", [])
            if outputs:
                return outputs[0].get("text", "")
            return ""
        else:
            # Fallback to Claude format
            return response_body.get("content", [{"text": ""}])[0].get("text", "")
    except Exception as e:
        logger.error(f"Error parsing response for model type {model_type}: {e}")
        return ""

# Format claim data for LLM prompt (ported from auditController.js)
def format_claim_data_for_llm(claim) -> str:
    """
    Format claim data in a human-readable format for LLM processing.
    This replicates the formatClaimDataForLLM function from the original Node.js implementation.
    """
    try:
        # Handle both string and dictionary inputs
        if isinstance(claim, str):
            try:
                # Try to parse as JSON first
                claim_dict = json.loads(claim)
            except json.JSONDecodeError:
                # If not JSON, return the string as raw data
                return f"Raw claim data:\n{claim}"
        else:
            claim_dict = claim
            
        # Basic claim information
        formatted_data = f"Claim ID: {claim_dict.get('claim_id')}\n"
        
        # Format dates properly
        claim_date = claim_dict.get('claim_date')
        if isinstance(claim_date, str):
            try:
                # Parse ISO format string to date object if needed
                claim_date = datetime.fromisoformat(claim_date.replace('Z', '+00:00'))
            except ValueError:
                # Keep as is if parsing fails
                pass
                
        formatted_data += f"Claim Date: {claim_date}\n" if claim_date else "Claim Date: N/A\n"
        formatted_data += f"Claim Status: {claim_dict.get('status')}\n"
        
        # Format currency values
        try:
            total_charge = float(claim_dict.get('total_charge', 0))
            formatted_data += f"Total Charge: ${total_charge:.2f}\n"
        except (ValueError, TypeError):
            formatted_data += f"Total Charge: ${claim_dict.get('total_charge', 'N/A')}\n"
            
        try:
            insurance_paid = float(claim_dict.get('insurance_paid', 0))
            formatted_data += f"Insurance Paid: ${insurance_paid:.2f}\n"
        except (ValueError, TypeError):
            formatted_data += f"Insurance Paid: ${claim_dict.get('insurance_paid', 'N/A')}\n"
            
        try:
            patient_paid = float(claim_dict.get('patient_paid', 0))
            formatted_data += f"Patient Paid: ${patient_paid:.2f}\n\n"
        except (ValueError, TypeError):
            formatted_data += f"Patient Paid: ${claim_dict.get('patient_paid', 'N/A')}\n\n"
            
        # Patient information
        patient_name = claim_dict.get('patient_name', 'N/A')
        patient_id = claim_dict.get('patient_id', 'N/A')
        formatted_data += f"Patient: {patient_name} (ID: {patient_id})\n"
        
        # Provider information
        provider_name = claim_dict.get('provider_name', 'N/A')
        provider_id = claim_dict.get('provider_id', 'N/A')
        formatted_data += f"Provider: {provider_name} (ID: {provider_id})\n\n"
        
        # Services/Items information
        formatted_data += "Services Billed:\n"
        items = claim_dict.get('items', [])
        for item in items:
            cpt_code = item.get('cpt_code', 'N/A')
            description = item.get('description', 'N/A')
            
            try:
                charge_amount = float(item.get('charge_amount', 0))
                formatted_data += f"- CPT Code: {cpt_code}, Description: {description}, Charge: ${charge_amount:.2f}\n"
            except (ValueError, TypeError):
                formatted_data += f"- CPT Code: {cpt_code}, Description: {description}, Charge: ${item.get('charge_amount', 'N/A')}\n"
                
        return formatted_data
    except Exception as e:
        logger.error(f"Error formatting claim data: {e}")
        # Fallback to string representation
        if isinstance(claim, dict):
            return f"Error formatting claim data: {str(e)}\nRaw claim data: {json.dumps(claim, cls=CustomJSONEncoder)}"
        else:
            return f"Error formatting claim data: {str(e)}\nRaw claim data: {str(claim)}"

# Main audit function for claims
async def process_audit(claim_data: str, model_id: str = None) -> Dict[str, Any]:
    """
    Process a medical billing claim audit using AWS Bedrock
    """
    try:
        # Get model configuration
        model_config = get_model_config(model_id)
        actual_model_id = model_config["model_id"]
        
        # Debug logging for model selection
        logger.info(f"🔍 AUDIT DEBUG: Processing audit request")
        logger.info(f"📋 AUDIT DEBUG: Requested model: {model_id or 'None (using default)'}")
        logger.info(f"🤖 AUDIT DEBUG: Selected model: {actual_model_id} ({model_config['name']})")
        logger.info(f"🏭 AUDIT DEBUG: Model provider: {model_config['provider']}")
        logger.info(f"⚙️ AUDIT DEBUG: Model type: {model_config['type']}")
        logger.info(f"🎯 AUDIT DEBUG: Default model available: {DEFAULT_MODEL}")
        logger.info(f"📊 AUDIT DEBUG: Total supported models: {len(SUPPORTED_MODELS)}")
        
        # Log model selection logic
        if model_id:
            if model_id in SUPPORTED_MODELS:
                logger.info(f"✅ AUDIT DEBUG: Requested model '{model_id}' is supported")
            else:
                logger.warning(f"⚠️ AUDIT DEBUG: Requested model '{model_id}' not supported, using default")
        else:
            logger.info(f"🔧 AUDIT DEBUG: No model specified, using default: {DEFAULT_MODEL}")
        
        # Log environment variable override if present
        env_model = os.getenv("AUDIT_MODEL")
        if env_model and env_model != DEFAULT_MODEL:
            logger.info(f"🌍 AUDIT DEBUG: Environment override detected: AUDIT_MODEL={env_model}")
            if env_model == actual_model_id:
                logger.info(f"✅ AUDIT DEBUG: Using environment model: {env_model}")
            else:
                logger.warning(f"⚠️ AUDIT DEBUG: Environment model '{env_model}' not supported, using: {actual_model_id}")
        
        # Log final model choice with emphasis
        logger.info(f"🚀 AUDIT DEBUG: FINAL MODEL CHOICE: {actual_model_id} ({model_config['name']}) from {model_config['provider']}")
        logger.info(f"⚙️ AUDIT DEBUG: Model configuration - Max tokens: {model_config['max_tokens']}, Temperature: {model_config['temperature']}")
        
        # Get the Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Format the claim data for the LLM
        formatted_claim_data = format_claim_data_for_llm(claim_data)
        
        # Create the audit prompt
        audit_prompt = f"""
You are a medical billing audit specialist. Please analyze the following medical billing claim for accuracy, compliance, and potential fraud indicators.

Provide a comprehensive audit report covering these areas:

1. **Coding Accuracy**: Review CPT codes, ICD-10 codes, and modifiers for correctness
2. **Documentation Completeness**: Assess if services are properly documented
3. **Medical Necessity**: Evaluate if services were medically necessary
4. **Regulatory Compliance**: Check for compliance with billing regulations
5. **Fraud Risk Indicators**: Identify any red flags or suspicious patterns
6. **Recommendations**: Provide specific recommendations for improvement

**Claim Data:**
{formatted_claim_data}

Please provide a detailed analysis with specific findings and recommendations.
"""

        # Log the audit request details
        logger.info(f"📤 AUDIT DEBUG: Sending request to AWS Bedrock")
        logger.info(f"📏 AUDIT DEBUG: Prompt length: {len(audit_prompt)} characters")
        logger.info(f"🎛️ AUDIT DEBUG: Max tokens: {model_config['max_tokens']}")
        logger.info(f"🌡️ AUDIT DEBUG: Temperature: {model_config['temperature']}")
        
        # Create model-specific request body
        request_body = create_request_body(audit_prompt, model_config)
        
        # Invoke the model
        try:
            response = bedrock_runtime.invoke_model(
                modelId=actual_model_id,
                body=json.dumps(request_body)
            )
        except Exception as invoke_error:
            error_str = str(invoke_error)
            
            # Handle specific model invocation errors
            if "ValidationException" in error_str and "inference profile" in error_str:
                logger.error(f"❌ AUDIT DEBUG: Model {actual_model_id} requires inference profile")
                logger.info(f"🔄 AUDIT DEBUG: Trying fallback to Claude 3 Haiku")
                
                # Try fallback to Claude 3 Haiku
                fallback_config = get_model_config("anthropic.claude-3-haiku-20240307-v1:0")
                fallback_body = create_request_body(audit_prompt, fallback_config)
                
                try:
                    response = bedrock_runtime.invoke_model(
                        modelId=fallback_config["model_id"],
                        body=json.dumps(fallback_body)
                    )
                    model_config = fallback_config
                    actual_model_id = fallback_config["model_id"]
                    logger.info(f"✅ AUDIT DEBUG: Successfully using fallback model: {model_config['name']}")
                except Exception as fallback_error:
                    logger.error(f"❌ AUDIT DEBUG: Fallback model also failed: {str(fallback_error)}")
                    raise invoke_error
            elif "AccessDeniedException" in error_str:
                logger.error(f"❌ AUDIT DEBUG: Access denied for model {actual_model_id}")
                raise invoke_error
            else:
                logger.error(f"❌ AUDIT DEBUG: Unknown model invocation error: {error_str}")
                raise invoke_error
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        audit_response = parse_model_response(response_body, model_config)
        
        # Debug logging for response
        logger.info(f"📥 AUDIT DEBUG: Received response from {model_config['name']}")
        logger.info(f"📏 AUDIT DEBUG: Response length: {len(audit_response)} characters")
        
        # Check if we got an empty response
        if not audit_response or audit_response.strip() == "":
            logger.error(f"❌ AUDIT DEBUG: Empty response received from {model_config['name']}")
            audit_response = (
                f"The audit system using {model_config['name']} could not generate an analysis at this time. "
                "Please try again later or contact system administration."
            )
            
        # Calculate a fraud score based on audit findings
        fraud_score = await calculate_fraud_score(formatted_claim_data, audit_response)
        
        # Create the final response object
        response_object = {
            "audit_result": audit_response,
            "success": True,
            "details": {
                "fraud_score": fraud_score,
                "model_used": actual_model_id,
                "model_name": model_config["name"],
                "model_provider": model_config["provider"],
                "prompt_length": len(audit_prompt),
                "response_length": len(audit_response),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"✅ AUDIT DEBUG: Audit completed successfully using {model_config['name']}")
        logger.info(f"📊 AUDIT DEBUG: Fraud score: {fraud_score}")
        
        return response_object
        
    except Exception as e:
        logger.error(f"❌ AUDIT DEBUG: Error in process_audit: {str(e)}")
        logger.error(f"🔧 AUDIT DEBUG: Falling back to mock audit system")
        
        # Fallback to mock audit if Bedrock fails
        try:
            mock_response = await generate_mock_audit_response(claim_data, model_id)
            mock_response["details"]["model_used"] = f"MOCK_FALLBACK (requested: {model_id or 'default'})"
            mock_response["details"]["error"] = str(e)
            return mock_response
        except Exception as mock_error:
            logger.error(f"❌ AUDIT DEBUG: Mock audit also failed: {str(mock_error)}")
            return {
                "audit_result": f"Audit system temporarily unavailable. Error: {str(e)}",
                "success": False,
                "details": {
                    "error": str(e),
                    "model_requested": model_id or "default",
                    "timestamp": datetime.now().isoformat()
                }
            }

# API endpoint to list available models
@router.get("/models", response_model=Dict[str, Any])
@router.get("/models/", response_model=Dict[str, Any])  # Handle with trailing slash
async def list_available_models():
    """List all available models for audit processing"""
    try:
        models_info = []
        for model_id, config in SUPPORTED_MODELS.items():
            models_info.append({
                "model_id": model_id,
                "name": config["name"],
                "provider": config["provider"],
                "type": config["type"],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "is_default": model_id == DEFAULT_MODEL
            })
        
        return {
            "models": models_info,
            "default_model": DEFAULT_MODEL,
            "total_models": len(SUPPORTED_MODELS)
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Generate mock audit response when Bedrock is not available
async def generate_mock_audit_response(claim_data: str, requested_model: str = None) -> Dict[str, Any]:
    """
    Generate a mock audit response when AWS Bedrock is not available
    """
    try:
        # Format the claim data
        formatted_claim_data = format_claim_data_for_llm(claim_data)
        
        # Calculate a basic fraud score
        fraud_score = await calculate_fraud_score(formatted_claim_data, "mock audit analysis")
        
        # Get model info for the requested model
        model_config = get_model_config(requested_model)
        
        # Debug logging for mock audit
        logger.info(f"🔧 MOCK AUDIT DEBUG: Generating mock response")
        logger.info(f"📋 MOCK AUDIT DEBUG: Requested model: {requested_model or 'None (using default)'}")
        logger.info(f"🤖 MOCK AUDIT DEBUG: Would use model: {model_config['model_id']} ({model_config['name']})")
        logger.info(f"🏭 MOCK AUDIT DEBUG: Model provider: {model_config['provider']}")
        logger.info(f"🎯 MOCK AUDIT DEBUG: Default model: {DEFAULT_MODEL}")
        logger.info(f"📊 MOCK AUDIT DEBUG: Generated fraud score: {fraud_score}")

        mock_audit = f"""
**MEDICAL BILLING AUDIT REPORT**
*Generated by Mock Audit System*

**MODEL INFORMATION**
• Requested Model: {requested_model or 'Default'}
• Would Use: {model_config['name']} ({model_config['model_id']})
• Provider: {model_config['provider']}
• Default Available: Claude Sonnet 4 ({DEFAULT_MODEL})
• Note: This is a mock response - enable AWS Bedrock for full AI analysis

**1. CODING ACCURACY**
✅ CPT codes appear to follow standard formatting
✅ Basic code structure validation passed
ℹ️  Detailed code accuracy requires AI model analysis

**2. DOCUMENTATION COMPLETENESS**
✅ Required fields are present in the claim
✅ Basic data validation passed
ℹ️  Comprehensive documentation review requires AI analysis

**3. MEDICAL NECESSITY**
✅ Services appear appropriate for documented conditions
✅ No obvious unnecessary or duplicate services identified
ℹ️  Full medical necessity review requires clinical documentation analysis

**4. REGULATORY COMPLIANCE**
✅ Claim format follows standard billing requirements
✅ Required fields are populated
ℹ️  Compliance with latest CMS guidelines should be verified

**5. FRAUD RISK INDICATORS**
Risk Score: {fraud_score}/100
{'🟢 LOW RISK' if fraud_score < 30 else '🟡 MODERATE RISK' if fraud_score < 70 else '🔴 HIGH RISK'}

{'No significant fraud indicators detected.' if fraud_score < 30 else 'Some patterns warrant additional review.' if fraud_score < 70 else 'Multiple risk factors identified - requires immediate review.'}

**6. RECOMMENDATIONS**
• Enable AWS Bedrock model access for comprehensive AI-powered audit analysis
• Verify all codes against current year coding guidelines
• Ensure supporting documentation is available for audit
• Consider implementing automated pre-submission validation
• Regular compliance training for billing staff

**SUMMARY**
This preliminary audit shows the claim follows basic formatting and completeness requirements. For comprehensive fraud detection and detailed compliance analysis, please enable AWS Bedrock model access to unlock full AI-powered audit capabilities.

*To enable full audit functionality:*
1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access to the following models:
   - {model_config['model_id']} (Target Model)
   - {DEFAULT_MODEL} (Default: Claude Sonnet 4)
   - anthropic.claude-3-haiku-20240307-v1:0 (Fallback)
4. Approval is typically instant for most models
"""

        logger.info(f"✅ MOCK AUDIT DEBUG: Mock audit completed successfully")

        return {
            "audit_result": mock_audit,
            "success": True,
            "details": {
                "fraud_score": fraud_score,
                "model_used": f"MOCK_SYSTEM (would_use: {model_config['model_id']})",
                "model_name": f"Mock System (Target: {model_config['name']})",
                "model_provider": f"mock (target: {model_config['provider']})",
                "requested_model": requested_model or "default",
                "target_model": model_config['model_id'],
                "prompt_length": len(formatted_claim_data),
                "response_length": len(mock_audit),
                "note": "Mock response - enable AWS Bedrock for full AI analysis",
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"❌ MOCK AUDIT DEBUG: Error generating mock audit response: {e}")
        return {
            "audit_result": "Mock audit system temporarily unavailable. Please enable AWS Bedrock model access for full functionality.",
            "success": False,
            "details": {
                "error": str(e),
                "requested_model": requested_model or "default",
                "timestamp": datetime.now().isoformat()
            }
        }

# Calculate fraud score using basic NLP analysis
async def calculate_fraud_score(claim_data: str, audit_result: str) -> float:
    """
    Examine the claim and audit results to produce a fraud risk score
    """
    try:
        # Import scikit-learn components
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # High-risk phrases to look for
        risk_indicators = [
            "upcoding", "unbundling", "mismatch", "unusual", "excessive", 
            "unnecessary", "duplicate", "no documentation", "inconsistent", 
            "fraud", "suspicious", "overutilization", "discrepancy"
        ]
        
        # Convert to lowercase to standardize text
        claim_lower = claim_data.lower()
        audit_lower = audit_result.lower()
        combined_text = claim_lower + " " + audit_lower
        
        # Count occurrences of each risk indicator
        risk_counts = sum(1 for indicator in risk_indicators if indicator in combined_text)
        
        # Calculate a base score from 0-1 based on risk indicator density
        max_possible_indicators = len(risk_indicators)
        base_score = min(risk_counts / max_possible_indicators, 1.0) * 0.5
        
        # Use TF-IDF to find similarity to known high-risk patterns
        vectorizer = TfidfVectorizer()
        
        # Some examples of high-risk patterns
        high_risk_examples = [
            "multiple high-cost procedures on same day without documentation",
            "billing for services not documented in medical records",
            "unusual patterns of billing across multiple patients"
        ]
        
        # Combine with the current text
        all_texts = high_risk_examples + [combined_text]
        
        # Vectorize all texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate similarity between the current text and high-risk examples
        similarities = cosine_similarity(
            tfidf_matrix[-1:], tfidf_matrix[:-1]
        )[0]
        
        # Average similarity score
        avg_similarity = np.mean(similarities) * 0.5
        
        # Combine the scores
        final_score = base_score + avg_similarity
        
        # Ensure the score is between 0 and 1
        final_score = min(max(final_score, 0.0), 1.0)
        
        # Return as a value between 0-100
        return round(final_score * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating fraud score: {e}")
        return 0.0

# API endpoint for claim auditing
@router.post("/claims/{claim_id}", response_model=Dict[str, Any])
async def audit_claim(claim_id: int, model_id: Optional[str] = Query(None, description="Model ID to use for audit")):
    try:
        # Debug logging for claim audit request
        logger.info(f"🔍 CLAIM AUDIT DEBUG: Starting audit for claim {claim_id}")
        logger.info(f"📋 CLAIM AUDIT DEBUG: Requested model: {model_id or 'None (using default)'}")
        
        # Get claim data
        query = '''
        SELECT c.*, p.first_name || ' ' || p.last_name as patient_name,
               pr.provider_name
        FROM claims c
        JOIN patients p ON c.patient_id = p.patient_id
        JOIN providers pr ON c.provider_id = pr.provider_id
        WHERE c.claim_id = %s
        '''
        claim_result = db.query(query, [claim_id])
        
        if not claim_result:
            logger.warning(f"❌ CLAIM AUDIT DEBUG: Claim {claim_id} not found")
            raise HTTPException(status_code=404, detail="Claim not found")
            
        claim = claim_result[0]
        
        # Get claim items
        items_query = '''
        SELECT ci.*, s.cpt_code, s.description
        FROM claim_items ci
        JOIN services s ON ci.service_id = s.service_id
        WHERE ci.claim_id = %s
        '''
        claim_items = db.query(items_query, [claim_id])
        
        # Add items to the claim
        claim["items"] = claim_items
        
        logger.info(f"📊 CLAIM AUDIT DEBUG: Found claim with {len(claim_items)} items")
        
        # Process the audit directly with the claim object and model selection
        audit_result = await process_audit(claim, model_id)
        
        # Log the complete audit result before returning
        logger.info(f"✅ CLAIM AUDIT DEBUG: Audit completed for claim {claim_id}")
        logger.info(f"📏 CLAIM AUDIT DEBUG: Result length: {len(audit_result.get('audit_result', ''))}")
        
        # If successful, update the fraud score in the database
        if audit_result["success"] and "fraud_score" in audit_result.get("details", {}):
            fraud_score = audit_result["details"]["fraud_score"]
            
            # Update the claim with the fraud score
            db.query(
                "UPDATE claims SET fraud_score = %s WHERE claim_id = %s",
                [fraud_score, claim_id]
            )
            
            logger.info(f"📊 CLAIM AUDIT DEBUG: Updated fraud score in database: {fraud_score}")
        
        # Format the response to match what the frontend expects (with 'analysis' field)
        frontend_response = {
            "claim_id": claim_id,
            "analysis": audit_result["audit_result"],
            "success": audit_result["success"],
            "details": audit_result.get("details", {})
        }
        
        logger.info(f"🚀 CLAIM AUDIT DEBUG: Returning response for claim {claim_id}")
        
        return frontend_response
    except Exception as e:
        logger.error(f"❌ CLAIM AUDIT DEBUG: Error auditing claim {claim_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for direct audit of claim data
@router.post("/process", response_model=AuditResponse)
@router.post("/process/", response_model=AuditResponse)  # Handle with trailing slash
async def process_audit_request(audit_request: AuditRequest):
    try:
        # Log that we're processing an audit request
        logger.info(f"Processing audit request with data length: {len(audit_request.claim_data)}")
        
        # Process the audit directly from provided data
        audit_result = await process_audit(audit_request.claim_data, audit_request.model_id)
        
        # Log the result before returning
        logger.info(f"Audit request processed, result length: {len(audit_result.get('audit_result', ''))}")
        
        return audit_result
    except Exception as e:
        logger.error(f"Error processing audit request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
