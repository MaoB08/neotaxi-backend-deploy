# ============================================
# ARCHIVO: core/config.py
# ============================================
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configuración general de la aplicación"""
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # API
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "NeoTaxi API")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://10.0.2.2:8000",  # Emulador Android
        "*"  # En producción, especificar dominios exactos
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Validar que Supabase esté configurado
if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
    raise ValueError(
        "❌ ERROR: SUPABASE_URL y SUPABASE_KEY deben estar configurados en el archivo .env"
    )

print(f"✅ Configuración cargada correctamente")
print(f"📡 Supabase URL: {settings.SUPABASE_URL[:30]}...")
print(f"🔑 JWT Secret configurado: {'Sí' if settings.JWT_SECRET_KEY else 'No'}")