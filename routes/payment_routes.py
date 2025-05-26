from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import date
import logging
from config import db

router = APIRouter()
logger = logging.getLogger("payment_routes")

# Pydantic models for validation - updated to match schema
class PaymentBase(BaseModel):
    claim_id: int
    payment_date: str  # Format: YYYY-MM-DD
    amount: float
    payment_source: str  # 'Insurance' or 'Patient'
    reference_number: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Payment amount must be positive')
        return v
    
    @validator('payment_source')
    def validate_payment_source(cls, v):
        allowed_values = ['Insurance', 'Patient']
        if v not in allowed_values:
            raise ValueError(f'Payment source must be one of: {", ".join(allowed_values)}')
        return v

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    payment_date: Optional[str] = None
    amount: Optional[float] = None
    payment_source: Optional[str] = None
    reference_number: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Payment amount must be positive')
        return v
    
    @validator('payment_source')
    def validate_payment_source(cls, v):
        if v is not None:
            allowed_values = ['Insurance', 'Patient']
            if v not in allowed_values:
                raise ValueError(f'Payment source must be one of: {", ".join(allowed_values)}')
        return v

class PaymentResponse(PaymentBase):
    payment_id: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[Dict[str, Any]])
@router.get("", response_model=List[Dict[str, Any]])  # Handle without trailing slash
async def get_all_payments(
    claim_id: Optional[int] = Query(None)
):
    try:
        query = "SELECT * FROM payments"
        params = []
        
        if claim_id:
            query += " WHERE claim_id = %s"
            params.append(claim_id)
            
        query += " ORDER BY payment_date DESC"
        
        payments = db.query(query, params)
        return payments
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{payment_id}", response_model=Dict[str, Any])
async def get_payment_by_id(payment_id: int):
    try:
        result = db.query("SELECT * FROM payments WHERE payment_id = %s", [payment_id])
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new payment
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_payment(payment: PaymentCreate):
    try:
        # Check if claim exists
        claim_check = db.query("SELECT * FROM claims WHERE claim_id = %s", [payment.claim_id])
        if not claim_check:
            raise HTTPException(status_code=404, detail=f"Claim with ID {payment.claim_id} not found")
        
        # Create the payment
        query_text = """
            INSERT INTO payments (
                claim_id, payment_date, amount, payment_source,
                reference_number
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        values = [
            payment.claim_id, payment.payment_date, payment.amount,
            payment.payment_source, payment.reference_number
        ]
        
        result = db.query(query_text, values)
        created_payment = result[0]
        
        # Update the claim's payment amounts
        claim = claim_check[0]
        if payment.payment_source.lower() == 'insurance':
            new_insurance_paid = claim['insurance_paid'] + payment.amount
            db.query(
                "UPDATE claims SET insurance_paid = %s WHERE claim_id = %s",
                [new_insurance_paid, payment.claim_id]
            )
        elif payment.payment_source.lower() == 'patient':
            new_patient_paid = claim['patient_paid'] + payment.amount
            db.query(
                "UPDATE claims SET patient_paid = %s WHERE claim_id = %s",
                [new_patient_paid, payment.claim_id]
            )
        
        return created_payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new payment for a claim
@router.post("/claims/{claim_id}/payments", response_model=Dict[str, Any], status_code=201)
async def create_payment_for_claim(
    claim_id: int = Path(..., description="ID of the claim to add payment to"),
    payment: PaymentCreate = Body(...)
):
    # Ensure the payment's claim_id matches the path parameter
    if payment.claim_id != claim_id:
        payment.claim_id = claim_id
        
    # Use the standard create payment function
    return await create_payment(payment)

# UPDATE a payment
@router.put("/{payment_id}", response_model=Dict[str, Any])
async def update_payment(payment_id: int, payment: PaymentUpdate):
    try:
        # Get current payment data
        current_payment = db.query("SELECT * FROM payments WHERE payment_id = %s", [payment_id])
        if not current_payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Build query dynamically based on provided fields
        update_parts = []
        values = []
        
        # Only update fields that are provided
        if payment.payment_date is not None:
            update_parts.append("payment_date = %s")
            values.append(payment.payment_date)
        
        if payment.amount is not None:
            # If amount is changing, we need to update the claim totals
            old_amount = current_payment[0]['amount']
            amount_difference = payment.amount - old_amount
            
            update_parts.append("amount = %s")
            values.append(payment.amount)
            
            # We'll handle the claim update after the payment update
        
        if payment.payment_source is not None:
            update_parts.append("payment_source = %s")
            values.append(payment.payment_source)
            
        if payment.reference_number is not None:
            update_parts.append("reference_number = %s")
            values.append(payment.reference_number)
        
        # If no fields to update, return current data
        if not update_parts:
            return current_payment[0]
            
        # Build and execute query
        query_text = f"""
            UPDATE payments
            SET {", ".join(update_parts)}
            WHERE payment_id = %s
            RETURNING *
        """
        values.append(payment_id)
        
        result = db.query(query_text, values)
        updated_payment = result[0]
        
        # If amount changed, update the claim totals
        if payment.amount is not None and amount_difference != 0:
            claim_id = current_payment[0]['claim_id']
            payment_source = updated_payment['payment_source'].lower()
            
            # Get current claim data
            claim = db.query("SELECT * FROM claims WHERE claim_id = %s", [claim_id])[0]
            
            if payment_source == 'insurance':
                new_insurance_paid = claim['insurance_paid'] + amount_difference
                db.query(
                    "UPDATE claims SET insurance_paid = %s WHERE claim_id = %s",
                    [new_insurance_paid, claim_id]
                )
            elif payment_source == 'patient':
                new_patient_paid = claim['patient_paid'] + amount_difference
                db.query(
                    "UPDATE claims SET patient_paid = %s WHERE claim_id = %s",
                    [new_patient_paid, claim_id]
                )
        
        return updated_payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE a payment
@router.delete("/{payment_id}", response_model=Dict[str, str])
async def delete_payment(payment_id: int):
    try:
        # Get payment data before deletion
        payment = db.query("SELECT * FROM payments WHERE payment_id = %s", [payment_id])
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment_data = payment[0]
        claim_id = payment_data['claim_id']
        payment_amount = payment_data['amount']
        payment_source = payment_data['payment_source'].lower()
        
        # Delete the payment
        delete_result = db.query("DELETE FROM payments WHERE payment_id = %s", [payment_id])
        
        if delete_result and delete_result.get("rowCount", 0) > 0:
            # Update the claim totals
            claim = db.query("SELECT * FROM claims WHERE claim_id = %s", [claim_id])[0]
            
            if payment_source == 'insurance':
                new_insurance_paid = max(0, claim['insurance_paid'] - payment_amount)
                db.query(
                    "UPDATE claims SET insurance_paid = %s WHERE claim_id = %s",
                    [new_insurance_paid, claim_id]
                )
            elif payment_source == 'patient':
                new_patient_paid = max(0, claim['patient_paid'] - payment_amount)
                db.query(
                    "UPDATE claims SET patient_paid = %s WHERE claim_id = %s",
                    [new_patient_paid, claim_id]
                )
            
            return {"message": "Payment deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Payment not found or already deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment {payment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
