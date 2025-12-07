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

router = APIRouter(tags=["Facial Recognition"])

# Threshold de similitud (distancia euclidiana máxima permitida)
# Basado en pruebas con emulador:
# - Misma persona: ~1.7
# - Persona diferente: ~7.9
# Threshold óptimo: 2.5 (permite misma persona, rechaza diferentes)
SIMILARITY_THRESHOLD = 4.5


@router.get("/test")
async def test_facial():
    """Endpoint de prueba"""
    return {
        "success": True,
        "message": "Módulo facial funcionando",
        "deepface_available": DEEPFACE_AVAILABLE
    }


@router.post("/register")
async def register_user_face(
    user_document: str = Form(...),
    user_type: str = Form(...),
    image: UploadFile = File(...)
):
    """Registra el vector facial de un cliente o conductor"""
    
    if not DEEPFACE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="DeepFace no está instalado. Ejecuta: pip install deepface"
        )
    
    try:
        # Validar user_type
        if user_type not in ['client', 'driver']:
            raise HTTPException(
                status_code=400, 
                detail="user_type debe ser 'client' o 'driver'"
            )
        
        print(f"📸 Registrando rostro para {user_type}: {user_document}")
        
        # Validar que el usuario exista en la tabla correspondiente
        table_name = "client" if user_type == "client" else "driver"
        user_check = supabase.table(table_name).select("document").eq(
            "document", user_document
        ).execute()
        
        if not user_check.data:
            raise HTTPException(
                status_code=404, 
                detail=f"{user_type.capitalize()} no encontrado"
            )
        
        # Guardar imagen temporalmente
        contents = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Extraer múltiples embeddings (DeepFace puede detectar múltiples rostros)
            # Usamos max_faces para intentar obtener múltiples detecciones del mismo rostro
            embeddings = DeepFace.represent(
                img_path=tmp_path,
                model_name="Facenet512",
                enforce_detection=False,
                detector_backend="opencv"
            )
            
            if not embeddings:
                raise HTTPException(status_code=400, detail="No se detectó rostro")
            
            # Si hay múltiples detecciones, promediar los embeddings
            if len(embeddings) > 1:
                print(f"📸 Detectados {len(embeddings)} rostros, promediando...")
                # Convertir a numpy arrays
                emb_arrays = [np.array(e["embedding"]) for e in embeddings[:3]]  # Max 3
                # Promediar
                avg_embedding = np.mean(emb_arrays, axis=0).tolist()
                encoding_json = json.dumps(avg_embedding)
            else:
                # Solo un embedding
                encoding_json = json.dumps(embeddings[0]["embedding"])
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        # Guardar en BD
        existing = supabase.table("facial_encodings").select("id").eq(
            "user_document", user_document
        ).eq("user_type", user_type).eq("is_active", True).execute()
        
        if existing.data:
            supabase.table("facial_encodings").update({
                "encoding": encoding_json,
                "updated_at": "now()"
            }).eq("user_document", user_document).eq(
                "user_type", user_type
            ).eq("is_active", True).execute()
            action = "updated"
        else:
            supabase.table("facial_encodings").insert({
                "user_document": user_document,
                "user_type": user_type,
                "encoding": encoding_json,
                "is_active": True
            }).execute()
            action = "created"
        
        return {
            "success": True,
            "message": f"Rostro {action}",
            "action": action,
            "user_document": user_document,
            "user_type": user_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_user_face(
    user_document: str = Form(...),
    user_type: str = Form("client"),
    image: UploadFile = File(...),
    trip_id: int = Form(None)
):
    """Verifica el rostro de un cliente o conductor"""
    
    if not DEEPFACE_AVAILABLE:
        raise HTTPException(status_code=500, detail="DeepFace no disponible")
    
    try:
        # Validar user_type
        if user_type not in ['client', 'driver']:
            raise HTTPException(
                status_code=400, 
                detail="user_type debe ser 'client' o 'driver'"
            )
        
        print(f"🔍 Verificando rostro para {user_type}: {user_document}")
        
        # Guardar imagen
        contents = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Extraer múltiples embeddings
            embeddings = DeepFace.represent(
                img_path=tmp_path,
                model_name="Facenet512",
                enforce_detection=False,
                detector_backend="opencv"
            )
            
            if not embeddings:
                # Solo guardar en biometric_record si es cliente
                if user_type == "client":
                    supabase.table("biometric_record").insert({
                        "client_document": user_document,
                        "verification_result": "N"
                    }).execute()
                raise HTTPException(status_code=400, detail="No se detectó rostro")
            
            # Promediar embeddings si hay múltiples
            if len(embeddings) > 1:
                print(f"📸 Detectados {len(embeddings)} rostros en verificación, promediando...")
                emb_arrays = [np.array(e["embedding"]) for e in embeddings[:3]]
                captured_embedding = np.mean(emb_arrays, axis=0)
            else:
                captured_embedding = np.array(embeddings[0]["embedding"])
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        # Obtener encoding registrado
        result = supabase.table("facial_encodings").select("encoding").eq(
            "user_document", user_document
        ).eq("user_type", user_type).eq("is_active", True).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No hay registro facial")
        
        stored_embedding = np.array(json.loads(result.data[0]["encoding"]))
        distance = float(np.linalg.norm(stored_embedding - captured_embedding))
        confidence = max(0, min(100, (1 - (distance / 10)) * 100))
        is_match = distance <= SIMILARITY_THRESHOLD
        
        # DEBUG: Mostrar valores para diagnóstico
        print(f"🔍 DEBUG - Distance: {distance:.4f}, Threshold: {SIMILARITY_THRESHOLD}, Confidence: {confidence:.2f}%, Match: {is_match}")
        
        # Guardar en biometric_record solo si es cliente
        if user_type == "client":
            supabase.table("biometric_record").insert({
                "client_document": user_document,
                "verification_result": "Y" if is_match else "N"
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


@router.get("/check/{user_document}")
async def check_registration(user_document: str, user_type: str = "client"):
    """Verifica si tiene registro facial"""
    try:
        # Validar user_type
        if user_type not in ['client', 'driver']:
            raise HTTPException(
                status_code=400, 
                detail="user_type debe ser 'client' o 'driver'"
            )
        
        result = supabase.table("facial_encodings").select("*").eq(
            "user_document", user_document
        ).eq("user_type", user_type).eq("is_active", True).execute()
        
        if not result.data:
            return {"success": True, "has_registration": False}
        
        # Stats solo para clientes (por ahora)
        if user_type == "client":
            stats = supabase.table("biometric_record").select("verification_result").eq(
                "client_document", user_document
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
        else:
            # Para conductores, solo confirmar registro
            return {
                "success": True,
                "has_registration": True,
                "registered_at": result.data[0]["registered_at"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
