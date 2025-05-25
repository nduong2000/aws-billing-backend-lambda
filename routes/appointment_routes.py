from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
import logging
from config import db

router = APIRouter()
logger = logging.getLogger("appointment_routes")

# Pydantic models for validation - updated to match schema
class AppointmentBase(BaseModel):
    patient_id: int
    provider_id: int
    appointment_date: str  # Format: YYYY-MM-DD HH:MM:SS
    reason_for_visit: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[str] = None
    reason_for_visit: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    appointment_id: int
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_appointments(
    patient_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None)
):
    try:
        query = "SELECT * FROM appointments"
        params = []
        
        # Build query conditions based on parameters
        conditions = []
        if patient_id:
            conditions.append("patient_id = %s")
            params.append(patient_id)
        if provider_id:
            conditions.append("provider_id = %s")
            params.append(provider_id)
            
        # Add WHERE clause if conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Add ORDER BY
        query += " ORDER BY appointment_date DESC"
        
        appointments = db.query(query, params)
        return appointments
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{appointment_id}", response_model=Dict[str, Any])
async def get_appointment_by_id(appointment_id: int):
    try:
        result = db.query("SELECT * FROM appointments WHERE appointment_id = %s", [appointment_id])
        if not result:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new appointment
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_appointment(appointment: AppointmentCreate):
    try:
        # Check if patient exists
        patient_check = db.query("SELECT 1 FROM patients WHERE patient_id = %s", [appointment.patient_id])
        if not patient_check:
            raise HTTPException(status_code=404, detail=f"Patient with ID {appointment.patient_id} not found")
            
        # Check if provider exists
        provider_check = db.query("SELECT 1 FROM providers WHERE provider_id = %s", [appointment.provider_id])
        if not provider_check:
            raise HTTPException(status_code=404, detail=f"Provider with ID {appointment.provider_id} not found")
        
        query_text = """
            INSERT INTO appointments (
                patient_id, provider_id, appointment_date, reason_for_visit
            )
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        values = [
            appointment.patient_id, appointment.provider_id,
            appointment.appointment_date, appointment.reason_for_visit
        ]
        result = db.query(query_text, values)
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE an appointment
@router.put("/{appointment_id}", response_model=Dict[str, Any])
async def update_appointment(appointment_id: int, appointment: AppointmentUpdate):
    try:
        # Get current appointment data
        current = db.query("SELECT * FROM appointments WHERE appointment_id = %s", [appointment_id])
        if not current:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        current_data = current[0]
        
        # Build query dynamically based on provided fields
        update_parts = []
        values = []
        
        # Only update fields that are provided
        if appointment.appointment_date is not None:
            update_parts.append("appointment_date = %s")
            values.append(appointment.appointment_date)
            
        if appointment.reason_for_visit is not None:
            update_parts.append("reason_for_visit = %s")
            values.append(appointment.reason_for_visit)
        
        # If no fields to update, return current data
        if not update_parts:
            return current_data
            
        # Build and execute query
        query_text = f"""
            UPDATE appointments
            SET {", ".join(update_parts)}
            WHERE appointment_id = %s
            RETURNING *
        """
        values.append(appointment_id)
        
        result = db.query(query_text, values)
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE an appointment
@router.delete("/{appointment_id}", response_model=Dict[str, str])
async def delete_appointment(appointment_id: int):
    try:
        # Check if appointment exists
        check_result = db.query("SELECT 1 FROM appointments WHERE appointment_id = %s", [appointment_id])
        if not check_result:
            raise HTTPException(status_code=404, detail="Appointment not found")
            
        # Check if appointment has related claims
        claim_check = db.query("""
            SELECT COUNT(*) as claim_count
            FROM claims
            WHERE appointment_id = %s
        """, [appointment_id])
        
        if claim_check and claim_check[0]['claim_count'] > 0:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete appointment with associated claims"
            )
            
        # Try to delete
        delete_result = db.query("DELETE FROM appointments WHERE appointment_id = %s", [appointment_id])
        
        if delete_result and delete_result.get("rowCount", 0) > 0:
            return {"message": "Appointment deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Appointment not found or already deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
