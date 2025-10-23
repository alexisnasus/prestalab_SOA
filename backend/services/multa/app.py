from fastapi import FastAPI, HTTPException, Body, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import os
import sys
from datetime import datetime

sys.path.append('/app')
from bus_client import register_service
from service_logger import create_service_logger
from models import get_db, Multa, Prestamo, Solicitud, Usuario

app = FastAPI(title="Servicio de Gestión de Multas")

logger = create_service_logger("multa")

class MultaCreate(BaseModel):
    prestamo_id: int
    motivo: str
    valor: float
    estado: str

class EstadoUpdate(BaseModel):
    estado: str

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://multa:8000")
    
    await register_service(
        app=app,
        service_name="multa",
        service_url="http://multa:8000",
        description="Gestión de multas y bloqueos de usuarios",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

@app.get("/")
def root():
    return {"message": "Servicio MULTA disponible"}

@app.get("/usuarios/{id}/multas")
def get_multas_usuario(id: int, db: Session = Depends(get_db)):
    logger.request_received("GET", f"/usuarios/{id}/multas")
    
    try:
        multas = (
            db.query(Multa)
            .join(Prestamo)
            .join(Solicitud)
            .filter(Solicitud.usuario_id == id)
            .all()
        )
        
        resultado = [
            {
                "id": m.id,
                "prestamo_id": m.prestamo_id,
                "motivo": m.motivo,
                "valor": m.valor,
                "estado": m.estado,
                "registro_instante": m.registro_instante.isoformat()
            } for m in multas
        ]
        
        response_data = {"usuario_id": id, "multas": resultado}
        logger.response_sent(200, f"Multas del usuario {id}", f"Total: {len(resultado)}")
        return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al consultar las multas.")

@app.post("/multas", status_code=status.HTTP_201_CREATED)
def crear_multa(multa: MultaCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/multas", multa.dict())
    
    nueva_multa = Multa(
        prestamo_id=multa.prestamo_id,
        motivo=multa.motivo,
        valor=multa.valor,
        estado=multa.estado,
        registro_instante=datetime.now()
    )
    
    try:
        db.add(nueva_multa)
        db.commit()
        db.refresh(nueva_multa)
        
        response_data = {"id": nueva_multa.id, "message": "Multa registrada con éxito"}
        logger.response_sent(201, "Multa registrada", f"ID: {nueva_multa.id}")
        return response_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        if "foreign key constraint fails" in str(e).lower():
            prestamo = db.query(Prestamo).filter(Prestamo.id == multa.prestamo_id).first()
            if not prestamo:
                raise HTTPException(status_code=404, detail=f"El préstamo con ID {multa.prestamo_id} no existe.")
        raise HTTPException(status_code=500, detail="Error al registrar la multa.")

@app.put("/usuarios/{id}/estado")
def actualizar_bloqueo(id: int, data: EstadoUpdate, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/usuarios/{id}/estado", data.dict())
    
    try:
        usuario = db.query(Usuario).filter(Usuario.id == id).first()
        
        if not usuario:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        usuario.estado = data.estado
        db.commit()
        
        response_data = {"message": f"Estado del usuario modificado correctamente a {data.estado}"}
        logger.response_sent(200, f"Estado actualizado a {data.estado}", f"Usuario: {id}")
        return response_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al actualizar el estado del usuario.")
