from fastapi import FastAPI, HTTPException, Body, Path, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os

app = FastAPI(title="Servicio de Gestión de Notificaciones (NOTIS)")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "Servicio NOTIS disponible"}

# Crear notificación
@app.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def crear_notificacion(notificacion: dict = Body(...)):
    query = text("""
        INSERT INTO notificacion (usuario_id, canal, tipo, mensaje, registro_instante)
        VALUES (:usuario_id, :canal, :tipo, :mensaje, NOW())
    """)
    try:
        with engine.begin() as conn:
            result = conn.execute(query, notificacion)
            return {"id": result.lastrowid, "message": "Notificación registrada correctamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener preferencias de notificación del usuario
@app.get("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def obtener_preferencias(usuario_id: int = Path(..., description="ID del usuario")):
    query = text("""
        SELECT preferencias_notificacion
        FROM usuario
        WHERE id = :usuario_id
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"usuario_id": usuario_id}).mappings().first()
            if not result:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            return {
                "usuario_id": usuario_id,
                "preferencias_notificacion": result["preferencias_notificacion"]
            }
    except SQLAlchemyError as e:
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