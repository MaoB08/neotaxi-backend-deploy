# ============================================
# ARCHIVO: api/client_routes.py
# ============================================
from fastapi import APIRouter, HTTPException, status
from models.schemas import ClientResponse, ClientUpdate, ApiResponse
from core.database import supabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{document}", response_model=ClientResponse)
async def get_client(document: str):
    """Obtener información de un cliente por documento"""
    try:
        response = supabase.table("client").select("*").eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener cliente: {str(e)}"
        )

@router.put("/{document}", response_model=ApiResponse)
async def update_client(document: str, data: ClientUpdate):
    """Actualizar información de un cliente"""
    try:
        # Preparar datos para actualizar (solo campos no nulos)
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        response = supabase.table("client").update(update_data).eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        return ApiResponse(
            success=True,
            message="Cliente actualizado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar cliente: {str(e)}"
        )

@router.delete("/{document}", response_model=ApiResponse)
async def delete_client(document: str):
    """Eliminar un cliente"""
    try:
        # Eliminar de CLIENT (esto también eliminará de USER por CASCADE)
        response = supabase.table("client").delete().eq("document", document).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        return ApiResponse(
            success=True,
            message="Cliente eliminado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar cliente: {str(e)}"
        )

@router.get("/", response_model=list[ClientResponse])
async def list_clients(limit: int = 100, offset: int = 0):
    """Listar todos los clientes"""
    try:
        response = supabase.table("client").select("*").range(offset, offset + limit - 1).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error al listar clientes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar clientes: {str(e)}"
        )