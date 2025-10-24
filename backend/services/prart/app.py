import socket
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from models import (
    get_db, Item, Usuario, Solicitud, ItemSolicitud, Prestamo, Ventana, ItemExistencia
)

SERVICE_NAME = "prart"
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
    print(f"[PRART] Enviando respuesta: {formatted_message!r}")
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

        print(f"[PRART] Operación: {operation}")
        print(f"[PRART] Payload: {payload}")

        db_session = next(get_db())

        if operation == "get_all_items":
            return obtener_todos_los_items(db_session)
        elif operation == "search_items":
            return buscar_items(payload, db_session)
        elif operation == "get_solicitudes":
            return obtener_solicitudes_usuario(payload, db_session)
        elif operation == "create_solicitud":
            return crear_solicitud(payload, db_session)
        elif operation == "create_reserva":
            return crear_reserva(payload, db_session)
        elif operation == "cancel_reserva":
            return cancelar_reserva(payload, db_session)
        elif operation == "create_prestamo":
            return registrar_prestamo(payload, db_session)
        elif operation == "create_devolucion":
            return registrar_devolucion(payload, db_session)
        elif operation == "renovar_prestamo":
            return renovar_prestamo(payload, db_session)
        elif operation == "update_item_estado":
            return actualizar_estado(payload, db_session)
        else:
            return "NK", json.dumps({"error": f"Operación desconocida: {operation}"})

    except json.JSONDecodeError:
        return "NK", json.dumps({"error": "Payload no es un JSON válido"})
    except IndexError:
        return "NK", json.dumps({"error": "Formato inválido. Use: OPERACION {json_payload}"})
    except Exception as e:
        print(f"[PRART] Error inesperado: {e}")
        return "NK", json.dumps({"error": f"Error interno: {str(e)}"})

# --- Lógica de Negocio ---

def obtener_todos_los_items(db: Session):
    """Obtiene todos los artículos del catálogo sin filtros"""
    try:
        items = db.query(Item).order_by(Item.nombre).all()
        items_data = [
            {
                "id": item.id,
                "nombre": item.nombre,
                "tipo": item.tipo,
                "descripcion": item.descripcion,
                "cantidad": item.cantidad,
                "cantidad_max": item.cantidad_max,
                "valor": float(item.valor),
                "tarifa_atraso": float(item.tarifa_atraso)
            }
            for item in items
        ]
        return "OK", json.dumps({"total": len(items_data), "items": items_data})
    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": f"Error al obtener items: {str(e)}"})

def buscar_items(payload: dict, db: Session):
    """Busca artículos con filtros opcionales"""
    try:
        nombre = payload.get("nombre")
        tipo = payload.get("tipo")
        
        query = db.query(Item)
        if nombre:
            query = query.filter(Item.nombre.like(f"%{nombre}%"))
        if tipo:
            query = query.filter(Item.tipo == tipo)
        
        items = query.all()
        items_data = [
            {
                "id": item.id,
                "nombre": item.nombre,
                "tipo": item.tipo,
                "descripcion": item.descripcion,
                "cantidad": item.cantidad,
                "cantidad_max": item.cantidad_max,
                "valor": float(item.valor),
                "tarifa_atraso": float(item.tarifa_atraso)
            }
            for item in items
        ]
        return "OK", json.dumps({"total": len(items_data), "items": items_data})
    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": f"Error al buscar items: {str(e)}"})

def crear_reserva(payload: dict, db: Session):
    """Crea una reserva (ventana de tiempo para un préstamo)"""
    try:
        solicitud_id = payload.get("solicitud_id")
        item_existencia_id = payload.get("item_existencia_id")
        inicio_str = payload.get("inicio")
        fin_str = payload.get("fin")
        
        if not all([solicitud_id, item_existencia_id, inicio_str, fin_str]):
            return "NK", json.dumps({"error": "Faltan campos requeridos"})
        
        inicio = datetime.fromisoformat(inicio_str.replace('Z', '+00:00'))
        fin = datetime.fromisoformat(fin_str.replace('Z', '+00:00'))
        
        if fin <= inicio:
            return "NK", json.dumps({"error": "La fecha de fin debe ser mayor a la fecha de inicio"})

        nueva_reserva = Ventana(
            solicitud_id=solicitud_id,
            item_existencia_id=item_existencia_id,
            inicio=inicio,
            fin=fin
        )
        db.add(nueva_reserva)
        db.commit()
        db.refresh(nueva_reserva)
        
        return "OK", json.dumps({
            "message": "Reserva creada exitosamente",
            "reserva_id": nueva_reserva.id
        })
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al crear la reserva: {str(e)}"})

