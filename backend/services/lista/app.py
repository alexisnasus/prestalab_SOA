from fastapi import FastAPI, HTTPException, Body, Path, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os

app = FastAPI(title="Servicio de Gestión de Listas de Espera")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "Servicio LISTA is running"}

# Agregar registro de lista de espera
@app.post("/lista-espera", status_code=status.HTTP_201_CREATED)
def agregar_lista_espera(
    solicitud_id: int = Body(..., embed=True),
    item_id: int = Body(..., embed=True),
    estado: str = Body("EN ESPERA", embed=True)
):
    query = text("""
        INSERT INTO lista_espera (solicitud_id, item_id, fecha_ingreso, estado, registro_instante)
        VALUES (:solicitud_id, :item_id, :fecha_ingreso, :estado, :registro_instante)
    """)
    now = datetime.now()

    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "solicitud_id": solicitud_id,
                "item_id": item_id,
                "fecha_ingreso": now,
                "estado": estado,
                "registro_instante": now
            })
        return {
            "message": "Registro agregado exitosamente",
            "solicitud_id": solicitud_id,
            "item_id": item_id,
            "fecha_ingreso": now.isoformat(),
            "estado": estado
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Atender registro de lista de espera
@app.put("/lista-espera/{id}", status_code=status.HTTP_200_OK)
def actualizar_estado_lista_espera(
    id: int = Path(..., gt=0),
    nuevo_estado: str = Body(..., embed=True)
):
    nuevo_estado = nuevo_estado.upper().strip()
    if nuevo_estado not in ("ATENDIDA", "CANCELADA"):
        raise HTTPException(status_code=400, detail="El estado debe ser 'ATENDIDA' o 'CANCELADA'")

    query = text("""
        UPDATE lista_espera
        SET estado = :estado, registro_instante = :instante
        WHERE id = :id
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(query, {
                "estado": nuevo_estado,
                "instante": datetime.now(),
                "id": id
            })
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {
            "message": f"Registro {id} actualizado correctamente"
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Consultar registros de lista de espera por ítem
@app.get("/lista-espera/{item_id}", status_code=status.HTTP_200_OK)
def obtener_lista_por_item(item_id: int = Path(..., gt=0)):
    query = text("""
        SELECT id, solicitud_id, item_id, fecha_ingreso, estado, registro_instante
        FROM lista_espera
        WHERE item_id = :item_id
        ORDER BY fecha_ingreso ASC
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"item_id": item_id})
            registros = [dict(row._mapping) for row in result]
        if not registros:
            raise HTTPException(status_code=404, detail="No se encontraron registros para este ítem")
        return {"item_id": item_id, "registros": registros}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
