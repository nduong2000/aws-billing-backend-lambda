from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import logging
from config import db

router = APIRouter()
logger = logging.getLogger("service_routes")

# Pydantic models for validation
class ServiceBase(BaseModel):
    cpt_code: str
    description: str
    standard_charge: float
    
    @validator('standard_charge')
    def validate_charge(cls, v):
        if v < 0:
            raise ValueError('Standard charge must be a non-negative number')
        return v

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    service_id: int
    
    class Config:
        orm_mode = True

# GET all services
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_services():
    try:
        services = db.query("SELECT * FROM services ORDER BY cpt_code")
        return services
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GET single service by ID
@router.get("/{service_id}", response_model=Dict[str, Any])
async def get_service_by_id(service_id: int):
    try:
        result = db.query("SELECT * FROM services WHERE service_id = %s", [service_id])
        if not result:
            raise HTTPException(status_code=404, detail="Service not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new service
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_service(service: ServiceCreate):
    try:
        query_text = """
            INSERT INTO services (cpt_code, description, standard_charge)
            VALUES (%s, %s, %s)
            RETURNING *
        """
        values = [service.cpt_code, service.description, service.standard_charge]
        result = db.query(query_text, values)
        return result[0]
    except Exception as e:
        if "services_cpt_code_key" in str(e):
            raise HTTPException(status_code=409, detail=f"Service with CPT code {service.cpt_code} already exists.")
        logger.error(f"Error creating service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE a service
@router.put("/{service_id}", response_model=Dict[str, Any])
async def update_service(service_id: int, service: ServiceUpdate):
    try:
        query_text = """
            UPDATE services
            SET cpt_code = %s, description = %s, standard_charge = %s
            WHERE service_id = %s
            RETURNING *
        """
        values = [service.cpt_code, service.description, service.standard_charge, service_id]
        result = db.query(query_text, values)
        
        if not result:
            raise HTTPException(status_code=404, detail="Service not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        if "services_cpt_code_key" in str(e):
            raise HTTPException(status_code=409, detail=f"Service with CPT code {service.cpt_code} already exists.")
        logger.error(f"Error updating service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE a service
@router.delete("/{service_id}", response_model=Dict[str, str])
async def delete_service(service_id: int):
    try:
        # Check if service exists
        check_result = db.query("SELECT 1 FROM services WHERE service_id = %s", [service_id])
        if not check_result:
            raise HTTPException(status_code=404, detail="Service not found")
            
        # Try to delete
        delete_result = db.query("DELETE FROM services WHERE service_id = %s", [service_id])
        
        if delete_result and delete_result.get("rowCount", 0) > 0:
            return {"message": "Service deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Service not found or already deleted")
    except HTTPException:
        raise
    except Exception as e:
        if "23503" in str(e):  # Foreign key violation
            logger.error(f"Error deleting service {service_id} due to foreign key constraint")
            raise HTTPException(
                status_code=409, 
                detail="Cannot delete service. It is associated with existing claim items."
            )
        logger.error(f"Error deleting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 