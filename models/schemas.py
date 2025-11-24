# ============================================
# ARCHIVO: models/schemas.py
# ============================================
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ==================== AUTENTICACIÓN ====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user_type: str  # "CLIENT", "DRIVER", "ADMIN"
    document: str
    email: str
    name: str
    phone: Optional[str] = None
    message: str = "Login exitoso"

class TokenVerificationRequest(BaseModel):
    token: str

class TokenVerificationResponse(BaseModel):
    valid: bool
    document: str
    user_type: str
    email: str

# ==================== REGISTRO ====================

class RegisterClientRequest(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str
    neighborhood_id: Optional[int] = None

class RegisterDriverRequest(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str
    license_number: str

class RegisterResponse(BaseModel):
    success: bool
    message: str
    document: str

# ==================== USUARIOS ====================

class UserBase(BaseModel):
    document: str
    email: EmailStr
    user_type: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    created_at: Optional[datetime] = None

# ==================== CLIENTES ====================

class ClientBase(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    neighborhood_id: Optional[int] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    created_at: Optional[datetime] = None

class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    neighborhood_id: Optional[int] = None

# ==================== CONDUCTORES ====================

class DriverBase(BaseModel):
    document: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    license_number: str
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, SUSPENDED

class DriverCreate(DriverBase):
    pass

class DriverResponse(DriverBase):
    created_at: Optional[datetime] = None

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    status: Optional[str] = None

class DriverApproval(BaseModel):
    status: str  # APPROVED, REJECTED, SUSPENDED

# ==================== VIAJES ====================

class TripCreate(BaseModel):
    client_document: str
    driver_document: str
    origin_neighborhood_id: int
    destination_neighborhood_id: int
    vehicle_id: int

class TripUpdate(BaseModel):
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_price: Optional[float] = None

class TripResponse(BaseModel):
    trip_id: int
    client_document: str
    driver_document: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_price: Optional[float] = None

# ==================== RESPUESTAS GENÉRICAS ====================

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: Optional[str] = None