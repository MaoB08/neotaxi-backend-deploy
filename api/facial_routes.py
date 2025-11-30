# api/facial_routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import numpy as np
import json
from io import BytesIO
from PIL import Image
import tempfile
import os

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️ DeepFace no disponible - instala con: pip install deepface")

from core.database import supabase

router = APIRouter(prefix="/facial", tags=["Facial Recognition - Clients"])

SIMILARITY_THRESHOLD = 0.4


@router.get("/test")
async def test_facial():
    """Endpoint de prueba"""
    return {
        "success": True,
        "message": "Módulo facial funcionando",
        "deepface_available": DEEPFACE_AVAILABLE
    }


@router.post("/register")
async def register_client_face(
    client_document: str = Form(...),
    image: UploadFile = File(...)
):
    """Registra el vector facial de un cliente"""
    
    if not DEEPFACE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="DeepFace no está instalado. Ejecuta: pip install deepface"
        )
    
    try:
        print(f"📸 Registrando rostro para cliente: {client_document}")
        
        # Validar cliente
        client_check = supabase.table("client").select("document").eq(
            "document", client_document
        ).execute()
        
        if not client_check.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Guardar imagen temporalmente
        contents = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Extraer embedding
            embeddings = DeepFace.represent(
                img_path=tmp_path,
                model_name="Facenet512",
                enforce_detection=True,
                detector_backend="opencv"
            )
            
            if not embeddings:
                raise HTTPException(status_code=400, detail="No se detectó rostro")
            
            encoding_json = json.dumps(embeddings[0]["embedding"])
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        # Guardar en BD
        existing = supabase.table("facial_encodings").select("id").eq(
            "client_document", client_document
        ).eq("is_active", True).execute()
        
        if existing.data:
            supabase.table("facial_encodings").update({
                "encoding": encoding_json,
                "updated_at": "now()"
            }).eq("client_document", client_document).eq("is_active", True).execute()
            action = "updated"
        else:
            supabase.table("facial_encodings").insert({
                "client_document": client_document,
                "encoding": encoding_json,
                "is_active": True
            }).execute()
            action = "created"
        
        return {
            "success": True,
            "message": f"Rostro {action}",
            "action": action,
            "client_document": client_document
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_client_face(
    client_document: str = Form(...),
    image: UploadFile = File(...),
    trip_id: int = Form(None)
):
    """Verifica el rostro de un cliente"""
    
    if not DEEPFACE_AVAILABLE:
        raise HTTPException(status_code=500, detail="DeepFace no disponible")
    
    try:
        # Guardar imagen
        contents = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            embeddings = DeepFace.represent(
                img_path=tmp_path,
                model_name="Facenet512",
                enforce_detection=True,
                detector_backend="opencv"
            )
            
            if not embeddings:
                supabase.table("biometric_record").insert({
                    "client_document": client_document,
                    "verification_result": "N",
                    "confidence": 0.0,
                    "trip_id": trip_id
                }).execute()
                raise HTTPException(status_code=400, detail="No se detectó rostro")
            
            captured_embedding = np.array(embeddings[0]["embedding"])
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        # Obtener encoding registrado
        result = supabase.table("facial_encodings").select("encoding").eq(
            "client_document", client_document
        ).eq("is_active", True).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No hay registro facial")
        
        stored_embedding = np.array(json.loads(result.data[0]["encoding"]))
        distance = float(np.linalg.norm(stored_embedding - captured_embedding))
        confidence = max(0, min(100, (1 - (distance / 10)) * 100))
        is_match = distance <= SIMILARITY_THRESHOLD
        
        # Guardar en biometric_record
        supabase.table("biometric_record").insert({
            "client_document": client_document,
            "verification_result": "Y" if is_match else "N",
            "confidence": round(confidence, 2),
            "distance": round(distance, 4),
            "trip_id": trip_id
        }).execute()
        
        return {
            "success": True,
            "is_match": is_match,
            "confidence": round(confidence, 2),
            "distance": round(distance, 4),
            "message": "Verificación exitosa ✓" if is_match else "Rostro no coincide ✗"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{client_document}")
async def check_registration(client_document: str):
    """Verifica si tiene registro"""
    try:
        result = supabase.table("facial_encodings").select("*").eq(
            "client_document", client_document
        ).eq("is_active", True).execute()
        
        if not result.data:
            return {"success": True, "has_registration": False}
        
        stats = supabase.table("biometric_record").select("verification_result").eq(
            "client_document", client_document
        ).execute()
        
        successful = sum(1 for r in stats.data if r["verification_result"] == "Y")
        failed = sum(1 for r in stats.data if r["verification_result"] == "N")
        
        return {
            "success": True,
            "has_registration": True,
            "registered_at": result.data[0]["registered_at"],
            "stats": {
                "successful": successful,
                "failed": failed,
                "total": len(stats.data),
                "success_rate": round((successful / len(stats.data) * 100), 2) if stats.data else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))