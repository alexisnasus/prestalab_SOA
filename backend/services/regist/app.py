import socket
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models import Usuario, Solicitud, get_db

SERVICE_NAME = "regis"
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
    print(f"[REGIS] Enviando respuesta: {formatted_message!r}")
    sock.sendall(formatted_message)

def handle_request(data: str):
    """
    Procesa el request y llama a la función de negocio correspondiente.
    Formato esperado: OPERACION {json_payload}
    Ejemplo: register {"nombre":"Juan","correo":"juan@mail.com","password":"123","tipo":"ESTUDIANTE"}
    """
    try:
        parts = data.split(' ', 1)
        operation = parts[0]
        payload_str = parts[1] if len(parts) > 1 else '{}'
        payload = json.loads(payload_str)

        print(f"[REGIS] Operación: {operation}")
        print(f"[REGIS] Payload: {payload}")

        db_session = next(get_db())

        if operation == "register":
            return registrar_usuario(payload, db_session)
        elif operation == "login":
            return login(payload, db_session)
        elif operation == "get_user":
            return consultar_usuario(payload, db_session)
        elif operation == "update_user":
            return actualizar_usuario(payload, db_session)
        elif operation == "update_solicitud":
            return actualizar_solicitud_registro(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[REGIS] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def registrar_usuario(data: dict, db: Session):
    try:
        nuevo_usuario = Usuario(
            nombre=data["nombre"],
            correo=data["correo"].lower(),
            tipo=data["tipo"],
            telefono=data.get("telefono", ""),
            estado=data.get("estado", "ACTIVO"),
            preferencias_notificacion=data.get("preferencias_notificacion", 1),
            registro_instante=datetime.now()
        )
        nuevo_usuario.set_password(data["password"])
        if data.get("id"):
            nuevo_usuario.id = data["id"]
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        response_data = {"message": "Usuario registrado", "user": nuevo_usuario.to_dict()}
        return "OK", json.dumps(response_data)
        
    except IntegrityError:
        db.rollback()
        return "NK", json.dumps({"error": "El correo ya está registrado"})
    except (SQLAlchemyError, KeyError) as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error en la base de datos o datos incompletos: {str(e)}"})

def login(auth: dict, db: Session):
    correo = auth["correo"].lower()
    user = db.query(Usuario).filter(Usuario.correo == correo).first()
    
    if not user or not user.check_password(auth["password"]):
        return "NK", json.dumps({"error": "Credenciales inválidas"})

    user_data = user.to_dict()
    token = f"session-{user_data['id']}"
    response_data = {"message": f"Usuario {correo} autenticado", "token": token, "user": user_data}
    return "OK", json.dumps(response_data)

def consultar_usuario(payload: dict, db: Session):
    user_id = payload.get("id")
    if not user_id:
        return "NK", json.dumps({"error": "ID de usuario no proporcionado"})
        
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        return "NK", json.dumps({"error": "Usuario no encontrado"})
        
    return "OK", json.dumps(user.to_dict())

def actualizar_usuario(payload: dict, db: Session):
    user_id = payload.get("id")
    datos = payload.get("datos")
    if not user_id or not datos:
        return "NK", json.dumps({"error": "Faltan 'id' o 'datos' para actualizar"})

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        return "NK", json.dumps({"error": "Usuario no encontrado"})
    
    try:
        for key, value in datos.items():
            if key == "password":
                user.set_password(value)
            elif hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return "OK", json.dumps({"message": f"Usuario {user_id} actualizado"})
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al actualizar: {str(e)}"})

def actualizar_solicitud_registro(payload: dict, db: Session):
    solicitud_id = payload.get("solicitud_id")
    nuevo_estado = payload.get("estado")

    if not solicitud_id or not nuevo_estado or nuevo_estado not in ["APROBADA", "RECHAZADA"]:
        return "NK", json.dumps({"error": "Faltan datos o el estado es inválido"})

    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        return "NK", json.dumps({"error": "Solicitud no encontrada"})
    
    if solicitud.estado != "PENDIENTE":
        return "NK", json.dumps({"error": f"La solicitud ya fue procesada (estado: {solicitud.estado})"})

    try:
        solicitud.estado = nuevo_estado
        db.commit()
        db.refresh(solicitud)
        response = {"message": f"Solicitud {solicitud_id} actualizada a {nuevo_estado}"}
        return "OK", json.dumps(response)
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al actualizar solicitud: {str(e)}"})

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
        print(f"[REGIS] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[REGIS] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro (NNNNNNOK o similar)
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[REGIS] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[REGIS] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[REGIS] Conexión cerrada por el bus.")
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
            print(f"\n[REGIS] ===== Nueva transacción =====")
            print(f"[REGIS] Datos recibidos: {message_str!r}")
            
            # Procesar la solicitud (los datos vienen directamente, sin prefijo de cliente)
            status, response_data = handle_request(message_str)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[REGIS] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[REGIS] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[REGIS] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()
