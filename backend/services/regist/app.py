from fastapi import FastAPI, HTTPException, Body, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import os
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service
from service_logger import create_service_logger
from models import Usuario, Solicitud, get_db

app = FastAPI(title="Servicio de Gestión de Usuarios")

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
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

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
def registrar_usuario(usuario: UsuarioCreate = Body(...), db: Session = Depends(get_db)):
    data = usuario.dict()
    logger.request_received("POST", "/usuarios", {**data, "password": "***"})

    try:
        # Crear instancia del modelo Usuario
        nuevo_usuario = Usuario(
            nombre=data["nombre"],
            correo=data["correo"].lower(),
            tipo=data["tipo"],
            telefono=data.get("telefono", ""),
            estado=data.get("estado", "ACTIVO"),
            preferencias_notificacion=data.get("preferencias_notificacion", 1),
            registro_instante=datetime.now()
        )
        
        # Establecer la contraseña hasheada
        nuevo_usuario.set_password(data["password"])
        
        # Si se proporciona un ID específico, establecerlo
        if data.get("id") is not None:
            nuevo_usuario.id = data["id"]
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        response_data = {
            "message": "Usuario registrado",
            "user": nuevo_usuario.to_dict(),
        }
        
        logger.response_sent(201, "Usuario registrado exitosamente", f"ID: {nuevo_usuario.id}")
        return response_data
        
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integridad de datos", f"Correo duplicado: {exc.orig}")
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error de base de datos", f"Error al registrar usuario: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Error interno al registrar usuario")
    except Exception as exc:
        db.rollback()
        logger.error("Error inesperado", f"Error al registrar usuario: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Error inesperado en el servidor")

# Autenticar usuario
@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(auth: LoginRequest = Body(...), db: Session = Depends(get_db)):
    payload = auth.dict()
    correo = payload["correo"].lower()
    logger.request_received("POST", "/auth/login", {"correo": correo})

    # Buscar usuario por correo usando ORM
    user = db.query(Usuario).filter(Usuario.correo == correo).first()
    
    if not user or not user.check_password(payload["password"]):
        logger.response_sent(401, "Credenciales inválidas")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    user_data = user.to_dict()
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
def consultar_usuario(id: int, db: Session = Depends(get_db)):
    logger.request_received("GET", f"/usuarios/{id}")
    
    # Buscar usuario por ID usando ORM
    user = db.query(Usuario).filter(Usuario.id == id).first()
    
    if not user:
        logger.response_sent(404, "Usuario no encontrado")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    response_data = user.to_dict()
    logger.response_sent(200, "Usuario encontrado", f"ID: {id}")
    return response_data

# Update usuario
@app.put("/usuarios/{id}")
def actualizar_usuario(id: int, datos: dict = Body(...), db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/usuarios/{id}", datos)
    
    # Buscar usuario por ID usando ORM
    user = db.query(Usuario).filter(Usuario.id == id).first()
    
    if not user:
        logger.response_sent(404, "Usuario no encontrado")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar solo los campos proporcionados
    try:
        for key, value in datos.items():
            if key == "password":
                # Hashear la contraseña si se está actualizando
                user.set_password(value)
            elif hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        logger.response_sent(200, f"Usuario {id} actualizado")
        return {"message": f"Usuario {id} actualizado"}
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error actualizando usuario", str(exc))
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")


class SolicitudActualizacion(BaseModel):
    estado: str = Field(..., pattern="^(APROBADA|RECHAZADA)$")


# Aprobar o rechazar solicitud de registro
@app.put("/solicitudes-registro/{solicitud_id}/actualizar")
def actualizar_solicitud_registro(solicitud_id: int, actualizacion: SolicitudActualizacion = Body(...), db: Session = Depends(get_db)):
    logger.request_received("PUT", f"/solicitudes-registro/{solicitud_id}/actualizar", actualizacion.dict())
    
    # Buscar la solicitud por ID usando ORM
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    
    if not solicitud:
        logger.response_sent(404, "Solicitud no encontrada")
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.estado != "PENDIENTE":
        logger.response_sent(400, f"Solicitud no está en estado PENDIENTE, estado actual: {solicitud.estado}")
        raise HTTPException(
            status_code=400,
            detail=f"La solicitud no está en estado PENDIENTE. Estado actual: {solicitud.estado}"
        )
    
    # Actualizar el estado de la solicitud
    try:
        solicitud.estado = actualizacion.estado
        db.commit()
        db.refresh(solicitud)
        
        response_data = {
            "message": f"Solicitud {solicitud_id} {actualizacion.estado.lower()}",
            "solicitud_id": solicitud_id,
            "nuevo_estado": actualizacion.estado
        }
        
        logger.response_sent(200, f"Solicitud {solicitud_id} actualizada a {actualizacion.estado}")
        return response_data
        
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Error actualizando solicitud", str(exc))
        raise HTTPException(status_code=500, detail="Error al actualizar solicitud")
