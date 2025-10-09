from fastapi import FastAPI, HTTPException, Body, Path, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger

app = FastAPI(title="Servicio de Gestión de Notificaciones (NOTIS)")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Crear logger para este servicio
logger = create_service_logger("notis")

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

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
    
    logger.registered(os.getenv("BUS_URL", "http://bus:8000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio NOTIS disponible"}

# Crear notificación
@app.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def crear_notificacion(notificacion: dict = Body(...)):
    logger.request_received("POST", "/notificaciones", notificacion)
    
    query = text("""
        INSERT INTO notificacion (usuario_id, canal, tipo, mensaje, registro_instante)
        VALUES (:usuario_id, :canal, :tipo, :mensaje, NOW())
    """)
    
    logger.db_query(str(query), notificacion)
    
    try:
        with engine.begin() as conn:
            result = conn.execute(query, notificacion)
            response_data = {"id": result.lastrowid, "message": "Notificación registrada correctamente"}
            logger.response_sent(201, "Notificación creada", f"ID: {result.lastrowid}")
            return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Obtener preferencias de notificación del usuario
@app.get("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def obtener_preferencias(usuario_id: int = Path(..., description="ID del usuario")):
    logger.request_received("GET", f"/preferencias/{usuario_id}")
    
    query = text("""
        SELECT preferencias_notificacion
        FROM usuario
        WHERE id = :usuario_id
    """)
    
    logger.db_query(str(query), {"usuario_id": usuario_id})

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"usuario_id": usuario_id}).mappings().first()
            if not result:
                logger.response_sent(404, "Usuario no encontrado")
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            response_data = {
                "usuario_id": usuario_id,
                "preferencias_notificacion": result["preferencias_notificacion"]
            }
            logger.response_sent(200, "Preferencias obtenidas", f"Usuario: {usuario_id}")
            return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar preferencias de notifiación del usuario
@app.put("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def actualizar_preferencias(usuario_id: int, preferencias: dict = Body(...)):
    if "preferencias_notificacion" not in preferencias:
        raise HTTPException(status_code=400, detail="Debe incluir 'preferencias_notificacion' en el cuerpo")

    query = text("""
        UPDATE usuario
        SET preferencias_notificacion = :preferencias_notificacion
        WHERE id = :usuario_id
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(query, {
                "usuario_id": usuario_id,
                "preferencias_notificacion": preferencias["preferencias_notificacion"]
            })

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "message": f"Preferencias e notificaión del usuario {usuario_id} actualizadas correctamente",

        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))