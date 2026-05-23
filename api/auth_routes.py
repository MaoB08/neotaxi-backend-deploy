# ============================================
# ARCHIVO: api/auth_routes.py
# ============================================
from fastapi import APIRouter, HTTPException, status
from models.schemas import (
    LoginRequest, LoginResponse,
    RegisterClientRequest, RegisterDriverRequest, RegisterResponse,
    TokenVerificationRequest, TokenVerificationResponse
)
from core.database import supabase
from utils.security import verify_password, hash_password, create_access_token, decode_access_token
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== LOGIN ====================

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Login unificado para CLIENT, DRIVER y ADMIN
    """
    try:
        # Normalizar email
        credentials.email = credentials.email.lower().strip()
        logger.info(f"🔐 Intento de login: {credentials.email}")
        
        # 1. Buscar usuario en tabla USER
        user_response = supabase.table("user").select("*").eq("email", credentials.email).execute()
        
        if not user_response.data:
            logger.warning(f"⚠️ Usuario no encontrado: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        
        user = user_response.data[0]
        
        # 2. Verificar contraseña
        if not verify_password(credentials.password, user["password"]):
            logger.warning(f"⚠️ Contraseña incorrecta: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        
        user_type = user["user_type"]
        
        # 3. Obtener datos según tipo de usuario
        if user_type == "CLIENT":
            details_response = supabase.table("client").select("*").eq("document", user["document"]).execute()
        elif user_type == "DRIVER":
            details_response = supabase.table("driver").select("*").eq("document", user["document"]).execute()
            
            # Verificar que el conductor esté aprobado
            if details_response.data and details_response.data[0].get("status") != "APPROVED":
                logger.warning(f"⚠️ Conductor no aprobado: {user['document']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Su cuenta está pendiente de aprobación por el administrador"
                )
        else:  # ADMIN
            details_response = user_response
        
        if not details_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener datos del usuario"
            )
        
        user_details = details_response.data[0]
        
        # 4. Crear token JWT
        token_data = {
            "document": user["document"],
            "email": user["email"],
            "user_type": user_type
        }
        token = create_access_token(token_data)
        
        # 5. Preparar respuesta
        full_name = f"{user_details.get('first_name', '')} {user_details.get('last_name', '')}".strip()
        if not full_name:
            full_name = "Usuario"
        
        logger.info(f"✅ Login exitoso: {credentials.email} ({user_type})")
        
        return LoginResponse(
            success=True,
            token=token,
            user_type=user_type,
            document=user["document"],
            email=user["email"],
            name=full_name,
            phone=user_details.get("phone")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# ==================== REGISTRO DE CLIENTE ====================

@router.post("/register/client", response_model=RegisterResponse)
def register_client(data: RegisterClientRequest):
    """
    Registrar nuevo cliente
    """
    try:
        # Normalizar email
        data.email = data.email.lower().strip()
        logger.info(f"📝 Registro de cliente: {data.email}")
        
        # 1. Verificar si el email ya existe en USER (tabla maestra) - Case Insensitive
        existing_user = supabase.table("user").select("email").ilike("email", data.email).execute()
        if existing_user.data:
            logger.warning(f"⚠️ Email ya registrado en USER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        # 2. Verificar explícitamente en DRIVER - Case Insensitive
        existing_driver = supabase.table("driver").select("email").ilike("email", data.email).execute()
        if existing_driver.data:
            logger.warning(f"⚠️ Email ya registrado en DRIVER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está asociado a una cuenta de conductor"
            )
            
        # 3. Verificar explícitamente en CLIENT - Case Insensitive
        existing_client = supabase.table("client").select("email").ilike("email", data.email).execute()
        if existing_client.data:
            logger.warning(f"⚠️ Email ya registrado en CLIENT: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # 4. Verificar si el documento ya existe en USER
        existing_doc = supabase.table("user").select("document").eq("document", data.document).execute()
        if existing_doc.data:
            logger.warning(f"⚠️ Documento ya registrado en USER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )

        # 5. Verificar documento explícitamente en DRIVER
        existing_doc_driver = supabase.table("driver").select("document").eq("document", data.document).execute()
        if existing_doc_driver.data:
            logger.warning(f"⚠️ Documento ya registrado en DRIVER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado como conductor"
            )

        # 6. Verificar documento explícitamente en CLIENT
        existing_doc_client = supabase.table("client").select("document").eq("document", data.document).execute()
        if existing_doc_client.data:
            logger.warning(f"⚠️ Documento ya registrado en CLIENT: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )
        
        # 7. Encriptar contraseña
        hashed_pwd = hash_password(data.password)
        
        # 8. Insertar en USER
        user_data = {
            "document": data.document,
            "email": data.email,
            "password": hashed_pwd,
            "user_type": "CLIENT"
        }
        supabase.table("user").insert(user_data).execute()
        
        # 9. Insertar en CLIENT
        client_data = {
            "document": data.document,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "email": data.email,
            "neighborhood_id": data.neighborhood_id
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
def register_driver(data: RegisterDriverRequest):
    """
    Registrar nuevo conductor (estado PENDING)
    """
    try:
        # Normalizar email
        data.email = data.email.lower().strip()
        logger.info(f"📝 Registro de conductor: {data.email}")
        
        # 1. Verificar si el email ya existe en USER - Case Insensitive
        existing_user = supabase.table("user").select("email").ilike("email", data.email).execute()
        if existing_user.data:
            logger.warning(f"⚠️ Email ya registrado en USER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        # 2. Verificar explícitamente en CLIENT - Case Insensitive
        existing_client = supabase.table("client").select("email").ilike("email", data.email).execute()
        if existing_client.data:
            logger.warning(f"⚠️ Email ya registrado en CLIENT: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está asociado a una cuenta de cliente"
            )

        # 3. Verificar explícitamente en DRIVER - Case Insensitive
        existing_driver = supabase.table("driver").select("email").ilike("email", data.email).execute()
        if existing_driver.data:
            logger.warning(f"⚠️ Email ya registrado en DRIVER: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # 4. Verificar si el documento ya existe en USER
        existing_doc = supabase.table("user").select("document").eq("document", data.document).execute()
        if existing_doc.data:
            logger.warning(f"⚠️ Documento ya registrado en USER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )

        # 5. Verificar documento explícitamente en CLIENT
        existing_doc_client = supabase.table("client").select("document").eq("document", data.document).execute()
        if existing_doc_client.data:
            logger.warning(f"⚠️ Documento ya registrado en CLIENT: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está asociado a una cuenta de cliente"
            )

        # 6. Verificar documento explícitamente en DRIVER
        existing_doc_driver = supabase.table("driver").select("document").eq("document", data.document).execute()
        if existing_doc_driver.data:
            logger.warning(f"⚠️ Documento ya registrado en DRIVER: {data.document}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado"
            )
        
        # 7. Encriptar contraseña
        hashed_pwd = hash_password(data.password)
        
        # 8. Insertar en USER
        user_data = {
            "document": data.document,
            "email": data.email,
            "password": hashed_pwd,
            "user_type": "DRIVER"
        }
        supabase.table("user").insert(user_data).execute()
        
        # 9. Insertar en DRIVER con estado PENDING
        driver_data = {
            "document": data.document,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "email": data.email,
            "license_number": data.license_number,
            "status": "PENDING"
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

@router.post("/verify-token", response_model=TokenVerificationResponse)
def verify_token(request: TokenVerificationRequest):
    """
    Verificar si un token JWT es válido
    """
    try:
        payload = decode_access_token(request.token)
        
        return TokenVerificationResponse(
            valid=True,
            document=payload["document"],
            user_type=payload["user_type"],
            email=payload["email"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# ==================== HEALTH CHECK ====================

@router.get("/health")
def health_check():
    """Verificar que el servicio de autenticación está funcionando"""
    return {
        "status": "ok",
        "service": "auth",
        "message": "Servicio de autenticación funcionando correctamente"
    }