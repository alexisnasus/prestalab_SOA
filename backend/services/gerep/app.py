import socket
import json
import io
import csv
import base64
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from reportlab.pdfgen import canvas
from models import Prestamo, Solicitud, ItemExistencia, Item, Sede, get_db, engine

SERVICE_NAME = "gerep"
BUS_ADDRESS = ('bus', 5000)

def send_response(sock, status, data):
    """
    Envía una respuesta al bus siguiendo el protocolo:
    NNNNNSSSSSSTDATOS
    donde:
    - NNNNN: longitud de lo que sigue (5 dígitos)
    - SSSSS: nombre del servicio (5 caracteres, padded)
    - ST: status OK o NK (2 caracteres)
    - DATOS: datos de respuesta
    """
    service_padded = SERVICE_NAME.ljust(5)[:5]
    message = f"{service_padded}{status}{data}"
    message_len = len(message)
    formatted_message = f"{message_len:05d}{message}".encode('utf-8')
    print(f"[GEREP] Enviando respuesta: {formatted_message!r}")
    sock.sendall(formatted_message)

def handle_request(data: str):
    """
    Procesa el request y llama a la función de negocio correspondiente.
    Formato esperado: OPERACION {json_payload}
    """
    try:
        parts = data.split(' ', 1)
        operation = parts[0]
        payload_str = parts[1] if len(parts) > 1 else '{}'
        payload = json.loads(payload_str)

        print(f"[GEREP] Operación: {operation}")
        print(f"[GEREP] Payload: {payload}")

        db_session = next(get_db())

        if operation == "get_historial":
            return historial_usuario(payload, db_session)
        elif operation == "get_reporte_circulacion":
            return reportes_circulacion(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[GEREP] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def historial_usuario(payload: dict, db: Session):
    """Obtiene el historial de préstamos de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        formato = payload.get("formato", "json")
        
        if not usuario_id:
            return "NK", json.dumps({"error": "Falta campo requerido: usuario_id"})
        
        if formato not in ["json", "csv", "pdf"]:
            return "NK", json.dumps({"error": "Formato no soportado. Use: json, csv o pdf"})

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

        if formato == "json":
            return "OK", json.dumps({
                "usuario_id": usuario_id,
                "total": len(historial),
                "historial": historial
            })

        elif formato == "csv":
            if not historial:
                return "NK", json.dumps({"error": "No se encontró historial para este usuario"})
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=historial[0].keys())
            writer.writeheader()
            writer.writerows(historial)
            csv_content = output.getvalue()
            
            # Codificar en base64 para transmitir como JSON
            csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
            
            return "OK", json.dumps({
                "usuario_id": usuario_id,
                "formato": "csv",
                "filename": f"historial_{usuario_id}.csv",
                "content": csv_base64
            })

        elif formato == "pdf":
            if not historial:
                return "NK", json.dumps({"error": "No se encontró historial para este usuario"})
            
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
            pdf_content = buffer.getvalue()
            
            # Codificar en base64 para transmitir como JSON
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            return "OK", json.dumps({
                "usuario_id": usuario_id,
                "formato": "pdf",
                "filename": f"historial_{usuario_id}.pdf",
                "content": pdf_base64
            })

    except Exception as e:
        return "NK", json.dumps({"error": f"Error al obtener historial: {str(e)}"})

def reportes_circulacion(payload: dict, db: Session):
    """Genera reporte de circulación por sede y período"""
    try:
        periodo = payload.get("periodo")
        sede_id = payload.get("sede_id")
        
        if not periodo or not sede_id:
            return "NK", json.dumps({"error": "Faltan campos requeridos: periodo, sede_id"})
        
        try:
            inicio = datetime.strptime(f"{periodo}-01", "%Y-%m-%d")
            fin_mes = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            fin = fin_mes
        except ValueError:
            return "NK", json.dumps({"error": "Formato de período inválido. Use YYYY-MM"})

        # Rotación (total de préstamos en el período)
        rotacion = (
            db.query(func.count(Prestamo.id))
            .join(ItemExistencia)
            .filter(ItemExistencia.sede_id == sede_id, Prestamo.fecha_prestamo.between(inicio, fin))
            .scalar()
        )

        # Morosidad (préstamos vencidos)
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

        # Daños reportados
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
        
        return "OK", json.dumps(response_data)
        
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al generar reporte: {str(e)}"})

# --- Main Loop ---

def main():
    """
    Función principal del servicio.
    1. Conecta al bus
    2. Se registra como servicio usando sinit
    3. Escucha transacciones en un bucle infinito
    4. Procesa cada transacción y responde
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"[GEREP] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[GEREP] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[GEREP] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[GEREP] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[GEREP] Conexión cerrada por el bus.")
                break
            
            amount_expected = int(length_bytes.decode('utf-8'))
            
            # Leer el mensaje completo
            data_received = b''
            while len(data_received) < amount_expected:
                chunk = sock.recv(amount_expected - len(data_received))
                if not chunk:
                    break
                data_received += chunk
            
            message_str = data_received.decode('utf-8')
            print(f"\n[GEREP] ===== Nueva transacción =====")
            print(f"[GEREP] Datos recibidos: {message_str!r}")
            
            # Procesar la solicitud
            status, response_data = handle_request(message_str)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[GEREP] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[GEREP] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[GEREP] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[GEREP] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()