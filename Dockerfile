# ============================================
# Dockerfile — NeoTaxi Backend
# ============================================

# Imagen base con Python 3.11 slim (más ligera)
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema necesarias para OpenCV y DeepFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha el caché de Docker)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Pre-descargar el modelo Facenet512 durante el build
# (evita descarga en el primer request, que puede causar timeout)
RUN python -c "\
import os; \
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'; \
from deepface import DeepFace; \
DeepFace.build_model('Facenet512'); \
print('✅ Modelo Facenet512 descargado correctamente')" || \
    echo "⚠️ Pre-descarga del modelo omitida"

# Copiar el resto del código
COPY . .

# Puerto que expone la aplicación
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
