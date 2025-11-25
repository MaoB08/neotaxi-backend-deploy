# ============================================
# ARCHIVO: main.py
# ============================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configuración
from core.config import settings

# Routers
from api import auth_routes_adapted as auth_routes
from api import client_routes, driver_routes, trip_routes, additional_routes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API REST para NeoTaxi - Sistema de transporte con seguridad biométrica",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    auth_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["🔐 Autenticación"]
)

app.include_router(
    client_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/clients",
    tags=["👥 Clientes"]
)

app.include_router(
    driver_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/drivers",
    tags=["🚗 Conductores"]
)

app.include_router(
    trip_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/trips",
    tags=["🚕 Viajes"]
)

app.include_router(
    additional_routes.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["📊 Datos Generales"]
)

# Endpoints raíz
@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Bienvenido a NeoTaxi API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "clients": f"{settings.API_V1_PREFIX}/clients",
            "drivers": f"{settings.API_V1_PREFIX}/drivers"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NeoTaxi API",
        "version": "1.0.0"
    }

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Error interno del servidor",
            "error": str(exc) if settings.DEBUG else "Error interno"
        }
    )

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.PROJECT_NAME} iniciado")
    logger.info(f"📡 Supabase URL: {settings.SUPABASE_URL[:30]}...")
    logger.info(f"🔑 JWT configurado: ✅")
    logger.info(f"📝 Documentación: http://localhost:8000/docs")
    logger.info("=" * 60)

# Evento de cierre
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Servidor detenido")

# Ejecutar servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )