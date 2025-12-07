# ============================================
# ARCHIVO: api/driver_routes.py
# ============================================
from fastapi import APIRouter, HTTPException, status
from models.schemas import DriverResponse, DriverUpdate, DriverApproval, ApiResponse
from core.database import supabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{document}", response_model=DriverResponse)
async def get_driver(document: str):
    """Obtener información de un conductor por documento"""
    try:
        response = supabase.table("driver").select("*").eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conductor no encontrado"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener conductor: {str(e)}"
        )

@router.put("/{document}", response_model=ApiResponse)
async def update_driver(document: str, data: DriverUpdate):
    """Actualizar información de un conductor"""
    try:
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        response = supabase.table("driver").update(update_data).eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conductor no encontrado"
            )
        
        return ApiResponse(
            success=True,
            message="Conductor actualizado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar conductor: {str(e)}"
        )

@router.post("/{document}/approve", response_model=ApiResponse)
async def approve_driver(document: str, approval: DriverApproval):
    """Aprobar, rechazar o suspender un conductor"""
    try:
        # Mapa de estados para convertir a CHAR(1) compatible con la BD
        status_map = {
            "APPROVED": "A",
            "REJECTED": "R",
            "SUSPENDED": "S",
            "PENDING": "P",
            "ACTIVE": "A",   # Alias para APPROVED
            "INACTIVE": "I", # Nuevo estado
            "A": "A",
            "R": "R",
            "S": "S",
            "P": "P",
            "I": "I"
        }
        
        # Validar si es un estado válido (largo o corto)
        valid_statuses = list(status_map.keys()) + list(status_map.values())
        
        if approval.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
            )
        
        # Obtener el código corto para la base de datos
        db_status = status_map.get(approval.status, approval.status)
        
        response = supabase.table("driver").update({"status": db_status}).eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conductor no encontrado"
            )
        
        status_messages = {
            "APPROVED": "Conductor aprobado exitosamente",
            "REJECTED": "Conductor rechazado",
            "SUSPENDED": "Conductor suspendido",
            "PENDING": "Conductor en estado pendiente",
            "ACTIVE": "Conductor activado exitosamente",
            "INACTIVE": "Conductor desactivado exitosamente",
            "A": "Conductor aprobado exitosamente",
            "R": "Conductor rechazado",
            "S": "Conductor suspendido",
            "P": "Conductor en estado pendiente",
            "I": "Conductor desactivado (Inactivo)"
        }
        
        logger.info(f"✅ Conductor {document} cambió a estado: {db_status}")
        
        return ApiResponse(
            success=True,
            message=status_messages.get(approval.status, "Estado actualizado correctamente")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar estado del conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )

@router.get("/")
async def list_drivers(status_filter: str = None):
    """Listar conductores (opcionalmente filtrados por estado)"""
    try:
        query = supabase.table("driver").select("*")
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        response = query.execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al listar conductores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar conductores: {str(e)}"
        )

@router.get("/pending/list", response_model=list[DriverResponse])
async def list_pending_drivers():
    """Listar conductores pendientes de aprobación"""
    try:
        response = supabase.table("driver").select("*").eq("status", "PENDING").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al listar conductores pendientes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar conductores pendientes: {str(e)}"
        )

@router.delete("/{document}", response_model=ApiResponse)
async def delete_driver(document: str):
    """Eliminar un conductor"""
    try:
        response = supabase.table("driver").delete().eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conductor no encontrado"
            )
        
        return ApiResponse(
            success=True,
            message="Conductor eliminado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar conductor: {str(e)}"
        )