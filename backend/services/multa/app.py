from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger

app = FastAPI(title="Servicio de Gestión de Multas")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Crear logger para este servicio
logger = create_service_logger("multa")

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

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
    
    logger.registered(os.getenv("BUS_URL", "http://bus:8000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio MULTA disponible"}

# Consultar multas de un usuario
@app.get("/usuarios/{id}/multas")
def get_multas_usuario(id: int):
    logger.request_received("GET", f"/usuarios/{id}/multas")
    
    query = text("""
        SELECT m.id, m.prestamo_id, m.motivo, m.valor, m.estado, m.registro_instante
        FROM multa m
        JOIN prestamo p ON m.prestamo_id = p.id
        JOIN solicitud s ON p.solicitud_id = s.id
        WHERE s.usuario_id = :usuario_id
    """)
    
    logger.db_query(str(query), {"usuario_id": id})
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"usuario_id": id}).mappings().all()
        
        response_data = {"usuario_id": id, "multas": result}
        logger.response_sent(200, f"Multas del usuario {id}", f"Total: {len(result)}")
        return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Registrar multa
@app.post("/multas", status_code=status.HTTP_201_CREATED)
def crear_multa(multa: dict = Body(...)):
    logger.request_received("POST", "/multas", multa)
    
    query = text("""
        INSERT INTO multa (prestamo_id, motivo, valor, estado, registro_instante)
        VALUES (:prestamo_id, :motivo, :valor, :estado, NOW())
    """)
    
    logger.db_query(str(query), multa)
    
    try:
        with engine.begin() as conn:
            result = conn.execute(query, multa)
        
        response_data = {"id": result.lastrowid, "message": "Multa registrada con éxito"}
        logger.response_sent(201, "Multa registrada", f"ID: {result.lastrowid}")
        return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Aplicar / quitar estado DEUDOR
@app.put("/usuarios/{id}/estado")
def actualizar_bloqueo(id: int, data: dict = Body(...)):
    logger.request_received("PUT", f"/usuarios/{id}/estado", data)
    
    if "estado" not in data:
        logger.response_sent(400, "Campo 'estado' requerido")
        raise HTTPException(status_code=400, detail="Campo 'estado' requerido")
    
    query = text("""
        UPDATE usuario
        SET estado = :estado
        WHERE id = :usuario_id
    """)
    
    logger.db_query(str(query), {"estado": data["estado"], "usuario_id": id})
    
    try:
        with engine.begin() as conn:
            result = conn.execute(query, {"estado": data["estado"], "usuario_id": id})
            if result.rowcount == 0:
                logger.response_sent(404, "Usuario no encontrado")
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        response_data = {"message": f"Estado del usuario modificado correctamente a {data['estado']}"}
        logger.response_sent(200, f"Estado actualizado a {data['estado']}", f"Usuario: {id}")
        return response_data
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail=str(e))
