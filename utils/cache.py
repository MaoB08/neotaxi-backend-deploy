# ============================================
# ARCHIVO: utils/cache.py
# Caché en memoria con TTL para datos estáticos
# ============================================
from datetime import datetime, timedelta
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Caché en memoria con tiempo de vida (TTL).
    Principio SRP: solo gestiona el almacenamiento temporal de datos.
    """

    def __init__(self, ttl_minutes: int = 60):
        self._data: Optional[Any] = None
        self._last_updated: Optional[datetime] = None
        self._ttl = timedelta(minutes=ttl_minutes)
        self._name: str = "unnamed"

    def is_valid(self) -> bool:
        """Retorna True si el caché aún es válido."""
        if self._data is None or self._last_updated is None:
            return False
        return datetime.now() - self._last_updated < self._ttl

    def get(self) -> Optional[Any]:
        """Retorna los datos cacheados si son válidos, None en caso contrario."""
        if self.is_valid():
            return self._data
        return None

    def set(self, data: Any) -> None:
        """Almacena nuevos datos y actualiza la marca de tiempo."""
        self._data = data
        self._last_updated = datetime.now()
        logger.debug(f"🗄️  Caché '{self._name}' actualizado con {len(data) if isinstance(data, list) else 1} registros")

    def invalidate(self) -> None:
        """Invalida el caché forzando una recarga en la siguiente petición."""
        self._data = None
        self._last_updated = None
        logger.info(f"🗑️  Caché '{self._name}' invalidado")

    @property
    def last_updated(self) -> Optional[datetime]:
        return self._last_updated


def _make_cache(name: str, ttl_minutes: int) -> TTLCache:
    c = TTLCache(ttl_minutes=ttl_minutes)
    c._name = name
    return c


# ---------------------------------------------------------------------------
# Instancias globales — tablas que raramente cambian
# ---------------------------------------------------------------------------

# Barrios: cambian solo cuando el admin agrega zonas nuevas (TTL 60 min)
neighborhoods_cache: TTLCache = _make_cache("neighborhoods", ttl_minutes=60)

# Tipos de antecedente: catálogo estático (TTL 120 min)
antecedent_types_cache: TTLCache = _make_cache("antecedent_types", ttl_minutes=120)

# Métodos de pago: catálogo estático (TTL 120 min)
payment_methods_cache: TTLCache = _make_cache("payment_methods", ttl_minutes=120)


# ---------------------------------------------------------------------------
# Funciones helper (Principio DRY + OCP: fácil de extender sin modificar)
# ---------------------------------------------------------------------------

def get_or_fetch(cache: TTLCache, fetch_fn):
    """
    Retorna datos del caché si son válidos; de lo contrario, llama a
    `fetch_fn()` para recuperarlos de Supabase y los almacena.

    Args:
        cache:    Instancia de TTLCache a usar.
        fetch_fn: Callable sin argumentos que devuelve la lista de datos.

    Returns:
        Lista de registros (del caché o recién descargados).
    """
    cached = cache.get()
    if cached is not None:
        logger.debug(f"✅ Cache HIT '{cache._name}'")
        return cached

    logger.info(f"🔄 Cache MISS '{cache._name}' — consultando Supabase")
    data = fetch_fn()
    cache.set(data)
    return data
