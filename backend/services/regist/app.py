from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger

app = FastAPI(title="Servicio de Gestión de Usuarios")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Crear logger para este servicio
logger = create_service_logger("regist")

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://regist:8000")
    
    await register_service(
        app=app,
        service_name="regist",
        service_url="http://regist:8000",
        description="Gestión de usuarios y autenticación",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:8000"))

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio REGIST disponible"}

# Registrar usuario
@app.post("/usuarios", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: dict = Body(...)):
    logger.request_received("POST", "/usuarios", usuario)
    
    query = text("""
        INSERT INTO usuario (id, nombre, correo, tipo, telefono, estado, preferencias_notificacion, registro_instante)
        VALUES (:id, :nombre, :correo, :tipo, :telefono, :estado, :preferencias_notificacion, NOW())
    """)
    
    logger.db_query(str(query), usuario)
    
    with engine.begin() as conn:
        result = conn.execute(query, usuario)
        response_data = {"id": result.lastrowid, "message": "Usuario registrado"}
        
        logger.response_sent(201, "Usuario registrado exitosamente", f"ID: {result.lastrowid}")
        return response_data

# Login usuario
@app.post("/auth/login")
def login(auth: dict = Body(...)):
    logger.request_received("POST", "/auth/login", {"correo": auth.get("correo")})
    
    correo = auth.get("correo")
    password = auth.get("password")
    query = text("SELECT * FROM usuario WHERE correo = :correo")
    
    logger.db_query(str(query), {"correo": correo})
    
    with engine.begin() as conn:
        user = conn.execute(query, {"correo": correo}).fetchone()
        if not user or password != "mock_password":
            logger.response_sent(401, "Credenciales inválidas")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        response_data = {"message": f"Usuario {correo} autenticado", "token": "fake-jwt-token"}
        logger.response_sent(200, "Autenticación exitosa", f"Usuario: {correo}")
        return response_data

# Retrieve usuario
@app.get("/usuarios/{id}")
def consultar_usuario(id: int):
    logger.request_received("GET", f"/usuarios/{id}")
    
    query = text("SELECT * FROM usuario WHERE id = :id")
    logger.db_query(str(query), {"id": id})
    
    with engine.begin() as conn:
        user = conn.execute(query, {"id": id}).fetchone()
        if not user:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        response_data = dict(user._mapping)
        logger.response_sent(200, "Usuario encontrado", f"ID: {id}")
        return response_data

# Update usuario
@app.put("/usuarios/{id}")
def actualizar_usuario(id: int, datos: dict = Body(...)):
    logger.request_received("PUT", f"/usuarios/{id}", datos)
    
    sets = ", ".join([f"{k} = :{k}" for k in datos.keys()])
    query = text(f"UPDATE usuario SET {sets} WHERE id = :id")
    datos["id"] = id
    
    logger.db_query(f"UPDATE usuario SET {sets} WHERE id = :id", datos)
    
    with engine.begin() as conn:
        conn.execute(query, datos)
        logger.response_sent(200, f"Usuario {id} actualizado")
        return {"message": f"Usuario {id} actualizado"}
