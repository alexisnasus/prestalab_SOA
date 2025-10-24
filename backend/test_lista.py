#!/usr/bin/env python3
"""
Cliente interactivo para el servicio LISTA
Sistema PrestaLab SOA
"""

import socket
import json

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "lista"

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

def op_crear_lista_espera():
    """Crear un nuevo registro en la lista de espera"""
    print("\n--- CREAR REGISTRO EN LISTA DE ESPERA ---")
    solicitud_id = input("ID de la solicitud: ")
    item_id = input("ID del item: ")
    estado = input("Estado (Enter para 'EN ESPERA'): ") or "EN ESPERA"
    
    payload = {
        "solicitud_id": int(solicitud_id),
        "item_id": int(item_id),
        "estado": estado
    }
    
    status, data = send_request("create_lista_espera", payload)
    print("✅ Solicitud enviada")

def op_actualizar_lista_espera():
    """Actualizar el estado de un registro en la lista de espera"""
    print("\n--- ACTUALIZAR ESTADO EN LISTA DE ESPERA ---")
    lista_id = input("ID del registro en lista de espera: ")
    nuevo_estado = input("Nuevo estado: ")
    
    payload = {
        "lista_id": int(lista_id),
        "estado": nuevo_estado
    }
    
    status, data = send_request("update_lista_espera", payload)
    print("✅ Solicitud enviada")

def op_consultar_lista_espera():
    """Consultar la lista de espera para un item"""
    print("\n--- CONSULTAR LISTA DE ESPERA ---")
    item_id = input("ID del item: ")
    
    payload = {
        "item_id": int(item_id)
    }
    
    status, data = send_request("get_lista_espera", payload)
    print("✅ Solicitud enviada")

def main():
    """Función principal - menú interactivo"""
    while True:
        print("\n=== CLIENTE LISTA DE ESPERA ===")
        print("1. Crear registro en lista de espera")
        print("2. Actualizar estado")
        print("3. Consultar lista de espera por item")
        print("0. Salir")
        
        opcion = input("\nOpción: ")
        
        if opcion == "1":
            op_crear_lista_espera()
        elif opcion == "2":
            op_actualizar_lista_espera()
        elif opcion == "3":
            op_consultar_lista_espera()
        elif opcion == "0":
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()