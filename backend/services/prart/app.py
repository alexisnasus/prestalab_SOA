from fastapi import FastAPI, HTTPException, Query, Path, Body, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import os
from datetime import datetime, timedelta
from typing import Optional, List
import sys
from pydantic import BaseModel, Field

sys.path.append('/app')
from bus_client import register_service
from service_logger import create_service_logger
from models import (
    get_db, Item, Usuario, Solicitud, ItemSolicitud, Prestamo, Ventana, ItemExistencia
)

app = FastAPI(title="Servicio de gestión de Préstamos & Artículos")
logger = create_service_logger("prart")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReservaCreate(BaseModel):
    solicitud_id: int
    item_existencia_id: int
    inicio: datetime
    fin: datetime

class SolicitudCreate(BaseModel):
    usuario_id: Optional[int] = Field(default=None, description="ID del usuario solicitante")
    correo: Optional[str] = Field(default=None, description="Correo del usuario solicitante")
    tipo: str = Field(..., min_length=1, description="Tipo de solicitud")

class PrestamoCreate(BaseModel):
    solicitud_id: int
    item_existencia_id: int
    comentario: Optional[str] = None

class DevolucionCreate(BaseModel):
    prestamo_id: int
    comentario: Optional[str] = None

class EstadoUpdate(BaseModel):
    estado: str

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

@app.on_event("startup")
async def startup():
    logger.startup("http://prart:8000")
    await register_service(
        app=app,
        service_name="prart",
        service_url="http://prart:8000",
        description="Gestión de préstamos y artículos del catálogo",
        version="1.0.0"
    )
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio PRART disponible"}

@app.get("/items/all", status_code=status.HTTP_200_OK)
def obtener_todos_los_items(db: Session = Depends(get_db)):
    """Obtiene todos los artículos del catálogo sin filtros"""
    logger.request_received("GET", "/items/all", {})
    try:
        items = db.query(Item).order_by(Item.nombre).all()
        logger.response_sent(200, "Todos los items obtenidos", f"Total: {len(items)}")
        return items
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al obtener items.")

