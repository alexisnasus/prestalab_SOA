import socket
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import get_db, Multa, Prestamo, Solicitud, Usuario

SERVICE_NAME = "multa"
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
    print(f"[MULTA] Enviando respuesta: {formatted_message!r}")
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

        print(f"[MULTA] Operación: {operation}")
        print(f"[MULTA] Payload: {payload}")

        db_session = next(get_db())

        if operation == "get_multas_usuario":
            return get_multas_usuario(payload, db_session)
        elif operation == "crear_multa":
            return crear_multa(payload, db_session)
        elif operation == "update_bloqueo":
            return actualizar_bloqueo(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[MULTA] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def get_multas_usuario(payload: dict, db: Session):
    """Obtiene las multas de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        
        if not usuario_id:
            return "NK", json.dumps({"error": "Falta campo requerido: usuario_id"})
        
        multas = (
            db.query(Multa)
            .join(Prestamo)
            .join(Solicitud)
            .filter(Solicitud.usuario_id == usuario_id)
            .all()
        )
        
        resultado = [
            {
                "id": m.id,
                "prestamo_id": m.prestamo_id,
                "motivo": m.motivo,
                "valor": m.valor,
                "estado": m.estado,
                "registro_instante": m.registro_instante.isoformat()
            } for m in multas
        ]
        
        return "OK", json.dumps({
            "usuario_id": usuario_id,
            "total": len(resultado),
            "multas": resultado
        })
        
    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": "Error al consultar las multas"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al obtener multas: {str(e)}"})

def crear_multa(payload: dict, db: Session):
    """Crea una nueva multa"""
    try:
        prestamo_id = payload.get("prestamo_id")
        motivo = payload.get("motivo")
        valor = payload.get("valor")
        estado = payload.get("estado")
        
        if not all([prestamo_id, motivo, valor, estado]):
            return "NK", json.dumps({"error": "Faltan campos requeridos: prestamo_id, motivo, valor, estado"})
        
        nueva_multa = Multa(
            prestamo_id=prestamo_id,
            motivo=motivo,
            valor=valor,
            estado=estado,
            registro_instante=datetime.now()
        )
        
        db.add(nueva_multa)
        db.commit()
        db.refresh(nueva_multa)
        
        return "OK", json.dumps({
            "id": nueva_multa.id,
            "message": "Multa registrada con éxito"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        if "foreign key constraint fails" in str(e).lower():
            prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
            if not prestamo:
                return "NK", json.dumps({"error": f"El préstamo con ID {prestamo_id} no existe"})
        return "NK", json.dumps({"error": "Error al registrar la multa"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al crear multa: {str(e)}"})

def actualizar_bloqueo(payload: dict, db: Session):
    """Actualiza el estado de bloqueo de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        estado = payload.get("estado")
        
        if not usuario_id or not estado:
            return "NK", json.dumps({"error": "Faltan campos requeridos: usuario_id, estado"})
        
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            return "NK", json.dumps({"error": "Usuario no encontrado"})
        
        usuario.estado = estado
        db.commit()
        
        return "OK", json.dumps({
            "message": f"Estado del usuario modificado correctamente a {estado}"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": "Error al actualizar el estado del usuario"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al actualizar bloqueo: {str(e)}"})

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
        print(f"[MULTA] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[MULTA] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[MULTA] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[MULTA] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[MULTA] Conexión cerrada por el bus.")
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
            print(f"\n[MULTA] ===== Nueva transacción =====")
            print(f"[MULTA] Datos recibidos: {message_str!r}")
            
            # El bus envía: SSSSS + DATOS, necesitamos solo DATOS
            # Quitar los primeros 5 caracteres (nombre del servicio)
            if len(message_str) > 5:
                message_data = message_str[5:]
            else:
                message_data = message_str
            
            print(f"[MULTA] Datos sin prefijo: {message_data!r}")
            
            # Procesar la solicitud
            status, response_data = handle_request(message_data)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[MULTA] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[MULTA] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[MULTA] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[MULTA] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()
