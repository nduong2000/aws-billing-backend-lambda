from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import logging
from config import db

router = APIRouter()
logger = logging.getLogger("provider_routes")

# Pydantic models for validation updated to match database schema
class ProviderBase(BaseModel):
    provider_name: str
    npi_number: str  # National Provider Identifier
    specialty: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None

class ProviderCreate(ProviderBase):
    pass

class ProviderUpdate(ProviderBase):
    pass

class ProviderResponse(ProviderBase):
    provider_id: int
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_providers():
    try:
        providers = db.query("SELECT * FROM providers ORDER BY provider_name")
        return providers
    except Exception as e:
        logger.error(f"Error fetching providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_id}", response_model=Dict[str, Any])
async def get_provider_by_id(provider_id: int):
    try:
        result = db.query("SELECT * FROM providers WHERE provider_id = %s", [provider_id])
        if not result:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CREATE a new provider
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_provider(provider: ProviderCreate):
    try:
        query_text = """
            INSERT INTO providers (
                provider_name, npi_number, specialty, 
                address, phone_number
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        values = [
            provider.provider_name, provider.npi_number, provider.specialty,
            provider.address, provider.phone_number
        ]
        result = db.query(query_text, values)
        return result[0]
    except Exception as e:
        # Check for unique constraint violations
        if "providers_npi_number_key" in str(e):
            raise HTTPException(status_code=409, detail=f"Provider with NPI {provider.npi_number} already exists")
        logger.error(f"Error creating provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE a provider
@router.put("/{provider_id}", response_model=Dict[str, Any])
async def update_provider(provider_id: int, provider: ProviderUpdate):
    try:
        query_text = """
            UPDATE providers
            SET provider_name = %s, npi_number = %s, specialty = %s,
                address = %s, phone_number = %s
            WHERE provider_id = %s
            RETURNING *
        """
        values = [
            provider.provider_name, provider.npi_number, provider.specialty,
            provider.address, provider.phone_number, provider_id
        ]
        result = db.query(query_text, values)
        
        if not result:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        # Check for unique constraint violations
        if "providers_npi_number_key" in str(e):
            raise HTTPException(status_code=409, detail=f"Provider with NPI {provider.npi_number} already exists")
        logger.error(f"Error updating provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# DELETE a provider
@router.delete("/{provider_id}", response_model=Dict[str, str])
async def delete_provider(provider_id: int):
    try:
        # Check if provider exists
        check_result = db.query("SELECT 1 FROM providers WHERE provider_id = %s", [provider_id])
        if not check_result:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Check if provider has appointments or claims
        dependent_records = db.query("""
            SELECT 
                (SELECT COUNT(*) FROM appointments WHERE provider_id = %s) as appointment_count,
                (SELECT COUNT(*) FROM claims WHERE provider_id = %s) as claim_count
        """, [provider_id, provider_id])
        
        if dependent_records and (
            dependent_records[0]['appointment_count'] > 0 or 
            dependent_records[0]['claim_count'] > 0
        ):
            raise HTTPException(
                status_code=409,
                detail="Cannot delete provider with associated appointments or claims"
            )
            
        # Try to delete
        delete_result = db.query("DELETE FROM providers WHERE provider_id = %s", [provider_id])
        
        if delete_result and delete_result.get("rowCount", 0) > 0:
            return {"message": "Provider deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Provider not found or already deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
