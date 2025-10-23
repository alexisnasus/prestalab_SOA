from fastapi import FastAPI, HTTPException, Body, Path, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from datetime import datetime
import os
import sys
sys.path.append('/app')
from bus_client import register_service
from service_logger import create_service_logger
from models import get_db, Notificacion, Usuario

app = FastAPI(title="Servicio de Gestión de Notificaciones (NOTIS)")

logger = create_service_logger("notis")

class NotificacionCreate(BaseModel):
    usuario_id: int
    canal: int
    tipo: str
    mensaje: str

class PreferenciasUpdate(BaseModel):
    preferencias_notificacion: int

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://notis:8000")
    
    await register_service(
        app=app,
        service_name="notis",
        service_url="http://notis:8000",
        description="Gestión de notificaciones multicanal",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

@app.get("/")
def root():
    return {"message": "Servicio NOTIS disponible"}

@app.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def crear_notificacion(notificacion: NotificacionCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/notificaciones", notificacion.dict())
    
    nueva_notificacion = Notificacion(
        usuario_id=notificacion.usuario_id,
        canal=notificacion.canal,
        tipo=notificacion.tipo,
        mensaje=notificacion.mensaje,
        registro_instante=datetime.now()
    )
    
    try:
        db.add(nueva_notificacion)
        db.commit()
        db.refresh(nueva_notificacion)
        
        response_data = {"id": nueva_notificacion.id, "message": "Notificación registrada correctamente"}
        logger.response_sent(201, "Notificación creada", f"ID: {nueva_notificacion.id}")
        return response_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        if "foreign key constraint fails" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"El usuario con ID {notificacion.usuario_id} no existe.")
        raise HTTPException(status_code=500, detail="Error al registrar la notificación.")

@app.get("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def obtener_preferencias(usuario_id: int = Path(..., description="ID del usuario"), db: Session = Depends(get_db)):
    logger.request_received("GET", f"/preferencias/{usuario_id}")
    
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        response_data = {
            "usuario_id": usuario_id,
            "preferencias_notificacion": usuario.preferencias_notificacion
        }
        logger.response_sent(200, "Preferencias obtenidas", f"Usuario: {usuario_id}")
        return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al consultar las preferencias.")

@app.put("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def actualizar_preferencias(usuario_id: int, preferencias: PreferenciasUpdate, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/preferencias/{usuario_id}", preferencias.dict())

    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

        if not usuario:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        usuario.preferencias_notificacion = preferencias.preferencias_notificacion
        db.commit()

        return {
            "message": f"Preferencias de notificación del usuario {usuario_id} actualizadas correctamente"
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al actualizar las preferencias.")