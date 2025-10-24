#!/usr/bin/env python3
"""
Cliente interactivo para el servicio PRART (Préstamos y Artículos)
Sistema PrestaLab SOA
"""

import socket
import json
from datetime import datetime, timedelta

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "prart"

def send_request(operation, payload):
    """Envía una solicitud al bus y retorna la respuesta"""
    service_padded = SERVICE_NAME.ljust(5)[:5]
    data = f"{operation} {json.dumps(payload)}"
    message = f"{service_padded}{data}"
    message_len = len(message)
    formatted_message = f"{message_len:05d}{message}".encode('utf-8')
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(BUS_ADDRESS)
        sock.sendall(formatted_message)
        
        length_bytes = sock.recv(5)
        if not length_bytes:
            return None, None
        
        amount_expected = int(length_bytes.decode('utf-8'))
        data_received = b''
        while len(data_received) < amount_expected:
            chunk = sock.recv(amount_expected - len(data_received))
            if not chunk:
                break
            data_received += chunk
        
        response_str = data_received.decode('utf-8')
        status = response_str[5:7]
        response_data = response_str[7:]
        
        return status, json.loads(response_data)
    except Exception as e:
        return None, None
    finally:
        sock.close()

def print_response(status, data):
    """Imprime la respuesta del servicio"""
    pass  # No mostrar respuesta - ver logs en soa_bus

def op_get_all_items():
    """Obtener todos los items del catálogo"""
    print("\n--- OBTENER TODOS LOS ITEMS ---")
    
    payload = {}
    
    status, data = send_request("get_all_items", payload)
    print("✅ Solicitud enviada")

def op_search_items():
    """Buscar items con filtros"""
    print("\n--- BUSCAR ITEMS ---")
    print("Ingrese los filtros de búsqueda (Enter para omitir):")
    
    payload = {}
    nombre = input("  Nombre: ")
    if nombre:
        payload["nombre"] = nombre
    tipo = input("  Tipo (LIBRO/REVISTA/TESIS/OTRO): ")
    if tipo:
        payload["tipo"] = tipo.upper()
    
    status, data = send_request("search_items", payload)
    print("✅ Solicitud enviada")

def op_get_solicitudes():
    """Obtener solicitudes de un usuario"""
    print("\n--- OBTENER SOLICITUDES DE USUARIO ---")
    usuario_id = input("ID del usuario: ")
    
    payload = {"usuario_id": int(usuario_id)}
    
    status, data = send_request("get_solicitudes", payload)
    print("✅ Solicitud enviada")

def op_create_solicitud():
    """Crear una nueva solicitud"""
    print("\n--- CREAR SOLICITUD ---")
    usuario_id = input("ID del usuario: ")
    print("Ingrese los IDs de los items (separados por coma): ")
    items_input = input("Items: ")
    items_ids = [int(x.strip()) for x in items_input.split(',') if x.strip()]
    
    payload = {
        "usuario_id": int(usuario_id),
        "items": items_ids
    }
    
    status, data = send_request("create_solicitud", payload)
    print("✅ Solicitud enviada")

def op_create_reserva():
    """Crear una reserva (ventana de tiempo)"""
    print("\n--- CREAR RESERVA ---")
    solicitud_id = input("ID de la solicitud: ")
    item_existencia_id = input("ID de la existencia del item: ")
    
    print("\nFecha de inicio (formato: YYYY-MM-DD HH:MM:SS)")
    inicio_str = input("Inicio: ")
    print("Fecha de fin (formato: YYYY-MM-DD HH:MM:SS)")
    fin_str = input("Fin: ")
    
    # Convertir a formato ISO
    try:
        inicio = datetime.strptime(inicio_str, "%Y-%m-%d %H:%M:%S").isoformat()
        fin = datetime.strptime(fin_str, "%Y-%m-%d %H:%M:%S").isoformat()
    except ValueError:
        print("❌ Formato de fecha inválido")
        return
    
    payload = {
        "solicitud_id": int(solicitud_id),
        "item_existencia_id": int(item_existencia_id),
        "inicio": inicio,
        "fin": fin
    }
    
    status, data = send_request("create_reserva", payload)
    print("✅ Solicitud enviada")