def cancelar_reserva(payload: dict, db: Session):
    """Cancela una reserva"""
    try:
        reserva_id = payload.get("reserva_id")
        if not reserva_id:
            return "NK", json.dumps({"error": "Falta reserva_id"})
        
        reserva = db.query(Ventana).filter(Ventana.id == reserva_id).first()
        if not reserva:
            return "NK", json.dumps({"error": "Reserva no encontrada"})
        
        db.delete(reserva)
        db.commit()
        
        return "OK", json.dumps({"message": "Reserva cancelada"})
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al cancelar la reserva: {str(e)}"})

def obtener_solicitudes_usuario(payload: dict, db: Session):
    """Obtiene las solicitudes de un usuario"""
    try:
        usuario_id = payload.get("usuario_id")
        correo = payload.get("correo")

        if not usuario_id and not correo:
            return "NK", json.dumps({"error": "Debe proporcionar 'usuario_id' o 'correo'"})

        user_query = db.query(Usuario)
        if usuario_id and correo:
            user = user_query.filter(Usuario.id == usuario_id, func.lower(Usuario.correo) == correo.lower()).first()
            if not user:
                return "NK", json.dumps({"error": "El usuario_id no coincide con el correo proporcionado"})
        elif usuario_id:
            user = user_query.filter(Usuario.id == usuario_id).first()
        else:
            user = user_query.filter(func.lower(Usuario.correo) == correo.lower()).first()

        if not user:
            return "NK", json.dumps({"error": "Usuario no encontrado"})

        solicitudes = db.query(Solicitud).filter(Solicitud.usuario_id == user.id)\
            .options(
                joinedload(Solicitud.items).joinedload(ItemSolicitud.item),
                joinedload(Solicitud.prestamos).joinedload(Prestamo.item_existencia).joinedload(ItemExistencia.item),
                joinedload(Solicitud.ventanas).joinedload(Ventana.item_existencia).joinedload(ItemExistencia.item)
            ).order_by(Solicitud.registro_instante.desc()).all()

        response_data = []
        for s in solicitudes:
            item_nombres = set()
            for item_sol in s.items:
                item_nombres.add(item_sol.item.nombre)
            for prestamo in s.prestamos:
                item_nombres.add(prestamo.item_existencia.item.nombre)
            for ventana in s.ventanas:
                item_nombres.add(ventana.item_existencia.item.nombre)

            response_data.append({
                "id": s.id,
                "usuario_id": s.usuario_id,
                "tipo": s.tipo,
                "estado": s.estado,
                "registro_instante": s.registro_instante.isoformat(),
                "items": [{"nombre": nombre} for nombre in item_nombres]
            })
        
        respuesta = {
            "usuario_id": user.id,
            "total": len(response_data),
            "solicitudes": response_data
        }
        
        return "OK", json.dumps(respuesta)

    except SQLAlchemyError as e:
        return "NK", json.dumps({"error": f"Error al obtener solicitudes: {str(e)}"})

def crear_solicitud(payload: dict, db: Session):
    """Crea una solicitud de préstamo"""
    try:
        usuario_id = payload.get("usuario_id")
        correo = payload.get("correo")
        tipo = payload.get("tipo")

        if not tipo:
            return "NK", json.dumps({"error": "Falta el campo 'tipo'"})

        if not usuario_id and not correo:
            return "NK", json.dumps({"error": "Debe proporcionar 'usuario_id' o 'correo'"})

        user_query = db.query(Usuario)
        if usuario_id and correo:
            user = user_query.filter(Usuario.id == usuario_id, func.lower(Usuario.correo) == correo.lower()).first()
            if not user:
                return "NK", json.dumps({"error": "El usuario_id no coincide con el correo proporcionado"})
        elif usuario_id:
            user = user_query.filter(Usuario.id == usuario_id).first()
        else:
            user = user_query.filter(func.lower(Usuario.correo) == correo.lower()).first()
        
        if not user:
            return "NK", json.dumps({"error": "Usuario no encontrado"})

        nueva_solicitud = Solicitud(
            usuario_id=user.id,
            tipo=tipo,
            estado='PENDIENTE',
            registro_instante=datetime.now()
        )
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)

        response_payload = {
            "message": "Solicitud creada exitosamente",
            "solicitud_id": nueva_solicitud.id,
            "usuario_id": user.id
        }
        
        return "OK", json.dumps(response_payload)
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al crear la solicitud: {str(e)}"})

def registrar_prestamo(payload: dict, db: Session):
    """Registra un nuevo préstamo"""
    try:
        solicitud_id = payload.get("solicitud_id")
        item_existencia_id = payload.get("item_existencia_id")
        comentario = payload.get("comentario")
        
        if not solicitud_id or not item_existencia_id:
            return "NK", json.dumps({"error": "Faltan campos requeridos"})
        
        fecha_prestamo = datetime.now()
        nuevo_prestamo = Prestamo(
            item_existencia_id=item_existencia_id,
            solicitud_id=solicitud_id,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion=fecha_prestamo + timedelta(days=30),
            estado='ACTIVO',
            renovaciones_realizadas=0,
            registro_instante=datetime.now(),
            comentario=comentario
        )
        db.add(nuevo_prestamo)
        db.commit()
        db.refresh(nuevo_prestamo)
        
        return "OK", json.dumps({
            "message": "Préstamo registrado",
            "prestamo_id": nuevo_prestamo.id
        })
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al registrar el préstamo: {str(e)}"})

