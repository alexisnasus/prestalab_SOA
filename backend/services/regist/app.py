from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
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

class UsuarioCreate(BaseModel):
    id: Optional[int] = Field(default=None, ge=1)
    nombre: str = Field(..., min_length=1)
    correo: EmailStr
    tipo: str = Field(..., min_length=1)
    telefono: str = Field(default="", max_length=15)
    password: str = Field(..., min_length=4)
    estado: str = Field(default="ACTIVO", min_length=1)
    preferencias_notificacion: int = 1


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=1)


# Registrar usuario
@app.post("/usuarios", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate = Body(...)):
    data = usuario.dict()
    logger.request_received("POST", "/usuarios", {**data, "password": "***"})

    columns = []
    values = []
    params = {}

    if data.get("id") is not None:
        columns.append("id")
        values.append(":id")
        params["id"] = data["id"]

    columns.extend([
        "nombre",
        "correo",
        "tipo",
        "telefono",
        "password",
        "estado",
        "preferencias_notificacion",
    ])

    params.update({
        "nombre": data["nombre"],
        "correo": data["correo"].lower(),
        "tipo": data["tipo"],
        "telefono": data.get("telefono", ""),
        "password": data["password"],
        "estado": data.get("estado", "ACTIVO"),
        "preferencias_notificacion": data.get("preferencias_notificacion", 1),
    })

    values.extend([
        ":nombre",
        ":correo",
        ":tipo",
        ":telefono",
        ":password",
        ":estado",
        ":preferencias_notificacion",
    ])

    columns.append("registro_instante")
    values.append("NOW()")

    query = text(
        f"INSERT INTO usuario ({', '.join(columns)}) VALUES ({', '.join(values)})"
    )

    logger.db_query(str(query), {**params, "password": "***"})

    try:
        with engine.begin() as conn:
            result = conn.execute(query, params)
            new_id = result.lastrowid if result.lastrowid else params.get("id")

            fetch_query = text(
                """
                SELECT id, nombre, correo, tipo, telefono, estado, preferencias_notificacion, registro_instante
                FROM usuario
                WHERE id = :id
                """
            )

            new_user = conn.execute(fetch_query, {"id": new_id}).mappings().first()

            response_data = {
                "message": "Usuario registrado",
                "user": dict(new_user) if new_user else {"id": new_id},
            }

            logger.response_sent(201, "Usuario registrado exitosamente", f"ID: {new_id}")
            return response_data
    except IntegrityError as exc:
        logger.error("Correo duplicado", str(exc.orig))
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    except SQLAlchemyError as exc:
        logger.error("Error registrando usuario", str(exc))
        raise HTTPException(status_code=500, detail="Error al registrar usuario")

# Login usuario
@app.post("/auth/login")
def login(auth: LoginRequest = Body(...)):
    payload = auth.dict()
    correo = payload["correo"].lower()
    logger.request_received("POST", "/auth/login", {"correo": correo})

    query = text("SELECT * FROM usuario WHERE correo = :correo")
    logger.db_query(str(query), {"correo": correo})

    with engine.begin() as conn:
        user = conn.execute(query, {"correo": correo}).mappings().first()
        if not user or user.get("password") != payload["password"]:
            logger.response_sent(401, "Credenciales inválidas")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        user_data = dict(user)
        user_data.pop("password", None)
        token = f"session-{user_data['id']}"

        response_data = {
            "message": f"Usuario {correo} autenticado",
            "token": token,
            "user": user_data,
        }

        logger.response_sent(200, "Autenticación exitosa", f"Usuario: {correo}")
        return response_data

# Retrieve usuario
@app.get("/usuarios/{id}")
def consultar_usuario(id: int):
    logger.request_received("GET", f"/usuarios/{id}")
    
    query = text("SELECT * FROM usuario WHERE id = :id")
    logger.db_query(str(query), {"id": id})
    
    with engine.begin() as conn:
        user = conn.execute(query, {"id": id}).mappings().first()
        if not user:
            logger.response_sent(404, "Usuario no encontrado")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        response_data = dict(user)
        response_data.pop("password", None)
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
