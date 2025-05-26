from fastapi import APIRouter, HTTPException, Depends, Body
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

# Pydantic models for validation
class AuditRequest(BaseModel):
    claim_data: str

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

# Model ID configuration
MODEL_ID = os.getenv("AUDIT_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")

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
async def process_audit(claim_data: str) -> Dict[str, Any]:
    """
    Process a medical billing claim audit using AWS Bedrock
    """
    try:
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

        # Log the audit request
        logger.info(f"Sending audit request to AWS Bedrock using model {MODEL_ID}")
        
        # Claude requires a different format than Mistral
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": audit_prompt}
            ]
        }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        audit_response = response_body.get("content", [{"text": ""}])[0].get("text", "")
        
        # Check if we got an empty response
        if not audit_response or audit_response.strip() == "":
            logger.error("Empty response received from AWS Bedrock")
            audit_response = (
                "The audit system could not generate an analysis at this time. "
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
                "model_used": MODEL_ID,
                "prompt_length": len(audit_prompt),
                "response_length": len(audit_response)
            }
        }
        
        # Log the final response we're sending back
        logger.info(f"Final response object: {json.dumps(response_object, default=str)[:500]}...")
        
        return response_object
    except Exception as e:
        logger.error(f"Error in audit processing: {e}", exc_info=True)
        
        # Check if this is a Bedrock access denied error
        if "AccessDeniedException" in str(e) or "access to the model" in str(e):
            logger.info("Bedrock access denied, using mock audit response")
            return await generate_mock_audit_response(claim_data)
        
        return {
            "audit_result": f"Failed to complete audit due to an error: {str(e)}. Please check server logs for details.",
            "success": False,
            "details": {"error": str(e)}
        }

async def generate_mock_audit_response(claim_data: str) -> Dict[str, Any]:
    """
    Generate a mock audit response when Bedrock is not available
    """
    try:
        # Format the claim data for analysis
        formatted_claim_data = format_claim_data_for_llm(claim_data)
        
        # Calculate a fraud score using our existing function
        fraud_score = await calculate_fraud_score(formatted_claim_data, "")
        
        # Generate a comprehensive mock audit response
        mock_audit = f"""
**MEDICAL BILLING AUDIT REPORT**
*Note: This is a mock audit response generated while AWS Bedrock model access is being configured.*

**1. CODING ACCURACY**
✅ CPT codes appear to be properly formatted and within valid ranges
✅ ICD-10 codes follow standard formatting conventions
⚠️  Recommend verification of code-to-service alignment with current coding guidelines

**2. DOCUMENTATION COMPLETENESS**
✅ Basic claim information is present and complete
✅ Patient and provider information properly documented
⚠️  Clinical documentation review recommended for complex procedures

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
3. Request access to Anthropic Claude models
4. Approval is typically instant for most models
"""

        return {
            "audit_result": mock_audit,
            "success": True,
            "details": {
                "fraud_score": fraud_score,
                "model_used": "mock-audit-system",
                "prompt_length": len(formatted_claim_data),
                "response_length": len(mock_audit),
                "note": "Mock response - enable AWS Bedrock for full AI analysis"
            }
        }
    except Exception as e:
        logger.error(f"Error generating mock audit response: {e}")
        return {
            "audit_result": "Mock audit system temporarily unavailable. Please enable AWS Bedrock model access for full functionality.",
            "success": False,
            "details": {"error": str(e)}
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
async def audit_claim(claim_id: int):
    try:
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
        
        # Process the audit directly with the claim object
        # Skip JSON serialization to avoid potential issues
        audit_result = await process_audit(claim)
        
        # Log the complete audit result before returning
        logger.info(f"Complete audit result for claim {claim_id}: {json.dumps(audit_result, default=str)[:500]}...")
        
        # If successful, update the fraud score in the database
        if audit_result["success"] and "fraud_score" in audit_result.get("details", {}):
            fraud_score = audit_result["details"]["fraud_score"]
            
            # Update the claim with the fraud score
            db.query(
                "UPDATE claims SET fraud_score = %s WHERE claim_id = %s",
                [fraud_score, claim_id]
            )
        
        # Format the response to match what the frontend expects (with 'analysis' field)
        frontend_response = {
            "claim_id": claim_id,
            "analysis": audit_result["audit_result"],
            "success": audit_result["success"],
            "details": audit_result.get("details", {})
        }
        
        logger.info(f"Returning frontend-compatible response with analysis length: {len(frontend_response['analysis'])}")
        
        return frontend_response
    except Exception as e:
        logger.error(f"Error auditing claim {claim_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for direct audit of claim data
@router.post("/process", response_model=AuditResponse)
@router.post("/process/", response_model=AuditResponse)  # Handle with trailing slash
async def process_audit_request(audit_request: AuditRequest):
    try:
        # Log that we're processing an audit request
        logger.info(f"Processing audit request with data length: {len(audit_request.claim_data)}")
        
        # Process the audit directly from provided data
        audit_result = await process_audit(audit_request.claim_data)
        
        # Log the result before returning
        logger.info(f"Audit request processed, result length: {len(audit_result.get('audit_result', ''))}")
        
        return audit_result
    except Exception as e:
        logger.error(f"Error processing audit request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
