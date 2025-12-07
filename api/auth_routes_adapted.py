# ============================================
# ARCHIVO: api/auth_routes_adapted.py
# ============================================
# Adaptado a la estructura de BD existente (CLIENT y DRIVER sin tabla USER)

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from core.database import supabase
from utils.security import verify_password, hash_password, create_access_token, decode_access_token
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== MODELOS ====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user_type: str  # "client", "driver" o "user"
    document: str
    email: str
    name: str
    phone: str | None = None
    message: str = "Login exitoso"

class RegisterClientRequest(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str

class RegisterDriverRequest(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str = None
    license: str
    years_experience: int = 0

class RegisterResponse(BaseModel):
    success: bool
    message: str
    document: str

# ==================== LOGIN ====================

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login para CLIENT, DRIVER o USER (admin)
    """
    try:
        # Normalizar email
        credentials.email = credentials.email.lower().strip()
        logger.info(f"🔐 Intento de login: {credentials.email}")
        
        # 1. Buscar en CLIENT (Case Insensitive)
        client_response = supabase.table("client").select("*").ilike("email", credentials.email).execute()
        
        if client_response.data:
            client = client_response.data[0]
            
            # Verificar contraseña
            if not verify_password(credentials.password, client["password"]):
                logger.warning(f"⚠️ Contraseña incorrecta (CLIENT): {credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos"
                )
            
            # Crear token
            token_data = {
                "document": client["document"],
                "email": client["email"],
                "user_type": "client"
            }
            token = create_access_token(token_data)
            
            logger.info(f"✅ Login exitoso (CLIENT): {client['email']}")
            
            return LoginResponse(
                success=True,
                token=token,
                user_type="client",
                document=client["document"],
                email=client["email"],
                name=f"{client['first_name']} {client['last_name']}",
                phone=client.get("phone"),
                message="Bienvenido"
            )
        
        # 2. Buscar en DRIVER (Case Insensitive)
        driver_response = supabase.table("driver").select("*").ilike("email", credentials.email).execute()
        
        if driver_response.data:
            driver = driver_response.data[0]
            
            # Verificar contraseña
            if not verify_password(credentials.password, driver["password"]):
                logger.warning(f"⚠️ Contraseña incorrecta (DRIVER): {credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos"
                )
            
            # Verificar estado del conductor
            if driver["status"] != 'A':  # 'A' = Aprobado
                status_messages = {
                    'P': "Tu cuenta está pendiente de aprobación",
                    'I': "Tu cuenta está inactiva"
                }
                logger.warning(f"⚠️ Conductor no aprobado: {driver['document']} - Estado: {driver['status']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=status_messages.get(driver['status'], "Tu cuenta no está activa")
                )
            
            # Crear token
            token_data = {
                "document": driver["document"],
                "email": driver["email"],
                "user_type": "driver"
            }
            token = create_access_token(token_data)
            
            logger.info(f"✅ Login exitoso (DRIVER): {driver['email']}")
            
            return LoginResponse(
                success=True,
                token=token,
                user_type="driver",
                document=driver["document"],
                email=driver["email"],
                name=f"{driver['first_name']} {driver['last_name']}",
                phone=None,  # DRIVER no tiene phone en tu BD
                message="Bienvenido"
            )
        
        # 3. Buscar en USER (admin) - Case Insensitive
        user_response = supabase.table("user").select("*").ilike("email", credentials.email).execute()
        
        if user_response.data:
            user = user_response.data[0]
            
            # Verificar contraseña
            if not verify_password(credentials.password, user["password"]):
                logger.warning(f"⚠️ Contraseña incorrecta (USER): {credentials.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos"
                )
            
            # ⚠️ IMPORTANTE: Los usuarios admin solo pueden acceder desde el panel web
            logger.warning(f"⚠️ Intento de login de admin desde app móvil: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los administradores solo pueden acceder desde el panel web. Por favor, use http://localhost:8000/login.html"
            )
        
        # 4. No encontrado en ninguna tabla
        logger.warning(f"⚠️ Usuario no encontrado: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# ==================== LOGIN ADMIN (PANEL WEB) ====================

@router.post("/login-admin", response_model=LoginResponse)
async def login_admin(credentials: LoginRequest):
    """
    Login exclusivo para administradores desde el panel web
    """
    try:
        # Normalizar email
        credentials.email = credentials.email.lower().strip()
        logger.info(f"🔐 Intento de login ADMIN: {credentials.email}")
        
        # Buscar en USER (admin) - Case Insensitive
        user_response = supabase.table("user").select("*").ilike("email", credentials.email).execute()
        
        if not user_response.data:
            logger.warning(f"⚠️ Usuario admin no encontrado: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        
        user = user_response.data[0]
        
        # Verificar contraseña
        if not verify_password(credentials.password, user["password"]):
            logger.warning(f"⚠️ Contraseña incorrecta (ADMIN): {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        
        # Para usuarios admin, usar email como identificador si no hay documento
        user_document = user.get("document", user["email"])
        
        # Crear token
        token_data = {
            "document": user_document,
            "email": user["email"],
            "user_type": "user"
        }
        token = create_access_token(token_data)
        
        logger.info(f"✅ Login ADMIN exitoso: {user['email']}")
        
        # Para usuarios admin, construir nombre desde los campos disponibles
        full_name = "Administrador"
        if "first_name" in user and "last_name" in user:
            full_name = f"{user['first_name']} {user['last_name']}"
        elif "name" in user:
            full_name = user["name"]
        
        return LoginResponse(
            success=True,
            token=token,
            user_type="user",
            document=user_document,
            email=user["email"],
            name=full_name,
            phone=user.get("phone"),
            message="Bienvenido Administrador"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en login admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# ==================== REGISTRO DE CLIENTE ====================

@router.post("/register/client", response_model=RegisterResponse)
async def register_client(data: RegisterClientRequest):
    """
    Registrar nuevo cliente
    """
    try:
        # Normalizar email
        data.email = data.email.lower().strip()
        logger.info(f"📝 Registro de cliente: {data.email}")
        
        # 1. Verificar si el email ya existe en USER (Case Insensitive)
        existing_user_email = supabase.table("user").select("email").ilike("email", data.email).execute()
        if existing_user_email.data:
            logger.warning(f"⚠️ Email ya registrado en USER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado en el sistema"
            )
        
        # 2. Verificar si el email ya existe en CLIENT (Case Insensitive)
        existing_client = supabase.table("client").select("email").ilike("email", data.email).execute()
        if existing_client.data:
            logger.warning(f"⚠️ Email ya registrado en CLIENT: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        # 3. Verificar si el email ya existe en DRIVER (Case Insensitive)
        existing_driver = supabase.table("driver").select("email").ilike("email", data.email).execute()
        if existing_driver.data:
            logger.warning(f"⚠️ Email ya registrado en DRIVER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está asociado a una cuenta de conductor"
            )
        
        # 4. Verificar si el documento ya existe en CLIENT
        existing_doc_client = supabase.table("client").select("document").eq("document", data.document).execute()
        if existing_doc_client.data:
            logger.warning(f"⚠️ Documento ya registrado en CLIENT: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )

        # 5. Verificar si el documento ya existe en DRIVER
        existing_doc_driver = supabase.table("driver").select("document").eq("document", data.document).execute()
        if existing_doc_driver.data:
            logger.warning(f"⚠️ Documento ya registrado en DRIVER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado como conductor"
            )
        
        # 6. Encriptar contraseña
        hashed_pwd = hash_password(data.password)
        
        # 7. Insertar en CLIENT
        client_data = {
            "document": data.document,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email": data.email,
            "password": hashed_pwd,
            "phone": data.phone
        }
        supabase.table("client").insert(client_data).execute()
        
        logger.info(f"✅ Cliente registrado: {data.email}")
        
        return RegisterResponse(
            success=True,
            message="Cliente registrado exitosamente",
            document=data.document
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al registrar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar cliente: {str(e)}"
        )

# ==================== REGISTRO DE CONDUCTOR ====================

@router.post("/register/driver", response_model=RegisterResponse)
async def register_driver(data: RegisterDriverRequest):
    """
    Registrar nuevo conductor (estado PENDING 'P')
    """
    try:
        # Normalizar email
        data.email = data.email.lower().strip()
        logger.info(f"📝 Registro de conductor: {data.email}")
        
        # 1. Verificar si el email ya existe en USER (Case Insensitive)
        existing_user_email = supabase.table("user").select("email").ilike("email", data.email).execute()
        if existing_user_email.data:
            logger.warning(f"⚠️ Email ya registrado en USER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado en el sistema"
            )
        
        # 2. Verificar si el email ya existe en DRIVER (Case Insensitive)
        existing_driver = supabase.table("driver").select("email").ilike("email", data.email).execute()
        if existing_driver.data:
            logger.warning(f"⚠️ Email ya registrado en DRIVER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        # 3. Verificar si el email ya existe en CLIENT (Case Insensitive)
        existing_client = supabase.table("client").select("email").ilike("email", data.email).execute()
        if existing_client.data:
            logger.warning(f"⚠️ Email ya registrado en CLIENT: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está asociado a una cuenta de cliente"
            )
        
        # 4. Verificar si el documento ya existe en DRIVER
        existing_doc_driver = supabase.table("driver").select("document").eq("document", data.document).execute()
        if existing_doc_driver.data:
            logger.warning(f"⚠️ Documento ya registrado en DRIVER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )

        # 5. Verificar si el documento ya existe en CLIENT
        existing_doc_client = supabase.table("client").select("document").eq("document", data.document).execute()
        if existing_doc_client.data:
            logger.warning(f"⚠️ Documento ya registrado en CLIENT: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está asociado a una cuenta de cliente"
            )
        
        # 6. Encriptar contraseña
        hashed_pwd = hash_password(data.password)
        
        # 7. Insertar en DRIVER con estado PENDING
        driver_data = {
            "document": data.document,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "license": data.license,
            "years_experience": data.years_experience,
            "email": data.email,
            "password": hashed_pwd,
            "status": "P"  # P = Pendiente
        }
        supabase.table("driver").insert(driver_data).execute()
        
        logger.info(f"✅ Conductor registrado (PENDING): {data.email}")
        
        return RegisterResponse(
            success=True,
            message="Conductor registrado. Esperando aprobación del administrador.",
            document=data.document
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al registrar conductor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar conductor: {str(e)}"
        )

# ==================== VERIFICAR TOKEN ====================

@router.post("/verify-token")
async def verify_token(token: str):
    """
    Verificar si un token JWT es válido
    """
    try:
        payload = decode_access_token(token)
        return {
            "valid": True,
            "document": payload["document"],
            "user_type": payload["user_type"],
            "email": payload["email"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Verificar que el servicio está funcionando"""
    return {
        "status": "ok",
        "service": "auth (adapted)",
        "message": "Servicio de autenticación funcionando correctamente"
    }