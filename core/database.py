# ============================================
# ARCHIVO: core/database.py
# ============================================
from supabase import create_client, Client
from core.config import settings

# Crear cliente de Supabase directamente
print("🔄 Inicializando cliente de Supabase...")

try:
    supabase: Client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY
    )
    print("✅ Cliente de Supabase inicializado correctamente")
    
    # Probar conexión con tabla CLIENT (adaptado a tu BD)
    try:
        test = supabase.table("client").select("document").limit(1).execute()
        print("✅ Conexión con Supabase exitosa")
    except Exception as test_error:
        print(f"⚠️ Advertencia al probar conexión: {str(test_error)}")
        print("ℹ️ La API funcionará, pero verifica tus credenciales de Supabase")
        
except Exception as e:
    print(f"❌ Error crítico al inicializar Supabase: {str(e)}")
    print("⚠️ Verifica tu archivo .env y las credenciales de Supabase")
    raise