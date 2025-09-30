from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="Servicio de Gestión de Sugerencias")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "Servicio SUGIT disponible"}

# Registrar sugerencia
@app.post("/sugerencias", status_code=status.HTTP_201_CREATED)
def registrar_sugerencia(sugerencia: dict = Body(...)):
    query = text("""
        INSERT INTO sugerencia (usuario_id, sugerencia, estado, registro_instante)
        VALUES (:usuario_id, :sugerencia, 'PENDIENTE', NOW())
    """)
    with engine.begin() as conn:
        result = conn.execute(query, sugerencia)
        return {"id": result.lastrowid, "message": "Sugerencia registrada"}

# Listar sugerencias
@app.get("/sugerencias", status_code=status.HTTP_200_OK)
def listar_sugerencias():
    query = text("SELECT * FROM sugerencia")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]

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