from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os

app = FastAPI(title="Servicio de Gestión de Reportes")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "El Servicio de Gestión de Reportes está activo"}

# GET /usuarios/{id}/historial?formato=pdf|csv
@app.get("/usuarios/{usuario_id}/historial")
def historial_usuario(usuario_id: int, formato: str = "json"):
    """
    Exporta el historial de préstamos de un usuario en formato:
    - json (default)
    - csv
    - pdf
    """

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT p.id, p.fecha_prestamo, p.fecha_devolucion, p.estado,
                   i.nombre as item, i.tipo
            FROM prestamo p
            JOIN solicitud s ON p.solicitud_id = s.id
            JOIN item_existencia ie ON p.item_existencia_id = ie.id
            JOIN item i ON ie.item_id = i.id
            WHERE s.usuario_id = :usuario_id
            ORDER BY p.fecha_prestamo DESC
        """), {"usuario_id": usuario_id}).fetchall()

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

    if formato == "json":
        return JSONResponse(content={"usuario_id": usuario_id, "historial": historial})

    elif formato == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=historial[0].keys())
        writer.writeheader()
        writer.writerows(historial)
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]),
                                 media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename=historial_{usuario_id}.csv"})

    elif formato == "pdf":
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
        raise HTTPException(status_code=400, detail="Formato no soportado")

# GET /reportes/circulacion?periodo&=...&sede=...
@app.get("/reportes/circulacion")
def reportes_circulacion(
    periodo: str = Query(..., description="Periodo en formato YYYY-MM"),
    sede: int = Query(..., description="ID de la sede")
    
    """
    Retorna métricas de:
    - Rotación (cantidad de préstamos realizados en el periodo por sede)
    - Morosidad (porcentaje de préstamos vencidos/no devueltos a tiempo)
    - Daños (cantidad de items dañados reportados en item_existencia)
    """

    with engine.connect() as conn:
        # Calcular fechas del periodo
        inicio = f"{periodo}-01"
        fin = f"{periodo}-31"

        # Rotación: cantidad de préstamos
        rotacion = conn.execute(text("""
            SELECT COUNT(*) as total
            FROM prestamo p
            JOIN item_existencia ie ON p.item_existencia_id = ie.id
            WHERE ie.sede_id = :sede
              AND p.fecha_prestamo BETWEEN :inicio AND :fin
        """), {"sede": sede, "inicio": inicio, "fin": fin}).scalar()

        # Morosidad: % de préstamos vencidos
        morosos = conn.execute(text("""
            SELECT COUNT(*) 
            FROM prestamo p
            JOIN item_existencia ie ON p.item_existencia_id = ie.id
            WHERE ie.sede_id = :sede
              AND p.estado = 'VENCIDO'
              AND p.fecha_prestamo BETWEEN :inicio AND :fin
        """), {"sede": sede, "inicio": inicio, "fin": fin}).scalar()

        total_prestamos = rotacion if rotacion > 0 else 1
        morosidad = (morosos / total_prestamos) * 100

        # Daños: items dañados
        danos = conn.execute(text("""
            SELECT COUNT(*)
            FROM item_existencia
            WHERE sede_id = :sede
              AND estado = 'DANNADO'
              AND registro_instante BETWEEN :inicio AND :fin
        """), {"sede": sede, "inicio": inicio, "fin": fin}).scalar()

    return {
        "sede": sede,
        "periodo": periodo,
        "rotacion": rotacion,
        "morosidad_porcentaje": round(morosidad, 2),
        "danos": danos
    }
):