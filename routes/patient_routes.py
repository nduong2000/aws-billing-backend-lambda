from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import logging
from config import db

router = APIRouter()
logger = logging.getLogger("patient_routes")

# Pydantic models for validation - updated to match SQL schema
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # Format: YYYY-MM-DD
    address: Optional[str] = None
    phone_number: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class PatientResponse(PatientBase):
    patient_id: int
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[Dict[str, Any]])
@router.get("", response_model=List[Dict[str, Any]])  # Handle without trailing slash
async def get_all_patients():
    try:
        patients = db.query("SELECT * FROM patients ORDER BY last_name, first_name")
        return patients
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}", response_model=Dict[str, Any])
async def get_patient_by_id(patient_id: int):
    try:
        result = db.query("SELECT * FROM patients WHERE patient_id = %s", [patient_id])
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new patient
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_patient(patient: PatientCreate):
    try:
        query_text = """
            INSERT INTO patients (
                first_name, last_name, date_of_birth,
                address, phone_number, insurance_provider, insurance_policy_number
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        values = [
            patient.first_name, patient.last_name, patient.date_of_birth,
            patient.address, patient.phone_number, patient.insurance_provider, 
            patient.insurance_policy_number
        ]
        result = db.query(query_text, values)
        return result[0]
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE a patient
@router.put("/{patient_id}", response_model=Dict[str, Any])
async def update_patient(patient_id: int, patient: PatientUpdate):
    try:
        query_text = """
            UPDATE patients
            SET first_name = %s, last_name = %s, date_of_birth = %s,
                address = %s, phone_number = %s, insurance_provider = %s, 
                insurance_policy_number = %s
            WHERE patient_id = %s
            RETURNING *
        """
        values = [
            patient.first_name, patient.last_name, patient.date_of_birth,
            patient.address, patient.phone_number, patient.insurance_provider,
            patient.insurance_policy_number, patient_id
        ]
        result = db.query(query_text, values)
        
        if not result:
            raise HTTPException(status_code=404, detail="Patient not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE a patient
@router.delete("/{patient_id}", response_model=Dict[str, str])
async def delete_patient(patient_id: int):
    try:
        # Check if patient exists
        check_result = db.query("SELECT 1 FROM patients WHERE patient_id = %s", [patient_id])
        if not check_result:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if patient has appointments or claims
        dependent_records = db.query("""
            SELECT 
                (SELECT COUNT(*) FROM appointments WHERE patient_id = %s) as appointment_count,
                (SELECT COUNT(*) FROM claims WHERE patient_id = %s) as claim_count
        """, [patient_id, patient_id])
        
        if dependent_records and (
            dependent_records[0]['appointment_count'] > 0 or 
            dependent_records[0]['claim_count'] > 0
        ):
            raise HTTPException(
                status_code=409,
                detail="Cannot delete patient with associated appointments or claims"
            )
            
        # Try to delete
        delete_result = db.query("DELETE FROM patients WHERE patient_id = %s", [patient_id])
        
        if delete_result and delete_result.get("rowCount", 0) > 0:
            return {"message": "Patient deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Patient not found or already deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
