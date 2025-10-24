import socket
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import ListaEspera, get_db, Item, Solicitud

SERVICE_NAME = "lista"
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
    print(f"[LISTA] Enviando respuesta: {formatted_message!r}")
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

        print(f"[LISTA] Operación: {operation}")
        print(f"[LISTA] Payload: {payload}")

        db_session = next(get_db())

        if operation == "create_lista_espera":
            return agregar_lista_espera(payload, db_session)
        elif operation == "update_lista_espera":
            return actualizar_estado_lista_espera(payload, db_session)
        elif operation == "get_lista_espera":
            return obtener_lista_por_item(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[LISTA] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def agregar_lista_espera(payload: dict, db: Session):
    """Agrega un usuario a la lista de espera de un artículo"""
    try:
        solicitud_id = payload.get("solicitud_id")
        item_id = payload.get("item_id")
        estado = payload.get("estado", "EN ESPERA")
        
        if not solicitud_id or not item_id:
            return "NK", json.dumps({"error": "Faltan campos requeridos: solicitud_id, item_id"})
        
        now = datetime.now()
        
        nuevo_registro = ListaEspera(
            solicitud_id=solicitud_id,
            item_id=item_id,
            fecha_ingreso=now,
            estado=estado,
            registro_instante=now
        )
        
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        response_data = {
            "message": "Registro agregado exitosamente",
            "id": nuevo_registro.id,
            "solicitud_id": solicitud_id,
            "item_id": item_id,
            "fecha_ingreso": now.isoformat(),
            "estado": estado
        }
        
        return "OK", json.dumps(response_data)
        
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = str(e)
        
        # Verificar si es una violación de llave foránea
        if "foreign key constraint fails" in error_msg.lower():
            # Verificar si el item_id existe
            item = db.query(Item).filter(Item.id == item_id).first()
            if not item:
                return "NK", json.dumps({"error": f"El item con ID {item_id} no existe"})
            # Verificar si la solicitud_id existe
            solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
            if not solicitud:
                return "NK", json.dumps({"error": f"La solicitud con ID {solicitud_id} no existe"})
        
        return "NK", json.dumps({"error": f"Error al interactuar con la base de datos: {error_msg}"})

def actualizar_estado_lista_espera(payload: dict, db: Session):
    """Actualiza el estado de un registro en la lista de espera"""
    try:
        id_registro = payload.get("id")
        nuevo_estado = payload.get("estado")
        
        if not id_registro or not nuevo_estado:
            return "NK", json.dumps({"error": "Faltan campos requeridos: id, estado"})
        
        nuevo_estado_upper = nuevo_estado.upper().strip()
        if nuevo_estado_upper not in ("ATENDIDA", "CANCELADA"):
            return "NK", json.dumps({"error": "El estado debe ser 'ATENDIDA' o 'CANCELADA'"})

        registro = db.query(ListaEspera).filter(ListaEspera.id == id_registro).first()
        
        if not registro:
            return "NK", json.dumps({"error": "Registro no encontrado"})
            
        registro.estado = nuevo_estado_upper
        registro.registro_instante = datetime.now()
        
        db.commit()
        
        response_data = {
            "message": f"Registro {id_registro} actualizado correctamente a {nuevo_estado_upper}",
            "id": id_registro,
            "nuevo_estado": nuevo_estado_upper
        }
        
        return "OK", json.dumps(response_data)
        
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al actualizar el registro: {str(e)}"})

def obtener_lista_por_item(payload: dict, db: Session):
    """Obtiene la lista de espera de un artículo específico"""
    try:
        item_id = payload.get("item_id")
        
        if not item_id:
            return "NK", json.dumps({"error": "Falta campo requerido: item_id"})
        
        registros = db.query(ListaEspera).filter(
            ListaEspera.item_id == item_id
        ).order_by(ListaEspera.fecha_ingreso.asc()).all()
        
        if not registros:
            return "NK", json.dumps({"error": "No se encontraron registros para este ítem"})
            
        resultado = [
            {
                "id": r.id,
                "solicitud_id": r.solicitud_id,
                "item_id": r.item_id,
                "fecha_ingreso": r.fecha_ingreso.isoformat(),
                "estado": r.estado,
                "registro_instante": r.registro_instante.isoformat()
            } for r in registros
        ]
        
        response_data = {
            "item_id": item_id,
            "total": len(resultado),
            "registros": resultado
        }
        
        return "OK", json.dumps(response_data)
        
    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": f"Error al consultar la base de datos: {str(e)}"})

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
        print(f"[LISTA] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[LISTA] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[LISTA] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[LISTA] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[LISTA] Conexión cerrada por el bus.")
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
            print(f"\n[LISTA] ===== Nueva transacción =====")
            print(f"[LISTA] Datos recibidos: {message_str!r}")
            
            # El bus envía: SSSSS + DATOS, necesitamos solo DATOS
            # Quitar los primeros 5 caracteres (nombre del servicio)
            if len(message_str) > 5:
                message_data = message_str[5:]
            else:
                message_data = message_str
            
            print(f"[LISTA] Datos sin prefijo: {message_data!r}")
            
            # Procesar la solicitud
            status, response_data = handle_request(message_data)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[LISTA] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[LISTA] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[LISTA] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[LISTA] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()
