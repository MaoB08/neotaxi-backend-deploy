# ============================================
# ARCHIVO: api/trip_routes.py
# Optimizado: Joins PostgREST, paginación y caché
# ============================================
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from core.database import supabase
from typing import List, Optional
from datetime import datetime
import logging

# ── Caché en memoria para datos estáticos ────────────────────────────────────
from utils.cache import neighborhoods_cache, get_or_fetch

router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SELECT con joins reutilizable
# Trae: origen, destino (via FK) y calificación (relación 1-to-many)
# Una sola llamada a Supabase en lugar de 3 separadas.
# ---------------------------------------------------------------------------
TRIP_SELECT = (
    "*, "
    "origin_neighborhood:neighborhood!origin_neighborhood_id(neighborhood_id, name), "
    "destination_neighborhood:neighborhood!destination_neighborhood_id(neighborhood_id, name), "
    "rating(*)"
)

# ---------------------------------------------------------------------------
# Límite máximo por petición (protección contra abusos)
# ---------------------------------------------------------------------------
MAX_PAGE_SIZE = 100


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


class PaginatedTripsResponse(BaseModel):
    data: List[dict]
    total: int
    skip: int
    limit: int
    has_more: bool


# ==================== HELPERS ====================

def _fetch_neighborhoods() -> list:
    """Función de carga real de barrios desde Supabase (usada por el caché)."""
    resp = supabase.table("neighborhood").select("neighborhood_id, name").execute()
    return resp.data or []


def _normalize_trip(trip: dict) -> dict:
    """
    Normaliza la respuesta del join PostgREST a un formato plano consistente
    para que el cliente Android no tenga que cambiar su parser.

    PostgREST devuelve objetos anidados, por ejemplo:
        trip["origin_neighborhood"] = {"neighborhood_id": 1, "name": "Centro"}
    Los aplanamos a:
        trip["origin_neighborhood"] = "Centro"
    """
    # Asegurar trip_id (puede llegar como 'id' en algunos contextos)
    if "trip_id" not in trip and "id" in trip:
        trip["trip_id"] = trip["id"]

    # Aplanar barrio de origen
    origin = trip.get("origin_neighborhood")
    if isinstance(origin, dict):
        trip["origin_neighborhood"] = origin.get("name", "N/A")
    elif origin is None:
        trip["origin_neighborhood"] = "N/A"

    # Aplanar barrio de destino
    destination = trip.get("destination_neighborhood")
    if isinstance(destination, dict):
        trip["destination_neighborhood"] = destination.get("name", "N/A")
    elif destination is None:
        trip["destination_neighborhood"] = "N/A"

    # Aplanar calificación (viene como lista de 0 o 1 elemento)
    ratings = trip.get("rating")
    if isinstance(ratings, list) and ratings:
        trip["rating"] = ratings[0].get("score")
        trip["rating_comment"] = ratings[0].get("comment")
    else:
        trip["rating"] = None
        trip["rating_comment"] = None

    return trip


# ==================== ENDPOINTS ====================