def op_cancel_reserva():
    """Cancelar una reserva"""
    print("\n--- CANCELAR RESERVA ---")
    reserva_id = input("ID de la reserva: ")
    
    payload = {"reserva_id": int(reserva_id)}
    
    status, data = send_request("cancel_reserva", payload)
    print("✅ Solicitud enviada")

def op_create_prestamo():
    """Registrar un nuevo préstamo"""
    print("\n--- REGISTRAR PRÉSTAMO ---")
    solicitud_id = input("ID de la solicitud: ")
    item_existencia_id = input("ID de la existencia del item: ")
    usuario_id = input("ID del usuario: ")
    fecha_limite_str = input("Fecha límite (YYYY-MM-DD): ")
    
    payload = {
        "solicitud_id": int(solicitud_id),
        "item_existencia_id": int(item_existencia_id),
        "usuario_id": int(usuario_id),
        "fecha_limite": fecha_limite_str
    }
    
    status, data = send_request("create_prestamo", payload)
    print("✅ Solicitud enviada")

def op_create_devolucion():
    """Registrar devolución de un préstamo"""
    print("\n--- REGISTRAR DEVOLUCIÓN ---")
    prestamo_id = input("ID del préstamo: ")
    
    payload = {"prestamo_id": int(prestamo_id)}
    
    status, data = send_request("create_devolucion", payload)
    print("✅ Solicitud enviada")

def op_renovar_prestamo():
    """Renovar un préstamo existente"""
    print("\n--- RENOVAR PRÉSTAMO ---")
    prestamo_id = input("ID del préstamo: ")
    
    payload = {"prestamo_id": int(prestamo_id)}
    
    status, data = send_request("renovar_prestamo", payload)
    print("✅ Solicitud enviada")

def op_update_item_estado():
    """Actualizar estado de un item"""
    print("\n--- ACTUALIZAR ESTADO DE ITEM ---")
    item_id = input("ID del item: ")
    nuevo_estado = input("Nuevo estado (DISPONIBLE/NO_DISPONIBLE/PERDIDO/DAÑADO): ").upper()
    
    payload = {
        "item_id": int(item_id),
        "estado": nuevo_estado
    }
    
    status, data = send_request("update_item_estado", payload)
    print("✅ Solicitud enviada")

def show_menu():
    """Muestra el menú de operaciones"""
    print("\n" + "="*60)
    print("  CLIENTE SERVICIO PRART - PrestaLab SOA")
    print("  (Préstamos y Artículos)")
    print("="*60)
    print("\n--- Catálogo ---")
    print("[1] Obtener todos los items")
    print("[2] Buscar items")
    print("\n--- Solicitudes ---")
    print("[3] Obtener solicitudes de usuario")
    print("[4] Crear solicitud")
    print("\n--- Reservas ---")
    print("[5] Crear reserva")
    print("[6] Cancelar reserva")
    print("\n--- Préstamos ---")
    print("[7] Registrar préstamo")
    print("[8] Registrar devolución")
    print("[9] Renovar préstamo")
    print("\n--- Administración ---")
    print("[10] Actualizar estado de item")
    print("\n[0] Salir")
    print("\n(Ver logs detallados en contenedor soa_bus)")

def main():
    """Bucle principal del menú"""
    while True:
        show_menu()
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            op_get_all_items()
        elif opcion == "2":
            op_search_items()
        elif opcion == "3":
            op_get_solicitudes()
        elif opcion == "4":
            op_create_solicitud()
        elif opcion == "5":
            op_create_reserva()
        elif opcion == "6":
            op_cancel_reserva()
        elif opcion == "7":
            op_create_prestamo()
        elif opcion == "8":
            op_create_devolucion()
        elif opcion == "9":
            op_renovar_prestamo()
        elif opcion == "10":
            op_update_item_estado()
        elif opcion == "0":
            print("\n👋 Saliendo...\n")
            break
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {e}")
