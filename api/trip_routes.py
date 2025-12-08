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
    origin_neighborhood_id: int
    destination_neighborhood_id: int

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

@router.get("")
async def get_all_trips():
    """Obtener todos los viajes con nombres de barrios"""
    try:
        # Obtener todos los viajes
        trips_response = supabase.table("trip").select("*").order("trip_id", desc=True).execute()
        
        if not trips_response.data:
            return []
        
        # Log para debugging
        if trips_response.data:
            logger.info(f"Primer viaje de ejemplo: {trips_response.data[0]}")
        
        # Obtener todos los barrios para hacer el mapeo
        neighborhoods_response = supabase.table("neighborhood").select("neighborhood_id, name").execute()
        neighborhoods_map = {n['neighborhood_id']: n['name'] for n in neighborhoods_response.data}
        
        # Procesar cada viaje para agregar nombres de barrios
        trips = []
        for trip in trips_response.data:
            trip_data = {**trip}
            
            # Asegurar que trip_id esté presente (puede venir como 'id' o 'trip_id')
            if 'trip_id' not in trip_data and 'id' in trip_data:
                trip_data['trip_id'] = trip_data['id']
            
            # Agregar nombre del barrio de origen
            origin_id = trip.get('origin_neighborhood_id')
            if origin_id and origin_id in neighborhoods_map:
                trip_data['origin_neighborhood'] = neighborhoods_map[origin_id]
            else:
                trip_data['origin_neighborhood'] = 'N/A'
            
            # Agregar nombre del barrio de destino
            destination_id = trip.get('destination_neighborhood_id')
            if destination_id and destination_id in neighborhoods_map:
                trip_data['destination_neighborhood'] = neighborhoods_map[destination_id]
            else:
                trip_data['destination_neighborhood'] = 'N/A'
            
            trips.append(trip_data)
        
        return trips
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
        response = supabase.table("trip").select("*").eq("client_document", client_document).order("trip_id", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al obtener viajes del cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/driver/{driver_document}")
async def get_trips_by_driver(driver_document: str):
    """Obtener viajes de un conductor con nombres de barrios"""
    try:
        # Obtener viajes del conductor
        trips_response = supabase.table("trip").select("*").eq("driver_document", driver_document).order("trip_id", desc=True).execute()
        
        if not trips_response.data:
            return []
        
        # Obtener todos los barrios para hacer el mapeo
        neighborhoods_response = supabase.table("neighborhood").select("neighborhood_id, name").execute()
        neighborhoods_map = {n['neighborhood_id']: n['name'] for n in neighborhoods_response.data}
        
        # Procesar cada viaje para agregar nombres de barrios
        trips = []
        for trip in trips_response.data:
            trip_data = {**trip}
            
            # Asegurar que trip_id esté presente
            if 'trip_id' not in trip_data and 'id' in trip_data:
                trip_data['trip_id'] = trip_data['id']
            
            # Agregar nombre del barrio de origen
            origin_id = trip.get('origin_neighborhood_id')
            if origin_id and origin_id in neighborhoods_map:
                trip_data['origin_neighborhood'] = neighborhoods_map[origin_id]
            else:
                trip_data['origin_neighborhood'] = 'N/A'
            
            # Agregar nombre del barrio de destino
            destination_id = trip.get('destination_neighborhood_id')
            if destination_id and destination_id in neighborhoods_map:
                trip_data['destination_neighborhood'] = neighborhoods_map[destination_id]
            else:
                trip_data['destination_neighborhood'] = 'N/A'
            
            trips.append(trip_data)
        
        return trips
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

@router.post("", response_model=TripResponse)
async def create_trip(trip: TripRequest):
    """Crear nuevo viaje con origen y destino"""
    try:
        trip_data = {
            "client_document": trip.client_document,
            "driver_document": trip.driver_document,
            "vehicle_plate": trip.vehicle_plate,
            "origin_neighborhood_id": trip.origin_neighborhood_id,
            "destination_neighborhood_id": trip.destination_neighborhood_id,
            "start_time": datetime.now().isoformat(),
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

@router.delete("/{trip_id}")
async def delete_trip(trip_id: int):
    """Eliminar un viaje por ID (y sus pagos asociados)"""
    try:
        # 1. Eliminar pagos y calificaciones asociados (Cascade manual)
        try:
            supabase.table("pay").delete().eq("trip_id", trip_id).execute()
        except Exception:
            pass 

        try:
            supabase.table("rating").delete().eq("trip_id", trip_id).execute()
        except Exception:
            pass

        # 2. Eliminar el viaje
        response = supabase.table("trip").delete().eq("trip_id", trip_id).execute()
        
        if not response.data:
            # Si falló, verificamos si existe
            check = supabase.table("trip").select("trip_id").eq("trip_id", trip_id).execute()
            if not check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Viaje no encontrado"
                )
            else:
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo eliminar el viaje"
                )
        
        return {
            "success": True,
            "message": "Viaje y datos asociados eliminados exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar viaje: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check para viajes"""
    return {
        "status": "ok",
        "service": "trips",
        "message": "Servicio de viajes funcionando"
    }