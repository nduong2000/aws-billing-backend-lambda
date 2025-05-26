# lambda_function.py
import json
import os
import logging
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Request, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize database on startup
def init_database():
    """Initialize the database when Lambda starts"""
    try:
        from config.db_init import initialize_db
        from config.db import test_connection
        
        logger.info("Initializing database...")
        initialize_db()
        
        if test_connection():
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed")
            raise Exception("Database connection test failed")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

# Initialize database
init_database()

# Import route modules after database initialization
from routes import (
    patient_routes,
    provider_routes, 
    service_routes,
    appointment_routes,
    claim_routes,
    payment_routes,
    audit_routes,
    ollama_routes
)

# Create FastAPI app
app = FastAPI(
    title="Medical Billing API",
    description="AWS Lambda-based Medical Billing System API",
    version="1.0.0",
    # Disable automatic trailing slash redirects
    redirect_slashes=False
)

# Manual CORS handling middleware
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Only add CORS headers if origin is allowed
    origin = request.headers.get("origin")
    allowed_origins = [
        "https://d1zvnblomkhxix.cloudfront.net",
        "https://d27z0qz3ducsem.cloudfront.net",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Handle preflight requests
@app.options("/{path:path}")
async def handle_options(request: Request):
    origin = request.headers.get("origin")
    allowed_origins = [
        "https://d1zvnblomkhxix.cloudfront.net",
        "https://d27z0qz3ducsem.cloudfront.net",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    headers = {}
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "*"
    
    return Response(status_code=200, headers=headers)

# Include routers
app.include_router(patient_routes.router, prefix="/api/patients", tags=["patients"])
app.include_router(provider_routes.router, prefix="/api/providers", tags=["providers"])
app.include_router(service_routes.router, prefix="/api/services", tags=["services"])
app.include_router(appointment_routes.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(claim_routes.router, prefix="/api/claims", tags=["claims"])
app.include_router(payment_routes.router, prefix="/api/payments", tags=["payments"])
app.include_router(audit_routes.router, prefix="/api/audit", tags=["audit"])
app.include_router(ollama_routes.router, prefix="/api/ollama", tags=["ollama"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Medical Billing API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from config.db import test_connection
    
    db_status = "healthy" if test_connection() else "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "medical-billing-api",
        "version": "1.0.0",
        "environment": os.getenv("NODE_ENV", "development"),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "database": db_status
    }

# Legacy endpoints for backward compatibility
@app.post("/legacy/process-claim")
async def legacy_process_claim(claim_data: dict):
    """Legacy endpoint for processing claims"""
    try:
        return await process_claim(claim_data)
    except Exception as e:
        logger.error(f"Legacy process claim error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/legacy/check-eligibility")
async def legacy_check_eligibility(eligibility_data: dict):
    """Legacy endpoint for checking eligibility"""
    try:
        return await check_eligibility(eligibility_data)
    except Exception as e:
        logger.error(f"Legacy check eligibility error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy functions (keeping for backward compatibility)
async def process_claim(claim_data):
    """Process a medical billing claim"""
    from datetime import datetime
    import uuid
    from decimal import Decimal
    
    try:
        # Validate required fields
        required_fields = ['patientId', 'serviceDate', 'services', 'providerId', 'payerId']
        missing_fields = [field for field in required_fields if field not in claim_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Calculate total amount
        total_amount = sum(
            Decimal(str(service['quantity'])) * Decimal(str(service['unitPrice']))
            for service in claim_data['services']
        )
        
        # Generate claim ID
        claim_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Process the claim
        processed_claim = {
            'claimId': claim_id,
            'patientId': claim_data['patientId'],
            'providerId': claim_data['providerId'],
            'payerId': claim_data['payerId'],
            'serviceDate': claim_data['serviceDate'],
            'submissionDate': datetime.now().isoformat(),
            'services': claim_data['services'],
            'diagnosisCodes': claim_data.get('diagnosisCodes', []),
            'procedureCodes': claim_data.get('procedureCodes', []),
            'totalAmount': float(total_amount),
            'status': 'PENDING',
            'priority': claim_data.get('priority', 'NORMAL')
        }
        
        logger.info(f"Processed claim: {claim_id}")
        
        return {
            'success': True,
            'claim': processed_claim
        }
        
    except Exception as e:
        logger.error(f"Process claim error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def check_eligibility(eligibility_data):
    """Check patient insurance eligibility"""
    from datetime import datetime
    import uuid
    
    try:
        # Validate required fields
        required_fields = ['patientId', 'payerId', 'serviceType']
        missing_fields = [field for field in required_fields if field not in eligibility_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Simulate eligibility check
        service_type = eligibility_data['serviceType']
        
        # Different coverage based on service type
        coverage_rules = {
            'PREVENTIVE': {'coverage': 100, 'copay': 0, 'preAuth': False},
            'PRIMARY': {'coverage': 80, 'copay': 25, 'preAuth': False},
            'SPECIALIST': {'coverage': 70, 'copay': 50, 'preAuth': False},
            'EMERGENCY': {'coverage': 80, 'copay': 150, 'preAuth': False},
            'SURGERY': {'coverage': 80, 'copay': 0, 'preAuth': True},
            'DIAGNOSTIC': {'coverage': 70, 'copay': 35, 'preAuth': False}
        }
        
        rules = coverage_rules.get(service_type, {'coverage': 60, 'copay': 75, 'preAuth': True})
        
        eligibility = {
            'eligibilityId': f"ELIG-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
            'patientId': eligibility_data['patientId'],
            'payerId': eligibility_data['payerId'],
            'serviceType': service_type,
            'serviceDate': eligibility_data.get('serviceDate', datetime.now().isoformat()),
            'eligible': True,
            'coveragePercentage': rules['coverage'],
            'copay': rules['copay'],
            'deductible': 500,
            'deductibleMet': 350,
            'deductibleRemaining': 150,
            'outOfPocketMax': 5000,
            'outOfPocketMet': 1200,
            'outOfPocketRemaining': 3800,
            'requiresPreAuthorization': rules['preAuth'],
            'planName': 'Premium Health Plan',
            'groupNumber': 'GRP-123456',
            'effectiveDate': '2024-01-01',
            'terminationDate': '2024-12-31',
            'verificationDate': datetime.now().isoformat()
        }
        
        logger.info(f"Eligibility checked for patient: {eligibility_data['patientId']}")
        
        return {
            'success': True,
            'eligibility': eligibility
        }
        
    except Exception as e:
        logger.error(f"Check eligibility error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Create the Lambda handler using Mangum
handler = Mangum(app, lifespan="off", api_gateway_base_path=None)

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Handle Lambda Function URL events specifically
        if "requestContext" in event and "http" in event["requestContext"]:
            # Add missing sourceIp field for Mangum compatibility
            if "sourceIp" not in event["requestContext"]["http"]:
                event["requestContext"]["http"]["sourceIp"] = "127.0.0.1"
            
            # Ensure all required fields are present
            if "userAgent" not in event["requestContext"]["http"]:
                event["requestContext"]["http"]["userAgent"] = event.get("headers", {}).get("user-agent", "Unknown")
        
        # Use Mangum to handle the request
        return handler(event, context)
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
        # Let FastAPI handle the error response and CORS headers
        # Don't add hardcoded headers that conflict with CORS middleware
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }