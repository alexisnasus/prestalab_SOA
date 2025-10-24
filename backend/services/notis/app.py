import socket
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import get_db, Notificacion, Usuario

SERVICE_NAME = "notis"
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
    print(f"[NOTIS] Enviando respuesta: {formatted_message!r}")
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

        print(f"[NOTIS] Operación: {operation}")
        print(f"[NOTIS] Payload: {payload}")

        db_session = next(get_db())

        if operation == "crear_notificacion":
            return crear_notificacion(payload, db_session)
        elif operation == "get_preferencias":
            return obtener_preferencias(payload, db_session)
        elif operation == "update_preferencias":
            return actualizar_preferencias(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[NOTIS] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def crear_notificacion(payload: dict, db: Session):
    """Crea una nueva notificación"""
    try:
        usuario_id = payload.get("usuario_id")
        canal = payload.get("canal")
        tipo = payload.get("tipo")
        mensaje = payload.get("mensaje")
        
        if not all([usuario_id, canal, tipo, mensaje]):
            return "NK", json.dumps({"error": "Faltan campos requeridos: usuario_id, canal, tipo, mensaje"})
        
        # Convertir canal de string a int si es necesario
        # CANAL: 1=PORTAL, 2=WHATSAPP, 3=EMAIL
        if isinstance(canal, str):
            canal_map = {"PORTAL": 1, "WHATSAPP": 2, "EMAIL": 3}
            canal = canal_map.get(canal.upper())
            if canal is None:
                return "NK", json.dumps({"error": "Canal inválido. Debe ser: PORTAL, WHATSAPP o EMAIL (o 1, 2, 3)"})
        
        nueva_notificacion = Notificacion(
            usuario_id=usuario_id,
            canal=canal,
            tipo=tipo,
            mensaje=mensaje,
            registro_instante=datetime.now()
        )
        
        db.add(nueva_notificacion)
        db.commit()
        db.refresh(nueva_notificacion)
        
        return "OK", json.dumps({
            "id": nueva_notificacion.id,
            "message": "Notificación registrada correctamente"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[NOTIS] SQLAlchemyError al crear notificación: {e}")
        if "foreign key constraint fails" in str(e).lower():
            return "NK", json.dumps({"error": f"El usuario con ID {usuario_id} no existe"})
        return "NK", json.dumps({"error": f"Error al registrar la notificación: {str(e)}"})
    except Exception as e:
        print(f"[NOTIS] Exception al crear notificación: {e}")
        return "NK", json.dumps({"error": f"Error al crear notificación: {str(e)}"})

def obtener_preferencias(payload: dict, db: Session):
    """Obtiene las preferencias de notificación de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        
        if not usuario_id:
            return "NK", json.dumps({"error": "Falta campo requerido: usuario_id"})
        
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            return "NK", json.dumps({"error": "Usuario no encontrado"})
        
        return "OK", json.dumps({
            "usuario_id": usuario_id,
            "preferencias_notificacion": usuario.preferencias_notificacion
        })
        
    except SQLAlchemyError as e:
        print(f"[NOTIS] SQLAlchemyError al obtener preferencias: {e}")
        return "NK", json.dumps({"error": f"Error al consultar las preferencias: {str(e)}"})
    except Exception as e:
        print(f"[NOTIS] Exception al obtener preferencias: {e}")
        return "NK", json.dumps({"error": f"Error al obtener preferencias: {str(e)}"})

def actualizar_preferencias(payload: dict, db: Session):
    """Actualiza las preferencias de notificación de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        preferencias_notificacion = payload.get("preferencias_notificacion")
        
        if not usuario_id or preferencias_notificacion is None:
            return "NK", json.dumps({"error": "Faltan campos requeridos: usuario_id, preferencias_notificacion"})
        
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            return "NK", json.dumps({"error": "Usuario no encontrado"})
        
        usuario.preferencias_notificacion = preferencias_notificacion
        db.commit()
        
        return "OK", json.dumps({
            "message": f"Preferencias de notificación del usuario {usuario_id} actualizadas correctamente"
        })
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[NOTIS] SQLAlchemyError al actualizar preferencias: {e}")
        return "NK", json.dumps({"error": f"Error al actualizar las preferencias: {str(e)}"})
    except Exception as e:
        print(f"[NOTIS] Exception al actualizar preferencias: {e}")
        return "NK", json.dumps({"error": f"Error al actualizar preferencias: {str(e)}"})

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
        print(f"[NOTIS] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[NOTIS] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[NOTIS] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[NOTIS] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[NOTIS] Conexión cerrada por el bus.")
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
            print(f"\n[NOTIS] ===== Nueva transacción =====")
            print(f"[NOTIS] Datos recibidos: {message_str!r}")
            
            # El bus envía: SSSSS + DATOS, necesitamos solo DATOS
            # Quitar los primeros 5 caracteres (nombre del servicio)
            if len(message_str) > 5:
                message_data = message_str[5:]
            else:
                message_data = message_str

            print(f"[NOTIS] Datos sin prefijo: {message_data!r}")

            # Procesar la solicitud
            status, response_data = handle_request(message_data)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[NOTIS] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[NOTIS] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[NOTIS] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[NOTIS] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()