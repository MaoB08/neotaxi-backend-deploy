# ============================================
# ARCHIVO: api/additional_routes.py
# ============================================
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from core.database import supabase
from typing import Optional, List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== NEIGHBORHOODS ====================

@router.get("/neighborhoods")
async def get_neighborhoods():
    """Obtener todos los barrios"""
    try:
        response = supabase.table("neighborhood").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VEHICLES ====================

@router.get("/vehicles")
async def get_vehicles():
    """Obtener todos los vehículos"""
    try:
        response = supabase.table("vehicle").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/available")
async def get_available_vehicles():
    """Obtener vehículos disponibles (con conductor activo)"""
    try:
        response = supabase.table("driver_vehicle")\
            .select("*, vehicle(*), driver(*)")\
            .eq("status", "A")\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/driver/{driver_document}")
async def get_driver_vehicles(driver_document: str):
    """Obtener vehículos de un conductor específico"""
    try:
        response = supabase.table("driver_vehicle")\
            .select("vehicle(*)")\
            .eq("driver_document", driver_document)\
            .eq("status", "A")\
            .execute()
        # Extraer solo los datos del vehículo
        vehicles = [item["vehicle"] for item in response.data if item.get("vehicle")]
        return vehicles
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/methods")
async def get_payment_methods():
    """Obtener métodos de pago"""
    try:
        response = supabase.table("method").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RATINGS ====================

@router.get("/ratings/trip/{trip_id}")
async def get_rating_by_trip(trip_id: int):
    """Obtener calificación de un viaje"""
    try:
        response = supabase.table("rating")\
            .select("*")\
            .eq("trip_id", trip_id)\
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class RatingCreate(BaseModel):
    trip_id: int
    score: int
    comment: Optional[str] = None

@router.post("/ratings")
async def create_rating(rating: RatingCreate):
    """Crear calificación para un viaje"""
    try:
        if rating.score < 1 or rating.score > 5:
            raise HTTPException(status_code=400, detail="Score debe estar entre 1 y 5")
        
        response = supabase.table("rating").insert({
            "trip_id": rating.trip_id,
            "score": rating.score,
            "comment": rating.comment
        }).execute()
        
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INCIDENTS ====================

@router.get("/incidents")
async def get_incidents():
    """Obtener todos los incidentes"""
    try:
        response = supabase.table("incident").select("*, trip(*)").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/incidents/trip/{trip_id}")
async def get_incidents_by_trip(trip_id: int):
    """Obtener incidentes de un viaje"""
    try:
        response = supabase.table("incident")\
            .select("*")\
            .eq("trip_id", trip_id)\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ALERTS ====================

@router.get("/alerts")
async def get_alerts():
    """Obtener todas las alertas"""
    try:
        # 1. Obtener alertas con antecedente
        response = supabase.table("alert").select("*, antecedent(type(*))").order("datetime", desc=True).execute()
        alerts = response.data

        # 2. Obtener documentos de usuarios manualmente usando record_id
        if alerts:
            # Extraer IDs de registros faciales que no sean nulos
            record_ids = [a['record_id'] for a in alerts if a.get('record_id')]
            
            if record_ids:
                # Consultar biometric_record (usa IDs enteros) en lugar de facial_encodings (UUIDs)
                try:
                    # Consultar biometric_record usando record_id
                    faces = supabase.table("biometric_record").select("record_id, client_document").in_("record_id", record_ids).execute()
                    
                    # Crear mapa id -> info
                    face_map = {f['record_id']: f for f in faces.data}
                    
                    # Enriquecer alertas
                    for alert in alerts:
                        rid = alert.get('record_id')
                        if rid and rid in face_map:
                            # Mapear client_document a user_document para que el frontend lo entienda
                            alert['facial_encodings'] = face_map[rid] 
                            alert['user_document'] = face_map[rid].get('client_document')
                            # Frontend espera user_type tambien para saber si es C o D
                            if alert['user_document']:
                                alert['facial_encodings']['user_type'] = 'client' 
                except Exception as inner_e:
                     logger.error(f"Error fetching biometric details: {inner_e}")

        return alerts
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/level/{level}")
async def get_alerts_by_level(level: int):
    """Obtener alertas por nivel de prioridad"""
    try:
        response = supabase.table("alert")\
            .select("*")\
            .eq("level", level)\
            .order("datetime", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANTECEDENTS ====================

@router.get("/antecedents")
async def get_antecedents():
    """Obtener todos los antecedentes"""
    try:
        response = supabase.table("antecedent")\
            .select("*, client(*), type(*)")\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/antecedents/client/{document}")
async def get_antecedents_by_client(document: str):
    """Obtener antecedentes de un cliente"""
    try:
        response = supabase.table("antecedent")\
            .select("*, type(*)")\
            .eq("client_document", document)\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== BIOMETRIC ====================

@router.get("/biometric/client/{document}")
async def get_biometric_records(document: str):
    """Obtener registros biométricos de un cliente"""
    try:
        response = supabase.table("biometric_record")\
            .select("*")\
            .eq("client_document", document)\
            .order("datetime", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATISTICS ====================

@router.get("/stats/overview")
async def get_overview_stats():
    """Obtener estadísticas generales del sistema"""
    try:
        # Contar registros en diferentes tablas
        clients = supabase.table("client").select("*", count="exact").execute()
        drivers = supabase.table("driver").select("*", count="exact").execute()
        trips = supabase.table("trip").select("*", count="exact").execute()
        active_trips = supabase.table("trip").select("*", count="exact").eq("status", "N").execute()
        
        return {
            "total_clients": len(clients.data) if clients.data else 0,
            "total_drivers": len(drivers.data) if drivers.data else 0,
            "total_trips": len(trips.data) if trips.data else 0,
            "active_trips": len(active_trips.data) if active_trips.data else 0
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))