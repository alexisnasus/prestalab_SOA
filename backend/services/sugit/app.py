from fastapi import FastAPI, HTTPException, Body, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from typing import Optional
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger
from models import Sugerencia, Usuario, get_db

app = FastAPI(title="Servicio de Gestión de Sugerencias")

# Crear logger para este servicio
logger = create_service_logger("sugit")

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://sugit:8000")
    
    await register_service(
        app=app,
        service_name="sugit",
        service_url="http://sugit:8000",
        description="Gestión de sugerencias de usuarios",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio SUGIT disponible"}

# Modelos Pydantic
class SugerenciaCreate(BaseModel):
    usuario_id: int = Field(..., gt=0)
    sugerencia: str = Field(..., min_length=1, max_length=100)

# Registrar sugerencia
@app.post("/sugerencias", status_code=status.HTTP_201_CREATED)
def registrar_sugerencia(sugerencia_data: SugerenciaCreate = Body(...), db: Session = Depends(get_db)):
    logger.request_received("POST", "/sugerencias", sugerencia_data.dict())
    
    try:
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == sugerencia_data.usuario_id).first()
        if not usuario:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Crear nueva sugerencia
        nueva_sugerencia = Sugerencia(
            usuario_id=sugerencia_data.usuario_id,
            sugerencia=sugerencia_data.sugerencia,
            estado='PENDIENTE'
        )
        
        db.add(nueva_sugerencia)
        db.commit()
        db.refresh(nueva_sugerencia)
        
        response_data = {
            "id": nueva_sugerencia.id,
            "message": "Sugerencia registrada"
        }
        
        logger.response_sent(201, "Sugerencia registrada", f"ID: {nueva_sugerencia.id}")
        return response_data
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error registrando sugerencia", str(exc))
        raise HTTPException(status_code=500, detail="Error al registrar sugerencia")

# Listar sugerencias
@app.get("/sugerencias", status_code=status.HTTP_200_OK)
def listar_sugerencias(db: Session = Depends(get_db)):
    logger.request_received("GET", "/sugerencias")
    
    try:
        # Obtener todas las sugerencias usando ORM
        sugerencias = db.query(Sugerencia).all()
        
        # Convertir a diccionarios
        data = [
            {
                "id": s.id,
                "usuario_id": s.usuario_id,
                "sugerencia": s.sugerencia,
                "estado": s.estado,
                "registro_instante": s.registro_instante
            }
            for s in sugerencias
        ]
        
        logger.response_sent(200, "Sugerencias obtenidas", f"Total: {len(data)}")
        return data
        
    except SQLAlchemyError as exc:
        logger.error("Error listando sugerencias", str(exc))
        raise HTTPException(status_code=500, detail="Error al listar sugerencias")

# Aprobar sugerencia
@app.put("/sugerencias/{id}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_sugerencia(id: int, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/sugerencias/{id}/aprobar")
    
    try:
        # Buscar la sugerencia por ID usando ORM
        sugerencia = db.query(Sugerencia).filter(Sugerencia.id == id).first()
        
        if not sugerencia:
            logger.response_sent(404, "Sugerencia no encontrada")
            raise HTTPException(status_code=404, detail="Sugerencia no encontrada")
        
        # Actualizar el estado
        sugerencia.estado = 'ACEPTADA'
        db.commit()
        db.refresh(sugerencia)
        
        response_data = {
            "id": id,
            "message": "Sugerencia aprobada"
        }
        
        logger.response_sent(200, f"Sugerencia {id} aprobada")
        return response_data
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error aprobando sugerencia", str(exc))
        raise HTTPException(status_code=500, detail="Error al aprobar sugerencia")

# Rechazar sugerencia
@app.put("/sugerencias/{id}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_sugerencia(id: int, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/sugerencias/{id}/rechazar")
    
    try:
        # Buscar la sugerencia por ID usando ORM
        sugerencia = db.query(Sugerencia).filter(Sugerencia.id == id).first()
        
        if not sugerencia:
            logger.response_sent(404, "Sugerencia no encontrada")
            raise HTTPException(status_code=404, detail="Sugerencia no encontrada")
        
        # Actualizar el estado
        sugerencia.estado = 'RECHAZADA'
        db.commit()
        db.refresh(sugerencia)
        
        response_data = {
            "id": id,
            "message": "Sugerencia rechazada"
        }
        
        logger.response_sent(200, f"Sugerencia {id} rechazada")
        return response_data
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error rechazando sugerencia", str(exc))
        raise HTTPException(status_code=500, detail="Error al rechazar sugerencia")