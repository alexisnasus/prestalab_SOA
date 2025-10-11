from fastapi import FastAPI, HTTPException, Query, Path, Body, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime, timedelta
from typing import Optional
import sys
from pydantic import BaseModel, Field
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger

app = FastAPI(title="Servicio de gestión de Préstamos & Artículos")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Crear logger para este servicio
logger = create_service_logger("prart")

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://prart:8000")
    
    await register_service(
        app=app,
        service_name="prart",
        service_url="http://prart:8000",
        description="Gestión de préstamos y artículos del catálogo",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:8000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio PRART disponible"}

# Obtener items
@app.get("/items")
def buscar_items(
    nombre: str = Query(None),
    tipo: str = Query(None)
):
    logger.request_received("GET", "/items", {"nombre": nombre, "tipo": tipo})
    try:
        query = "SELECT * FROM item WHERE 1=1"
        params = {}
        if nombre:
            query += " AND nombre LIKE :nombre"
            params["nombre"] = f"%{nombre}%"
        if tipo:
            query += " AND tipo = :tipo"
            params["tipo"] = tipo

        logger.db_query(query, params)
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params).mappings().all()
        
        logger.response_sent(200, "Items obtenidos", f"Total: {len(result)}")
        return result
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Registrar reserva con ventana
@app.post("/reservas", status_code=status.HTTP_201_CREATED)
def crear_reserva(
    solicitud_id: int = Body(...),
    item_existencia_id: int = Body(...),
    inicio: str = Body(...),
    fin: str = Body(...)
):
    try:
        inicio_dt = datetime.fromisoformat(inicio)
        fin_dt = datetime.fromisoformat(fin)
        if fin_dt <= inicio_dt:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser mayor a la fecha de inicio")

        with engine.begin() as conn:
            query = """
            INSERT INTO ventana (solicitud_id, item_existencia_id, inicio, fin)
            VALUES (:solicitud_id, :item_existencia_id, :inicio, :fin)
            """
            conn.execute(
                text(query),
                {"solicitud_id": solicitud_id, "item_existencia_id": item_existencia_id, "inicio": inicio_dt, "fin": fin_dt}
            )
        return {"message": "Reserva creada exitosamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cancelar/caducar reserva
@app.delete("/reservas/{reserva_id}", status_code=status.HTTP_200_OK)
def cancelar_reserva(reserva_id: int = Path(...)):
    try:
        with engine.begin() as conn:
            query = "DELETE FROM ventana WHERE id = :reserva_id"
            result = conn.execute(text(query), {"reserva_id": reserva_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        return {"message": "Reserva cancelada"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

class SolicitudCreate(BaseModel):
    usuario_id: Optional[int] = Field(default=None, description="ID del usuario solicitante")
    correo: Optional[str] = Field(default=None, description="Correo del usuario solicitante")
    tipo: str = Field(..., min_length=1, description="Tipo de solicitud")


# Registrar solicitud
@app.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def crear_solicitud(datos: SolicitudCreate = Body(...)):
    payload = datos.model_dump(exclude_none=True)
    logger.request_received("POST", "/solicitudes", payload)

    try:
        usuario_id = datos.usuario_id
        correo = datos.correo.strip().lower() if datos.correo else None

        if usuario_id is None and not correo:
            raise HTTPException(status_code=422, detail="Debe proporcionar 'usuario_id' o 'correo'")

        if usuario_id is not None and correo is not None:
            lookup_query = text("SELECT id FROM usuario WHERE id = :usuario_id AND LOWER(correo) = :correo")
            params = {"usuario_id": usuario_id, "correo": correo}
            logger.db_query(str(lookup_query), params)
            with engine.connect() as conn:
                match = conn.execute(lookup_query, params).mappings().first()
            if not match:
                raise HTTPException(status_code=400, detail="El usuario_id no coincide con el correo proporcionado")

        if usuario_id is None:
            lookup_query = text("SELECT id FROM usuario WHERE LOWER(correo) = :correo")
            params = {"correo": correo}
            logger.db_query(str(lookup_query), params)
            with engine.connect() as conn:
                user = conn.execute(lookup_query, params).mappings().first()
            if not user:
                raise HTTPException(status_code=404, detail="No se encontró un usuario con ese correo")
            usuario_id = user["id"]
            payload["usuario_id"] = usuario_id

        insert_query = text(
            """
            INSERT INTO solicitud (usuario_id, tipo, estado, registro_instante)
            VALUES (:usuario_id, :tipo, 'PENDIENTE', NOW())
            """
        )
        insert_params = {"usuario_id": usuario_id, "tipo": datos.tipo}
        logger.db_query(str(insert_query), insert_params)

        with engine.begin() as conn:
            result = conn.execute(insert_query, insert_params)
            solicitud_id = result.lastrowid

        response_payload = {
            "message": "Reserva creada exitosamente",
            "solicitud_id": solicitud_id,
            "usuario_id": usuario_id,
        }
        logger.response_sent(201, "Solicitud creada", f"ID: {solicitud_id}")
        return response_payload
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Registrar préstamo
@app.post("/prestamos", status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    solicitud_id: int = Body(...),
    item_existencia_id: int = Body(...),
    comentario: str = Body(None)
):
    logger.request_received("POST", "/prestamos", {"solicitud_id": solicitud_id, "item_existencia_id": item_existencia_id})
    try:
        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=30)
        
        query = text("""
            INSERT INTO prestamo (item_existencia_id, solicitud_id, fecha_prestamo, fecha_devolucion, estado, renovaciones_realizadas, registro_instante, comentario)
            VALUES (:item_existencia_id, :solicitud_id, :fecha_prestamo, :fecha_devolucion, 'ACTIVO', 0, NOW(), :comentario)
        """)
        
        logger.db_query(str(query), {"solicitud_id": solicitud_id, "item_existencia_id": item_existencia_id})
        
        with engine.begin() as conn:
            conn.execute(
                query,
                {"item_existencia_id": item_existencia_id, "solicitud_id": solicitud_id, "fecha_prestamo": fecha_prestamo, "fecha_devolucion": fecha_devolucion, "comentario": comentario}
            )
        
        logger.response_sent(201, "Préstamo registrado", f"Solicitud: {solicitud_id}")
        return {"message": "Préstamo registrado"}
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Registrar devolución de ítem
@app.post("/devoluciones", status_code=status.HTTP_200_OK)
def registrar_devolucion(
    prestamo_id: int = Body(...),
    comentario: str = Body(None)
):
    try:
        with engine.begin() as conn:
            query = """
            UPDATE prestamo
            SET estado = 'DEVUELTO', comentario = :comentario
            WHERE id = :prestamo_id
            """
            result = conn.execute(text(query), {"prestamo_id": prestamo_id, "comentario": comentario})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado o no activo")
        return {"message": "Devolución registrada"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Renovar préstamo
@app.put("/prestamos/{prestamo_id}/renovar", status_code=status.HTTP_200_OK)
def renovar_prestamo(prestamo_id: int = Path(...)):
    try:
        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=30)
        with engine.begin() as conn:
            query = """
            UPDATE prestamo
            SET renovaciones_realizadas = renovaciones_realizadas + 1, fecha_prestamo = :fecha_prestamo, fecha_devolucion = :fecha_devolucion, comentario= 'Préstamo renovado', estado= 'ACTIVO'
            WHERE id = :prestamo_id
            """
            result = conn.execute(text(query), {"prestamo_id": prestamo_id, "fecha_prestamo": fecha_prestamo, "fecha_devolucion": fecha_devolucion})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        return {"message": "Préstamo renovado"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar estado de item/existencia
@app.put("/items/{existencia_id}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado(
    existencia_id: int = Path(...),
    body: dict = Body(...)
):
    estado = body.get("estado")
    if not estado:
        raise HTTPException(status_code=400, detail="Falta el campo 'estado'")

    try:
        with engine.begin() as conn:
            query = "UPDATE item_existencia SET estado = :estado WHERE id = :existencia_id"
            result = conn.execute(text(query), {"estado": estado, "existencia_id": existencia_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado")
        return {"message": f"Estado actualizado a {estado}"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))