def registrar_devolucion(payload: dict, db: Session):
    """Registra la devolución de un préstamo"""
    try:
        prestamo_id = payload.get("prestamo_id")
        comentario = payload.get("comentario")
        
        if not prestamo_id:
            return "NK", json.dumps({"error": "Falta prestamo_id"})
        
        prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
        if not prestamo:
            return "NK", json.dumps({"error": "Préstamo no encontrado"})
        
        prestamo.estado = 'DEVUELTO'
        prestamo.comentario = comentario
        prestamo.fecha_devolucion = datetime.now()
        db.commit()
        
        return "OK", json.dumps({"message": "Devolución registrada"})
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al registrar la devolución: {str(e)}"})

def renovar_prestamo(payload: dict, db: Session):
    """Renueva un préstamo existente"""
    try:
        prestamo_id = payload.get("prestamo_id")
        
        if not prestamo_id:
            return "NK", json.dumps({"error": "Falta prestamo_id"})
        
        prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
        if not prestamo:
            return "NK", json.dumps({"error": "Préstamo no encontrado"})

        prestamo.renovaciones_realizadas += 1
        prestamo.fecha_prestamo = datetime.now()
        prestamo.fecha_devolucion = datetime.now() + timedelta(days=30)
        prestamo.comentario = 'Préstamo renovado'
        prestamo.estado = 'ACTIVO'
        db.commit()
        
        return "OK", json.dumps({
            "message": "Préstamo renovado",
            "renovaciones": prestamo.renovaciones_realizadas
        })
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al renovar el préstamo: {str(e)}"})

def actualizar_estado(payload: dict, db: Session):
    """Actualiza el estado de un item de existencia"""
    try:
        existencia_id = payload.get("existencia_id")
        estado = payload.get("estado")
        
        if not existencia_id or not estado:
            return "NK", json.dumps({"error": "Faltan campos requeridos"})
        
        item_existencia = db.query(ItemExistencia).filter(ItemExistencia.id == existencia_id).first()
        if not item_existencia:
            return "NK", json.dumps({"error": "Ítem no encontrado"})
        
        item_existencia.estado = estado
        db.commit()
        
        return "OK", json.dumps({"message": f"Estado actualizado a {estado}"})
    except SQLAlchemyError as e:
        db.rollback()
        return "NK", json.dumps({"error": f"Error al actualizar el estado: {str(e)}"})

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
        print(f"[PRART] Conectando al bus en {BUS_ADDRESS}...")
        sock.connect(BUS_ADDRESS)

        # Registrar el servicio usando sinit
        init_message = f"sinit{SERVICE_NAME}"
        init_message_len = len(init_message)
        formatted_init_message = f"{init_message_len:05d}{init_message}".encode('utf-8')
        print(f"[PRART] Registrando servicio: {formatted_init_message!r}")
        sock.sendall(formatted_init_message)

        # Esperar confirmación de registro
        length_bytes = sock.recv(5)
        if length_bytes:
            amount_expected = int(length_bytes.decode('utf-8'))
            confirmation = sock.recv(amount_expected).decode('utf-8')
            print(f"[PRART] Confirmación recibida: {confirmation!r}")

        # Bucle principal: escuchar transacciones
        print(f"[PRART] Servicio '{SERVICE_NAME}' listo. Esperando transacciones...\n")
        
        while True:
            # Leer longitud del mensaje (5 dígitos)
            length_bytes = sock.recv(5)
            if not length_bytes:
                print("[PRART] Conexión cerrada por el bus.")
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
            print(f"\n[PRART] ===== Nueva transacción =====")
            print(f"[PRART] Datos recibidos: {message_str!r}")
            
            # El bus envía: SSSSS + DATOS, necesitamos solo DATOS
            # Quitar los primeros 5 caracteres (nombre del servicio)
            if len(message_str) > 5:
                message_data = message_str[5:]
            else:
                message_data = message_str
            
            print(f"[PRART] Datos sin prefijo: {message_data!r}")
            
            # Procesar la solicitud
            status, response_data = handle_request(message_data)
            
            # Enviar respuesta al bus
            send_response(sock, status, response_data)
            print(f"[PRART] Respuesta enviada con status: {status}")

    except ConnectionRefusedError:
        print("[PRART] ERROR: No se pudo conectar al bus. Verifique que esté corriendo.")
    except Exception as e:
        print(f"[PRART] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[PRART] Cerrando socket.")
        sock.close()

if __name__ == "__main__":
    main()