from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from decimal import Decimal
import logging
import json
import traceback
from config import db

router = APIRouter()
logger = logging.getLogger("claim_routes")

# Custom JSON encoder to handle dates and decimals
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Pydantic models for validation updated to match database schema
class ClaimItemBase(BaseModel):
    service_id: int
    charge_amount: float
    
    @validator('charge_amount')
    def validate_charge_amount(cls, v):
        if v < 0:
            raise ValueError('Charge amount must be a non-negative number')
        return v

class ClaimBase(BaseModel):
    patient_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    claim_date: str  # Format: YYYY-MM-DD
    status: str  # Submitted, Paid, Denied, Pending, Partial
    total_charge: float
    insurance_paid: Optional[float] = 0
    patient_paid: Optional[float] = 0
    notes: Optional[str] = None
    claim_items: Optional[List[ClaimItemBase]] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    status: Optional[str] = None
    insurance_paid: Optional[float] = None
    patient_paid: Optional[float] = None
    notes: Optional[str] = None

class ClaimResponse(ClaimBase):
    claim_id: int
    fraud_score: Optional[float] = None
    
    class Config:
        from_attributes = True

# Simple test endpoint that doesn't require database access
@router.get("/test", response_model=Dict[str, str])
async def test_claims_route():
    """Test endpoint that doesn't require database access"""
    return {"status": "Claims route is working"}

