# ============================================
# ARCHIVO: api/trip_routes.py
# ============================================
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from core.database import supabase
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter()  # ← IMPORTANTE: Esta línea DEBE existir
logger = logging.getLogger(__name__)

# ==================== MODELOS ====================

class TripRequest(BaseModel):
    client_document: str
    driver_document: str
    vehicle_plate: str
    neighborhood_id: int

class TripResponse(BaseModel):
    success: bool
    trip_id: int
    message: str

class ActiveTrip(BaseModel):
    trip_id: int
    client_name: str
    driver_name: str
    vehicle_plate: str
    neighborhood: str
    start_time: str
    status: str

# ==================== ENDPOINTS ====================

@router.get("/")
async def get_all_trips():
    """Obtener todos los viajes"""
    try:
        response = supabase.table("trip").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al obtener viajes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener viajes: {str(e)}"
        )

@router.get("/client/{client_document}")
async def get_trips_by_client(client_document: str):
    """Obtener viajes de un cliente"""
    try:
        response = supabase.table("trip").select("*").eq("client_document", client_document).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al obtener viajes del cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/driver/{driver_document}")
async def get_trips_by_driver(driver_document: str):
    """Obtener viajes de un conductor"""
    try:
        response = supabase.table("trip").select("*").eq("driver_document", driver_document).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al obtener viajes del conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/active")
async def get_active_trips():
    """Obtener viajes activos (status = 'N')"""
    try:
        response = supabase.table("trip").select("*").eq("status", "N").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al obtener viajes activos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("/", response_model=TripResponse)
async def create_trip(trip: TripRequest):
    """Crear nuevo viaje"""
    try:
        trip_data = {
            "client_document": trip.client_document,
            "driver_document": trip.driver_document,
            "vehicle_plate": trip.vehicle_plate,
            "neighborhood_id": trip.neighborhood_id,
            "status": "N"  # N = En curso
        }
        
        response = supabase.table("trip").insert(trip_data).execute()
        
        if response.data:
            return TripResponse(
                success=True,
                trip_id=response.data[0]["trip_id"],
                message="Viaje creado exitosamente"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear viaje"
            )
    except Exception as e:
        logger.error(f"Error al crear viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.put("/{trip_id}/finish")
async def finish_trip(trip_id: int):
    """Finalizar viaje"""
    try:
        update_data = {
            "end_time": datetime.now().isoformat(),
            "status": "F"  # F = Finalizado
        }
        
        response = supabase.table("trip").update(update_data).eq("trip_id", trip_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al finalizar viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/{trip_id}")
async def get_trip_by_id(trip_id: int):
    """Obtener viaje por ID"""
    try:
        response = supabase.table("trip").select("*").eq("trip_id", trip_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check para viajes"""
    return {
        "status": "ok",
        "service": "trips",
        "message": "Servicio de viajes funcionando"
    }