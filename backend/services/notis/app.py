from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

app = FastAPI(title="Servicio de Gestión de Notificaciones")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)


@app.get("/")
def root():
    return {"message": "Servicio NOTIS disponible"}

# POST /notificaciones → enviar aviso (RF10)
@app.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def enviar_notificacion(
    usuario_id: int = Body(...),
    canal: str = Body(...),  # EMAIL, WHATSAPP, PORTAL
    tipo: str = Body(...),   # RECORDATORIO, RESERVA_CREADA, etc.
    mensaje: str = Body(...),
):
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO notificacion (usuario_id, canal, tipo, mensaje, registro_instante)
                    VALUES (:usuario_id, :canal, :tipo, :mensaje, NOW())
                    """
                ),
                {
                    "usuario_id": usuario_id,
                    "canal": canal,
                    "tipo": tipo,
                    "mensaje": mensaje,
                },
            )
        return {"status": "ok", "detail": "Notificación registrada"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /preferencias/{usuarioId} → consultar preferencias
@app.get("/preferencias/{usuario_id}")
def get_preferencias(usuario_id: int):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT canales FROM preferencias WHERE usuario_id = :usuario_id"),
                {"usuario_id": usuario_id},
            ).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Preferencias no encontradas")

            return {"usuario_id": usuario_id, "canales": result[0].split(",")}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /preferencias/{usuarioId} → actualizar preferencias
@app.put("/preferencias/{usuario_id}", status_code=status.HTTP_200_OK)
def update_preferencias(usuario_id: int, canales: list[str] = Body(...)):
    try:
        canales_str = ",".join(canales)
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO preferencias (usuario_id, canales)
                    VALUES (:usuario_id, :canales)
                    ON DUPLICATE KEY UPDATE canales = :canales
                    """
                ),
                {"usuario_id": usuario_id, "canales": canales_str},
            )
        return {"status": "ok", "detail": "Preferencias actualizadas"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
