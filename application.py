import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("app")

# Create the FastAPI application
application = FastAPI(title="Medical Billing API")
app = application  # Alias for compatibility

# Configure CORS
allowed_origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "https://duong.casa",
    "https://billing-system.duong.casa",
    "https://billing.duong.casa"
]

application.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

logger.info("Middleware configured.")

# Base route
@application.get("/")
async def root():
    return {"message": "Medical Billing API Running!"}

# Include routers
from routes.patient_routes import router as patient_router
from routes.provider_routes import router as provider_router
from routes.service_routes import router as service_router
from routes.appointment_routes import router as appointment_router
from routes.claim_routes import router as claim_router
from routes.payment_routes import router as payment_router
from routes.ollama_routes import router as ollama_router
from routes.audit_routes import router as audit_router

# Mount routers
application.include_router(patient_router, prefix="/api/patients", tags=["patients"])
application.include_router(provider_router, prefix="/api/providers", tags=["providers"])
application.include_router(service_router, prefix="/api/services", tags=["services"])
application.include_router(appointment_router, prefix="/api/appointments", tags=["appointments"])
application.include_router(claim_router, prefix="/api/claims", tags=["claims"])
application.include_router(payment_router, prefix="/api/payments", tags=["payments"])
application.include_router(ollama_router, prefix="/api/ollama-test", tags=["ollama"])
application.include_router(audit_router, prefix="/api/audit", tags=["audit"])

logger.info("Routes configured.")

# Debug endpoint (only in development)
@application.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    if os.getenv("NODE_ENV") != "production":
        routes = []
        for route in application.routes:
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, "methods") else []
            })
        return sorted(routes, key=lambda x: x["path"])
    else:
        raise HTTPException(status_code=404, detail="Not found")

@application.post("/debug/echo", include_in_schema=False)
async def debug_echo(request: Request):
    if os.getenv("NODE_ENV") != "production":
        json_body = await request.json()
        return {
            "message": "Echo endpoint working",
            "received": {
                "body": json_body,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers)
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Not found")

logger.info("Debug routes added for development.")

# Test AWS Bedrock connectivity
@application.get("/debug/bedrock-test", include_in_schema=False)
async def test_bedrock_connection():
    if os.getenv("NODE_ENV") != "production":
        try:
            import boto3
            import json
            
            # Get AWS Region from environment
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
            
            # Initialize Bedrock client
            bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_region
            )
            
            # Simple test prompt
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.7,
                "messages": [
                    {"role": "user", "content": "Hello, this is a test."}
                ]
            }
            
            # Invoke the model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            return {
                "status": "Bedrock connection successful",
                "model": model_id,
                "response": response_body
            }
        except Exception as e:
            logger.error(f"Error testing Bedrock connection: {e}")
            return {
                "status": "Bedrock connection failed",
                "error": str(e)
            }
    else:
        raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5001"))
    uvicorn.run("application:app", host="0.0.0.0", port=port, reload=True)
