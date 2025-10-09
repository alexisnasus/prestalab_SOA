from fastapi import FastAPI, HTTPException, Query, Path, Body, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime, timedelta
import sys
sys.path.append('/app')  # Para importar bus_client desde el contenedor
from bus_client import register_service

app = FastAPI(title="Servicio de gestión de Préstamos & Artículos")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

# ============================================================================
# REGISTRO EN EL BUS (SOA)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    await register_service(
        app=app,
        service_name="prart",
        service_url="http://prart:8000",
        description="Gestión de préstamos y artículos del catálogo",
        version="1.0.0"
    )

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "Servicio PRART disponible"}

# Obtener items
@app.get("/items")
def buscar_items(
    nombre: str = Query(None),
    tipo: str = Query(None)
):
    try:
        query = "SELECT * FROM item WHERE 1=1"
        params = {}
        if nombre:
            query += " AND nombre LIKE :nombre"
            params["nombre"] = f"%{nombre}%"
        if tipo:
            query += " AND tipo = :tipo"
            params["tipo"] = tipo

        with engine.connect() as conn:
            result = conn.execute(text(query), params).mappings().all()
        return result
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Registrar reserva con ventana
@app.post("/reservas", status_code=status.HTTP_201_CREATED)
def crear_reserva(
    solicitud_id: int = Body(...),
    item_existencia_id: int = Body(...),
    inicio: str = Body(...),
    fin: str = Body(...)
):
    try:
        inicio_dt = datetime.fromisoformat(inicio)
        fin_dt = datetime.fromisoformat(fin)
        if fin_dt <= inicio_dt:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser mayor a la fecha de inicio")

        with engine.begin() as conn:
            query = """
            INSERT INTO ventana (solicitud_id, item_existencia_id, inicio, fin)
            VALUES (:solicitud_id, :item_existencia_id, :inicio, :fin)
            """
            conn.execute(
                text(query),
                {"solicitud_id": solicitud_id, "item_existencia_id": item_existencia_id, "inicio": inicio_dt, "fin": fin_dt}
            )
        return {"message": "Reserva creada exitosamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cancelar/caducar reserva
@app.delete("/reservas/{reserva_id}", status_code=status.HTTP_200_OK)
def cancelar_reserva(reserva_id: int = Path(...)):
    try:
        with engine.begin() as conn:
            query = "DELETE FROM ventana WHERE id = :reserva_id"
            result = conn.execute(text(query), {"reserva_id": reserva_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        return {"message": "Reserva cancelada"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Registrar solicitud
@app.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def crear_solicitud(
    usuario_id: int = Body(...),
    tipo: str = Body(...)
):
    try:
        with engine.begin() as conn:
            query = """
            INSERT INTO solicitud (usuario_id, tipo, estado, registro_instante)
            VALUES (:usuario_id, :tipo, 'PENDIENTE', NOW())
            """
            conn.execute(
                text(query),
                {"usuario_id": usuario_id, "tipo": tipo}
            )
        return {"message": "Reserva creada exitosamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Registrar préstamo
@app.post("/prestamos", status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    solicitud_id: int = Body(...),
    item_existencia_id: int = Body(...),
    comentario: str = Body(None)
):
    try:
        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=30)
        with engine.begin() as conn:
            query = """
            INSERT INTO prestamo (item_existencia_id, solicitud_id, fecha_prestamo, fecha_devolucion, estado, renovaciones_realizadas, registro_instante, comentario)
            VALUES (:item_existencia_id, :solicitud_id, :fecha_prestamo, :fecha_devolucion, 'ACTIVO', 0, NOW(), :comentario)
            """
            conn.execute(
                text(query),
                {"item_existencia_id": item_existencia_id, "solicitud_id": solicitud_id, "fecha_prestamo": fecha_prestamo, "fecha_devolucion": fecha_devolucion, "comentario": comentario}
            )
        return {"message": "Préstamo registrado"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Registrar devolución de ítem
@app.post("/devoluciones", status_code=status.HTTP_200_OK)
def registrar_devolucion(
    prestamo_id: int = Body(...),
    comentario: str = Body(None)
):
    try:
        with engine.begin() as conn:
            query = """
            UPDATE prestamo
            SET estado = 'DEVUELTO', comentario = :comentario
            WHERE id = :prestamo_id
            """
            result = conn.execute(text(query), {"prestamo_id": prestamo_id, "comentario": comentario})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado o no activo")
        return {"message": "Devolución registrada"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Renovar préstamo
@app.put("/prestamos/{prestamo_id}/renovar", status_code=status.HTTP_200_OK)
def renovar_prestamo(prestamo_id: int = Path(...)):
    try:
        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=30)
        with engine.begin() as conn:
            query = """
            UPDATE prestamo
            SET renovaciones_realizadas = renovaciones_realizadas + 1, fecha_prestamo = :fecha_prestamo, fecha_devolucion = :fecha_devolucion, comentario= 'Préstamo renovado', estado= 'ACTIVO'
            WHERE id = :prestamo_id
            """
            result = conn.execute(text(query), {"prestamo_id": prestamo_id, "fecha_prestamo": fecha_prestamo, "fecha_devolucion": fecha_devolucion})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        return {"message": "Préstamo renovado"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar estado de item/existencia
@app.put("/items/{existencia_id}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado(
    existencia_id: int = Path(...),
    body: dict = Body(...)
):
    estado = body.get("estado")
    if not estado:
        raise HTTPException(status_code=400, detail="Falta el campo 'estado'")

    try:
        with engine.begin() as conn:
            query = "UPDATE item_existencia SET estado = :estado WHERE id = :existencia_id"
            result = conn.execute(text(query), {"estado": estado, "existencia_id": existencia_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado")
        return {"message": f"Estado actualizado a {estado}"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))