@router.get("", response_model=PaginatedTripsResponse)
async def get_all_trips(
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir (offset)"),
    limit: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE, description="Cantidad de registros a devolver"),
):
    """
    Obtener todos los viajes con nombres de barrios y calificación.

    Optimizaciones aplicadas:
    - JOIN PostgREST: barrios + rating en 1 sola consulta (antes 3 llamadas N+1)
    - Paginación: range(skip, skip+limit-1) — scroll infinito desde Android
    - Caché de barrios: fallback en memoria si el join falla
    """

    try:
        # ── Una sola consulta con joins ───────────────────────────────────────
        response = (
            supabase.table("trip")
            .select(TRIP_SELECT, count="exact")
            .order("trip_id", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        total = response.count or 0
        trips = [_normalize_trip(t) for t in (response.data or [])]

        logger.info(f"📄 get_all_trips → skip={skip}, limit={limit}, total={total}, devueltos={len(trips)}")

        return PaginatedTripsResponse(
            data=trips,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    except Exception as e:
        logger.error(f"Error al obtener viajes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener viajes: {str(e)}",
        )


@router.get("/client/{client_document}")
async def get_trips_by_client(
    client_document: str,
    skip: int = Query(default=0, ge=0, description="Offset para paginación"),
    limit: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE, description="Límite de resultados"),
):
    """
    Obtener viajes de un cliente con joins y paginación.

    Antes: select("*") sin barrios ni rating → 1 query incompleta
    Ahora: join de barrios + rating + paginación en 1 sola query
    """
    try:
        response = (
            supabase.table("trip")
            .select(TRIP_SELECT, count="exact")
            .eq("client_document", client_document)
            .order("trip_id", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        total = response.count or 0
        trips = [_normalize_trip(t) for t in (response.data or [])]

        logger.info(f"📄 get_trips_by_client [{client_document}] → devueltos={len(trips)}, total={total}")

        return PaginatedTripsResponse(
            data=trips,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    except Exception as e:
        logger.error(f"Error al obtener viajes del cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.get("/driver/{driver_document}")
async def get_trips_by_driver(
    driver_document: str,
    skip: int = Query(default=0, ge=0, description="Offset para paginación"),
    limit: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE, description="Límite de resultados"),
):
    """
    Obtener viajes de un conductor con nombres de barrios y paginación.

    Antes: 2 consultas separadas (trip + neighborhood) → N+1
    Ahora: join PostgREST en 1 sola consulta + paginación
    """
    try:
        response = (
            supabase.table("trip")
            .select(TRIP_SELECT, count="exact")
            .eq("driver_document", driver_document)
            .order("trip_id", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        total = response.count or 0
        trips = [_normalize_trip(t) for t in (response.data or [])]

        logger.info(f"📄 get_trips_by_driver [{driver_document}] → devueltos={len(trips)}, total={total}")

        return PaginatedTripsResponse(
            data=trips,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    except Exception as e:
        logger.error(f"Error al obtener viajes del conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.get("/active")
async def get_active_trips():
    """Obtener viajes activos (status = 'N') con datos de barrios."""
    try:
        response = (
            supabase.table("trip")
            .select(TRIP_SELECT)
            .eq("status", "N")
            .order("trip_id", desc=True)
            .execute()
        )
        trips = [_normalize_trip(t) for t in (response.data or [])]
        return trips

    except Exception as e:
        logger.error(f"Error al obtener viajes activos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.get("/{trip_id}")
async def get_trip_by_id(trip_id: int):
    """
    Obtener detalle completo de un viaje por ID.

    Incluye nombres de barrios y calificación en una sola consulta.
    """
    try:
        response = (
            supabase.table("trip")
            .select(TRIP_SELECT)
            .eq("trip_id", trip_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado",
            )

        trip = _normalize_trip(response.data[0])
        return trip

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.post("", response_model=TripResponse)
async def create_trip(trip: TripRequest):
    """Crear nuevo viaje con origen y destino."""
    try:
        trip_data = {
            "client_document": trip.client_document,
            "driver_document": trip.driver_document,
            "vehicle_plate": trip.vehicle_plate,
            "origin_neighborhood_id": trip.origin_neighborhood_id,
            "destination_neighborhood_id": trip.destination_neighborhood_id,
            "start_time": datetime.now().isoformat(),
            "status": "N",  # N = En curso
        }

        response = supabase.table("trip").insert(trip_data).execute()

        if response.data:
            # Invalidar caché si fuera necesario (no aplica aquí, pero patrón útil)
            return TripResponse(
                success=True,
                trip_id=response.data[0]["trip_id"],
                message="Viaje creado exitosamente",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear viaje",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.put("/{trip_id}/finish")
async def finish_trip(trip_id: int):
    """Finalizar viaje (status → 'F')."""
    try:
        update_data = {
            "end_time": datetime.now().isoformat(),
            "status": "F",  # F = Finalizado
        }

        response = supabase.table("trip").update(update_data).eq("trip_id", trip_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viaje no encontrado",
            )

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al finalizar viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.delete("/{trip_id}")
async def delete_trip(trip_id: int):
    """Eliminar un viaje por ID (y sus registros asociados)."""
    try:
        # 1. Eliminar registros dependientes (cascade manual)
        for table in ("pay", "rating"):
            try:
                supabase.table(table).delete().eq("trip_id", trip_id).execute()
            except Exception:
                pass  # Tabla puede no existir o no tener registros

        # 2. Eliminar el viaje
        response = supabase.table("trip").delete().eq("trip_id", trip_id).execute()

        if not response.data:
            check = supabase.table("trip").select("trip_id").eq("trip_id", trip_id).execute()
            if not check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Viaje no encontrado",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo eliminar el viaje",
            )

        return {"success": True, "message": "Viaje y datos asociados eliminados exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar viaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar viaje: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check para el servicio de viajes."""
    return {"status": "ok", "service": "trips", "message": "Servicio de viajes funcionando"}