@router.get("/", response_model=List[Dict[str, Any]])
@router.get("", response_model=List[Dict[str, Any]])  # Handle without trailing slash
async def get_all_claims(
    patient_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    try:
        # First, test database connection
        logger.info("Testing database connection before query...")
        if hasattr(db, 'test_connection'):
            connection_result = db.test_connection()
            if not connection_result:
                logger.error("Database connection test failed")
                raise HTTPException(
                    status_code=500,
                    detail="Database connection error - failed connection test"
                )
        
        logger.info("Building query for claims...")
        query = '''
        SELECT c.*, p.first_name || ' ' || p.last_name as patient_name,
               pr.provider_name
        FROM claims c
        JOIN patients p ON c.patient_id = p.patient_id
        JOIN providers pr ON c.provider_id = pr.provider_id
        '''
        params = []
        
        # Build query conditions based on parameters
        conditions = []
        if patient_id:
            conditions.append("c.patient_id = %s")
            params.append(patient_id)
        if provider_id:
            conditions.append("c.provider_id = %s")
            params.append(provider_id)
        if status:
            conditions.append("c.status = %s")
            params.append(status)
            
        # Add WHERE clause if conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Add ORDER BY
        query += " ORDER BY c.claim_date DESC"
        
        logger.info(f"Executing query: {query} with params: {params}")
        claims = db.query(query, params)
        logger.info(f"Query successful, returned {len(claims) if claims else 0} claims")
        return claims
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error fetching claims: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.get("/{claim_id}", response_model=Dict[str, Any])
async def get_claim_by_id(claim_id: int):
    try:
        # Get the main claim
        claim_query = '''
        SELECT c.*, p.first_name || ' ' || p.last_name as patient_name,
               pr.provider_name
        FROM claims c
        JOIN patients p ON c.patient_id = p.patient_id
        JOIN providers pr ON c.provider_id = pr.provider_id
        WHERE c.claim_id = %s
        '''
        claim_result = db.query(claim_query, [claim_id])
        
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
        
        # Get payments
        payments_query = "SELECT * FROM payments WHERE claim_id = %s"
        payments = db.query(payments_query, [claim_id])
        
        # Combine the results
        claim["items"] = claim_items
        claim["payments"] = payments
        
        return claim
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error fetching claim {claim_id}: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new claim
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_claim(claim: ClaimCreate):
    try:
        # Start a transaction
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if patient exists
            cursor.execute("SELECT 1 FROM patients WHERE patient_id = %s", [claim.patient_id])
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Patient with ID {claim.patient_id} not found")
                
            # Check if provider exists
            cursor.execute("SELECT 1 FROM providers WHERE provider_id = %s", [claim.provider_id])
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Provider with ID {claim.provider_id} not found")
            
            # Check if appointment exists if provided
            if claim.appointment_id:
                cursor.execute("SELECT 1 FROM appointments WHERE appointment_id = %s", [claim.appointment_id])
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Appointment with ID {claim.appointment_id} not found")
            
            # Insert main claim record
            cursor.execute("""
                INSERT INTO claims (
                    patient_id, provider_id, appointment_id, claim_date, 
                    status, total_charge, insurance_paid, 
                    patient_paid, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING claim_id
            """, [
                claim.patient_id, claim.provider_id, claim.appointment_id,
                claim.claim_date, claim.status, claim.total_charge,
                claim.insurance_paid, claim.patient_paid, claim.notes
            ])
            
            claim_id = cursor.fetchone()["claim_id"]
            
            # Insert claim items if provided
            if claim.claim_items:
                for item in claim.claim_items:
                    cursor.execute("""
                        INSERT INTO claim_items (
                            claim_id, service_id, charge_amount
                        )
                        VALUES (%s, %s, %s)
                    """, [
                        claim_id, item.service_id, item.charge_amount
                    ])
            
            # Commit the transaction
            conn.commit()
            
            # Fetch the complete claim for response
            return await get_claim_by_id(claim_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating claim: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error creating claim: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE a claim
@router.put("/{claim_id}", response_model=Dict[str, Any])
async def update_claim(claim_id: int, claim: ClaimUpdate):
    try:
        # Check if claim exists
        check_result = db.query("SELECT 1 FROM claims WHERE claim_id = %s", [claim_id])
        if not check_result:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Build query dynamically based on provided fields
        update_parts = []
        values = []
        
        # Only update fields that are provided
        if claim.status is not None:
            update_parts.append("status = %s")
            values.append(claim.status)
        
        if claim.insurance_paid is not None:
            update_parts.append("insurance_paid = %s")
            values.append(claim.insurance_paid)
            
        if claim.patient_paid is not None:
            update_parts.append("patient_paid = %s")
            values.append(claim.patient_paid)
            
        if claim.notes is not None:
            update_parts.append("notes = %s")
            values.append(claim.notes)
        
        # If no fields to update, return current claim
        if not update_parts:
            return await get_claim_by_id(claim_id)
            
        # Build and execute query
        query_text = f"""
            UPDATE claims
            SET {", ".join(update_parts)}
            WHERE claim_id = %s
            RETURNING claim_id
        """
        values.append(claim_id)
        
        result = db.query(query_text, values)
        
        # Fetch the updated claim
        return await get_claim_by_id(claim_id)
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error updating claim {claim_id}: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE a claim
@router.delete("/{claim_id}", response_model=Dict[str, str])
async def delete_claim(claim_id: int):
    try:
        # Start a transaction
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if claim exists
            cursor.execute("SELECT 1 FROM claims WHERE claim_id = %s", [claim_id])
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Claim not found")
            
            # Check for payments
            cursor.execute("SELECT COUNT(*) as payment_count FROM payments WHERE claim_id = %s", [claim_id])
            payment_count = cursor.fetchone()["payment_count"]
            
            if payment_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete claim with associated payments. Delete payments first."
                )
            
            # Delete claim items first
            cursor.execute("DELETE FROM claim_items WHERE claim_id = %s", [claim_id])
            
            # Then delete the claim
            cursor.execute("DELETE FROM claims WHERE claim_id = %s", [claim_id])
            
            # Commit the transaction
            conn.commit()
            
            return {"message": "Claim and associated items deleted successfully"}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting claim {claim_id}: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error deleting claim {claim_id}: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

# Audit endpoint for claims
@router.post("/{claim_id}/audit", response_model=Dict[str, Any])
async def audit_claim(claim_id: int):
    try:
        # Get the claim data
        claim_data = await get_claim_by_id(claim_id)
        
        # Import the audit function from audit_routes
        from routes.audit_routes import process_audit_request, AuditRequest
        
        # Prepare the data for audit
        formatted_claim = json.dumps(claim_data, indent=2, cls=CustomJSONEncoder)
        
        # Call the audit function
        audit_result = await process_audit_request(AuditRequest(claim_data=formatted_claim))
        
        return audit_result
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Error auditing claim {claim_id}: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))