@app.get("/items", status_code=status.HTTP_200_OK)
def buscar_items(
    nombre: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    logger.request_received("GET", "/items", {"nombre": nombre, "tipo": tipo})
    try:
        query = db.query(Item)
        if nombre:
            query = query.filter(Item.nombre.like(f"%{nombre}%"))
        if tipo:
            query = query.filter(Item.tipo == tipo)
        
        items = query.all()
        logger.response_sent(200, "Items obtenidos", f"Total: {len(items)}")
        return items
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al buscar items.")

@app.post("/reservas", status_code=status.HTTP_201_CREATED)
def crear_reserva(reserva: ReservaCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/reservas", reserva.dict())
    if reserva.fin <= reserva.inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser mayor a la fecha de inicio")

    try:
        nueva_reserva = Ventana(**reserva.dict())
        db.add(nueva_reserva)
        db.commit()
        logger.response_sent(201, "Reserva creada", f"Solicitud ID: {reserva.solicitud_id}")
        return {"message": "Reserva creada exitosamente"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al crear la reserva.")

@app.delete("/reservas/{reserva_id}", status_code=status.HTTP_200_OK)
def cancelar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    logger.request_received("DELETE", f"/reservas/{reserva_id}")
    try:
        reserva = db.query(Ventana).filter(Ventana.id == reserva_id).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        db.delete(reserva)
        db.commit()
        logger.response_sent(200, "Reserva cancelada", f"ID: {reserva_id}")
        return {"message": "Reserva cancelada"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al cancelar la reserva.")

@app.get("/solicitudes", status_code=status.HTTP_200_OK)
def obtener_solicitudes_usuario(
    usuario_id: Optional[int] = Query(None, ge=1),
    correo: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    logger.request_received("GET", "/solicitudes", {"usuario_id": usuario_id, "correo": correo})

    if not usuario_id and not correo:
        raise HTTPException(status_code=422, detail="Debe proporcionar 'usuario_id' o 'correo'")

    try:
        user_query = db.query(Usuario)
        if usuario_id and correo:
            user = user_query.filter(Usuario.id == usuario_id, func.lower(Usuario.correo) == correo.lower()).first()
            if not user:
                raise HTTPException(status_code=400, detail="El usuario_id no coincide con el correo proporcionado")
        elif usuario_id:
            user = user_query.filter(Usuario.id == usuario_id).first()
        else:
            user = user_query.filter(func.lower(Usuario.correo) == correo.lower()).first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        solicitudes = db.query(Solicitud).filter(Solicitud.usuario_id == user.id)\
            .options(
                joinedload(Solicitud.items).joinedload(ItemSolicitud.item),
                joinedload(Solicitud.prestamos).joinedload(Prestamo.item_existencia).joinedload(ItemExistencia.item),
                joinedload(Solicitud.ventanas).joinedload(Ventana.item_existencia).joinedload(ItemExistencia.item)
            ).order_by(Solicitud.registro_instante.desc()).all()

        response_data = []
        for s in solicitudes:
            item_nombres = set()
            for item_sol in s.items:
                item_nombres.add(item_sol.item.nombre)
            for prestamo in s.prestamos:
                item_nombres.add(prestamo.item_existencia.item.nombre)
            for ventana in s.ventanas:
                item_nombres.add(ventana.item_existencia.item.nombre)

            response_data.append({
                "id": s.id,
                "usuario_id": s.usuario_id,
                "tipo": s.tipo,
                "estado": s.estado,
                "registro_instante": s.registro_instante.isoformat(),
                "items": [{"nombre": nombre} for nombre in item_nombres]
            })
        
        respuesta = {
            "usuario_id": user.id,
            "total": len(response_data),
            "solicitudes": response_data
        }
        logger.response_sent(200, "Solicitudes obtenidas", f"Total: {len(response_data)}")
        return JSONResponse(content=respuesta)

    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al obtener solicitudes.")

@app.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def crear_solicitud(datos: SolicitudCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/solicitudes", datos.dict(exclude_none=True))

    if not datos.usuario_id and not datos.correo:
        raise HTTPException(status_code=422, detail="Debe proporcionar 'usuario_id' o 'correo'")

    try:
        user_query = db.query(Usuario)
        if datos.usuario_id and datos.correo:
            user = user_query.filter(Usuario.id == datos.usuario_id, func.lower(Usuario.correo) == datos.correo.lower()).first()
            if not user:
                raise HTTPException(status_code=400, detail="El usuario_id no coincide con el correo proporcionado")
        elif datos.usuario_id:
            user = user_query.filter(Usuario.id == datos.usuario_id).first()
        else:
            user = user_query.filter(func.lower(Usuario.correo) == datos.correo.lower()).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        nueva_solicitud = Solicitud(
            usuario_id=user.id,
            tipo=datos.tipo,
            estado='PENDIENTE',
            registro_instante=datetime.now()
        )
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)

        response_payload = {
            "message": "Solicitud creada exitosamente",
            "solicitud_id": nueva_solicitud.id,
            "usuario_id": user.id,
        }
        logger.response_sent(201, "Solicitud creada", f"ID: {nueva_solicitud.id}")
        return response_payload
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al crear la solicitud.")

@app.post("/prestamos", status_code=status.HTTP_201_CREATED)
def registrar_prestamo(prestamo_data: PrestamoCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/prestamos", prestamo_data.dict())
    try:
        fecha_prestamo = datetime.now()
        nuevo_prestamo = Prestamo(
            item_existencia_id=prestamo_data.item_existencia_id,
            solicitud_id=prestamo_data.solicitud_id,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion=fecha_prestamo + timedelta(days=30),
            estado='ACTIVO',
            renovaciones_realizadas=0,
            registro_instante=datetime.now(),
            comentario=prestamo_data.comentario
        )
        db.add(nuevo_prestamo)
        db.commit()
        logger.response_sent(201, "Préstamo registrado", f"Solicitud: {prestamo_data.solicitud_id}")
        return {"message": "Préstamo registrado"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al registrar el préstamo.")

@app.post("/devoluciones", status_code=status.HTTP_200_OK)
def registrar_devolucion(devolucion_data: DevolucionCreate, db: Session = Depends(get_db)):
    logger.request_received("POST", "/devoluciones", devolucion_data.dict())
    try:
        prestamo = db.query(Prestamo).filter(Prestamo.id == devolucion_data.prestamo_id).first()
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        
        prestamo.estado = 'DEVUELTO'
        prestamo.comentario = devolucion_data.comentario
        prestamo.fecha_devolucion = datetime.now()
        db.commit()
        
        logger.response_sent(200, "Devolución registrada", f"Préstamo ID: {devolucion_data.prestamo_id}")
        return {"message": "Devolución registrada"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al registrar la devolución.")

@app.put("/prestamos/{prestamo_id}/renovar", status_code=status.HTTP_200_OK)
def renovar_prestamo(prestamo_id: int, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/prestamos/{prestamo_id}/renovar")
    try:
        prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")

        prestamo.renovaciones_realizadas += 1
        prestamo.fecha_prestamo = datetime.now()
        prestamo.fecha_devolucion = datetime.now() + timedelta(days=30)
        prestamo.comentario = 'Préstamo renovado'
        prestamo.estado = 'ACTIVO'
        db.commit()
        
        logger.response_sent(200, "Préstamo renovado", f"ID: {prestamo_id}")
        return {"message": "Préstamo renovado"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al renovar el préstamo.")

@app.put("/items/{existencia_id}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado(existencia_id: int, body: EstadoUpdate, db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/items/{existencia_id}/estado", body.dict())
    try:
        item_existencia = db.query(ItemExistencia).filter(ItemExistencia.id == existencia_id).first()
        if not item_existencia:
            raise HTTPException(status_code=404, detail="Ítem no encontrado")
        
        item_existencia.estado = body.estado
        db.commit()
        
        logger.response_sent(200, "Estado actualizado", f"ID: {existencia_id}, Estado: {body.estado}")
        return {"message": f"Estado actualizado a {body.estado}"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al actualizar el estado.")