import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import sys
import sqlite3
import datetime

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

app = FastAPI(title="Medical Billing API")

# Configure CORS with expanded settings
allowed_origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "https://duong.casa",
    "https://billing-system.duong.casa",
    "https://dj3a7xz7qtdtg.cloudfront.net",
    "https://billing.duong.casa",
    "https://main.d31p6vf8ghge1r.amplifyapp.com",  # Add Amplify URL
    # Additional origins for development/testing
    "http://localhost:3000",
    "http://localhost:8000"
]

# Log the configured origins
logger.info(f"Configuring CORS with allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Length", "Content-Type", "Authorization"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Add a middleware to log CORS info for debugging
@app.middleware("http")
async def log_requests_and_add_cors(request: Request, call_next):
    # Log the request details
    logger.info(f"Request: {request.method} {request.url.path} - Origin: {request.headers.get('origin', 'None')}")
    
    # Process the request through all other middleware and get the response
    response = await call_next(request)
    
    # Log the response details
    logger.info(f"Response: {response.status_code} - CORS Headers: {response.headers.get('access-control-allow-origin', 'None')}")
    
    return response

logger.info("Middleware configured.")

# Base route with CORS info
@app.get("/")
async def root():
    cors_info = {
        "allowed_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": "All headers allowed"
    }
    return {
        "message": "Medical Billing API Running!",
        "cors_configuration": cors_info
    }

# Add new route to execute SQL queries from JavaScript
class QueryRequest(BaseModel):
    query: str
    params: List[Any] = []

@app.post("/api/db/query", response_model=List[Dict[str, Any]])
async def execute_query(query_request: QueryRequest):
    from config import db
    try:
        # Convert PostgreSQL-style parameters ($1, $2) to SQLite-style (?)
        query_text = query_request.query.replace("$1", "?").replace("$2", "?").replace("$3", "?").replace("$4", "?").replace("$5", "?")
        result = db.query(query_text, query_request.params)
        return result if result else []
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
app.include_router(patient_router, prefix="/api/patients", tags=["patients"])
app.include_router(provider_router, prefix="/api/providers", tags=["providers"])
app.include_router(service_router, prefix="/api/services", tags=["services"])
app.include_router(appointment_router, prefix="/api/appointments", tags=["appointments"])
app.include_router(claim_router, prefix="/api/claims", tags=["claims"])
app.include_router(payment_router, prefix="/api/payments", tags=["payments"])
app.include_router(ollama_router, prefix="/api/ollama-test", tags=["ollama"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])

logger.info("Routes configured.")

# Debug endpoint (only in development)
@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    if os.getenv("NODE_ENV") != "production":
        routes = []
        for route in app.routes:
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, "methods") else []
            })
        return sorted(routes, key=lambda x: x["path"])
    else:
        raise HTTPException(status_code=404, detail="Not found")

# Debug endpoint for testing CORS
@app.options("/debug/cors-test", include_in_schema=False)
async def cors_test_options():
    return {"message": "CORS preflight request successful"}

@app.get("/debug/cors-test", include_in_schema=False)
async def cors_test():
    return {"message": "CORS GET request successful"}

@app.post("/debug/echo", include_in_schema=False)
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

if __name__ == "__main__":
    import uvicorn
    from config.db_init import print_db_summary, initialize_db
    
    print("Initializing in-memory medical billing database...")
    conn = initialize_db()
    
    print_db_summary(conn)
    
    port = int(os.getenv("PORT", "5001"))
    print(f"\nAPI server is running on port {port}... The database is in memory and will be lost when the server stops.")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)