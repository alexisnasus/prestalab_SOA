from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from reportlab.pdfgen import canvas
import os
import io
import csv
import sys
from datetime import datetime, timedelta

sys.path.append('/app')
from bus_client import register_service, setup_heartbeat
from service_logger import create_service_logger
from models import Prestamo, Solicitud, ItemExistencia, Item, Sede, get_db, engine

app = FastAPI(title="Servicio de Gestión de Reportes")

logger = create_service_logger("gerep")

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://gerep:8000")
    
    await register_service(
        app=app,
        service_name="gerep",
        service_url="http://gerep:8000",
        description="Gestión de reportes e historial de préstamos",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

@app.get("/")
def root():
    return {"message": "El Servicio de Gestión de Reportes está activo"}

@app.get("/usuarios/{usuario_id}/historial")
def historial_usuario(usuario_id: int, formato: str = "json", db: Session = Depends(get_db)):
    logger.request_received("GET", f"/usuarios/{usuario_id}/historial", {"formato": formato})

    query = (
        db.query(
            Prestamo.id,
            Prestamo.fecha_prestamo,
            Prestamo.fecha_devolucion,
            Prestamo.estado,
            Item.nombre.label("item"),
            Item.tipo
        )
        .join(Solicitud, Prestamo.solicitud_id == Solicitud.id)
        .join(ItemExistencia, Prestamo.item_existencia_id == ItemExistencia.id)
        .join(Item, ItemExistencia.item_id == Item.id)
        .filter(Solicitud.usuario_id == usuario_id)
        .order_by(Prestamo.fecha_prestamo.desc())
    )
    
    logger.db_query(str(query.statement.compile(engine)), {"usuario_id": usuario_id})
    rows = query.all()

    historial = [
        {
            "prestamo_id": r.id,
            "fecha_prestamo": r.fecha_prestamo.strftime("%Y-%m-%d"),
            "fecha_devolucion": r.fecha_devolucion.strftime("%Y-%m-%d") if r.fecha_devolucion else None,
            "estado": r.estado,
            "item": r.item,
            "tipo": r.tipo
        } for r in rows
    ]

    if not historial and formato != 'json':
        raise HTTPException(status_code=404, detail="No se encontró historial para este usuario.")

    if formato == "json":
        logger.response_sent(200, f"Historial en JSON", f"Usuario: {usuario_id}, Registros: {len(historial)}")
        return JSONResponse(content={"usuario_id": usuario_id, "historial": historial})

    elif formato == "csv":
        logger.response_sent(200, f"Historial en CSV", f"Usuario: {usuario_id}")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=historial[0].keys())
        writer.writeheader()
        writer.writerows(historial)
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]),
                                 media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename=historial_{usuario_id}.csv"})

    elif formato == "pdf":
        logger.response_sent(200, f"Historial en PDF", f"Usuario: {usuario_id}")
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.setTitle(f"Historial Usuario {usuario_id}")

        pdf.drawString(100, 800, f"Historial de Usuario {usuario_id}")
        y = 760
        for h in historial:
            pdf.drawString(80, y, f"{h['fecha_prestamo']} - {h['item']} ({h['estado']})")
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 800

        pdf.save()
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename=historial_{usuario_id}.pdf"})

    else:
        logger.response_sent(400, "Formato no soportado")
        raise HTTPException(status_code=400, detail="Formato no soportado")

@app.get("/reportes/circulacion")
def reportes_circulacion(
    periodo: str = Query(..., description="Periodo en formato YYYY-MM"),
    sede_id: int = Query(..., description="ID de la sede"),
    db: Session = Depends(get_db)
):
    logger.request_received("GET", "/reportes/circulacion", {"periodo": periodo, "sede_id": sede_id})
    
    try:
        inicio = datetime.strptime(f"{periodo}-01", "%Y-%m-%d")
        fin_mes = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        fin = fin_mes
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de período inválido. Use YYYY-MM.")

    # Rotación
    rotacion = (
        db.query(func.count(Prestamo.id))
        .join(ItemExistencia)
        .filter(ItemExistencia.sede_id == sede_id, Prestamo.fecha_prestamo.between(inicio, fin))
        .scalar()
    )

    # Morosidad
    morosos = (
        db.query(func.count(Prestamo.id))
        .join(ItemExistencia)
        .filter(
            ItemExistencia.sede_id == sede_id,
            Prestamo.estado == 'VENCIDO',
            Prestamo.fecha_prestamo.between(inicio, fin)
        )
        .scalar()
    )
    
    total_prestamos = rotacion if rotacion > 0 else 1
    morosidad_porcentaje = (morosos / total_prestamos) * 100

    # Daños
    danos = (
        db.query(func.count(ItemExistencia.id))
        .filter(
            ItemExistencia.sede_id == sede_id,
            ItemExistencia.estado == 'DANNADO',
            ItemExistencia.registro_instante.between(inicio, fin)
        )
        .scalar()
    )

    response_data = {
        "sede_id": sede_id,
        "periodo": periodo,
        "metricas": {
            "rotacion_total": rotacion,
            "morosidad_porcentaje": round(morosidad_porcentaje, 2),
            "danos_reportados": danos
        }
    }
    
    logger.response_sent(200, "Reporte de circulación generado", response_data)
    return response_data