import socket
import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Sugerencia, Usuario, get_db

SERVICE_NAME = "sugit"
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
    print(f"[SUGIT] Enviando respuesta: {formatted_message!r}")
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

        print(f"[SUGIT] Operación: {operation}")
        print(f"[SUGIT] Payload: {payload}")

        db_session = next(get_db())

        if operation == "registrar_sugerencia":
            return registrar_sugerencia(payload, db_session)
        elif operation == "listar_sugerencias":
            return listar_sugerencias(payload, db_session)
        elif operation == "aprobar_sugerencia":
            return aprobar_sugerencia(payload, db_session)
        elif operation == "rechazar_sugerencia":
            return rechazar_sugerencia(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[SUGIT] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def registrar_sugerencia(payload: dict, db: Session):
    """Registra una nueva sugerencia"""
    try:
        usuario_id = payload.get("usuario_id")
        sugerencia_texto = payload.get("sugerencia")
        
        if not usuario_id or not sugerencia_texto:
            return "NK", json.dumps({"error": "Faltan campos requeridos: usuario_id, sugerencia"})
        
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return "NK", json.dumps({"error": "Usuario no encontrado"})
        
        # Crear nueva sugerencia
        nueva_sugerencia = Sugerencia(
            usuario_id=usuario_id,
            sugerencia=sugerencia_texto,
            estado='PENDIENTE'
        )
        
        db.add(nueva_sugerencia)
        db.commit()
        db.refresh(nueva_sugerencia)
        
        return "OK", json.dumps({
            "id": nueva_sugerencia.id,
            "message": "Sugerencia registrada"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": "Error al registrar sugerencia"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al registrar sugerencia: {str(e)}"})

def listar_sugerencias(payload: dict, db: Session):
    """Lista todas las sugerencias"""
    try:
        sugerencias = db.query(Sugerencia).all()
        
        data = [
            {
                "id": s.id,
                "usuario_id": s.usuario_id,
                "sugerencia": s.sugerencia,
                "estado": s.estado,
                "registro_instante": s.registro_instante.isoformat() if s.registro_instante else None
            }
            for s in sugerencias
        ]
        
        return "OK", json.dumps({
            "total": len(data),
            "sugerencias": data
        })
        
    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": "Error al listar sugerencias"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al listar sugerencias: {str(e)}"})

def aprobar_sugerencia(payload: dict, db: Session):
    """Aprueba una sugerencia"""
    try:
        sugerencia_id = payload.get("id")
        
        if not sugerencia_id:
            return "NK", json.dumps({"error": "Falta campo requerido: id"})
        
        sugerencia = db.query(Sugerencia).filter(Sugerencia.id == sugerencia_id).first()
        
        if not sugerencia:
            return "NK", json.dumps({"error": "Sugerencia no encontrada"})
        
        sugerencia.estado = 'ACEPTADA'
        db.commit()
        db.refresh(sugerencia)
        
        return "OK", json.dumps({
            "id": sugerencia_id,
            "message": "Sugerencia aprobada"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": "Error al aprobar sugerencia"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al aprobar sugerencia: {str(e)}"})

def rechazar_sugerencia(payload: dict, db: Session):
    """Rechaza una sugerencia"""
    try:
        sugerencia_id = payload.get("id")
        
        if not sugerencia_id:
            return "NK", json.dumps({"error": "Falta campo requerido: id"})
        
        sugerencia = db.query(Sugerencia).filter(Sugerencia.id == sugerencia_id).first()
        
        if not sugerencia:
            return "NK", json.dumps({"error": "Sugerencia no encontrada"})
        
        sugerencia.estado = 'RECHAZADA'
        db.commit()
        db.refresh(sugerencia)
        
        return "OK", json.dumps({
            "id": sugerencia_id,
            "message": "Sugerencia rechazada"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": "Error al rechazar sugerencia"})
    except Exception as e:
        return "NK", json.dumps({"error": f"Error al rechazar sugerencia: {str(e)}"})

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
        print(f"[SUGIT] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[SUGIT] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[SUGIT] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[SUGIT] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[SUGIT] Conexión cerrada por el bus.")
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
            print(f"\n[SUGIT] ===== Nueva transacción =====")
            print(f"[SUGIT] Datos recibidos: {message_str!r}")
            
            # El bus envía: SSSSS + DATOS, necesitamos solo DATOS
            # Quitar los primeros 5 caracteres (nombre del servicio)
            if len(message_str) > 5:
                message_data = message_str[5:]
            else:
                message_data = message_str
            
            print(f"[SUGIT] Datos sin prefijo: {message_data!r}")
            
            # Procesar la solicitud
            status, response_data = handle_request(message_data)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[SUGIT] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[SUGIT] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[SUGIT] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[SUGIT] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()