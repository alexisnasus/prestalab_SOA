from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger

app = FastAPI(title="Servicio de Gestión de Sugerencias")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

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
    
    logger.registered(os.getenv("BUS_URL", "http://bus:8000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio SUGIT disponible"}

# Registrar sugerencia
@app.post("/sugerencias", status_code=status.HTTP_201_CREATED)
def registrar_sugerencia(sugerencia: dict = Body(...)):
    logger.request_received("POST", "/sugerencias", sugerencia)
    query = text("""
        INSERT INTO sugerencia (usuario_id, sugerencia, estado, registro_instante)
        VALUES (:usuario_id, :sugerencia, 'PENDIENTE', NOW())
    """)
    logger.db_query(str(query), sugerencia)
    with engine.begin() as conn:
        result = conn.execute(query, sugerencia)
        response_data = {"id": result.lastrowid, "message": "Sugerencia registrada"}
        logger.response_sent(201, "Sugerencia registrada", f"ID: {result.lastrowid}")
        return response_data

# Listar sugerencias
@app.get("/sugerencias", status_code=status.HTTP_200_OK)
def listar_sugerencias():
    logger.request_received("GET", "/sugerencias")
    query = text("SELECT * FROM sugerencia")
    logger.db_query(str(query))
    with engine.connect() as conn:
        result = conn.execute(query)
        data = [dict(row._mapping) for row in result]
        logger.response_sent(200, "Sugerencias obtenidas", f"Total: {len(data)}")
        return data

# Aprobar sugerencia
@app.put("/sugerencias/{id}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_sugerencia(id: int):
    query = text("UPDATE sugerencia SET estado = 'APROBADA' WHERE id = :id")
    with engine.begin() as conn:
        result = conn.execute(query, {"id": id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sugerencia no encontrada")
    return {"id": id, "message": "Sugerencia aprobada"}

# Rechazar sugerencia
@app.put("/sugerencias/{id}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_sugerencia(id: int):
    query = text("UPDATE sugerencia SET estado = 'RECHAZADA' WHERE id = :id")
    with engine.begin() as conn:
        result = conn.execute(query, {"id": id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sugerencia no encontrada")
    return {"id": id, "message": "Sugerencia rechazada"}