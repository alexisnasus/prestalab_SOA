#!/usr/bin/env python3
"""
Cliente interactivo para el servicio SUGIT
Sistema PrestaLab SOA
"""

import socket
import json

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "sugit"

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

def op_registrar_sugerencia():
    """Registrar nueva sugerencia"""
    print("\n--- REGISTRAR SUGERENCIA ---")
    usuario_id = input("ID del usuario: ")
    sugerencia = input("Sugerencia: ")
    
    payload = {
        "usuario_id": int(usuario_id),
        "sugerencia": sugerencia
    }
    
    status, data = send_request("registrar_sugerencia", payload)
    print("✅ Solicitud enviada")

def op_listar_sugerencias():
    """Listar todas las sugerencias"""
    print("\n--- LISTAR SUGERENCIAS ---")
    
    payload = {}
    
    status, data = send_request("listar_sugerencias", payload)
    print("✅ Solicitud enviada")

def op_aprobar_sugerencia():
    """Aprobar una sugerencia"""
    print("\n--- APROBAR SUGERENCIA ---")
    sugerencia_id = input("ID de la sugerencia: ")
    
    payload = {"id": int(sugerencia_id)}
    
    status, data = send_request("aprobar_sugerencia", payload)
    print("✅ Solicitud enviada")

def op_rechazar_sugerencia():
    """Rechazar una sugerencia"""
    print("\n--- RECHAZAR SUGERENCIA ---")
    sugerencia_id = input("ID de la sugerencia: ")
    
    payload = {"id": int(sugerencia_id)}
    
    status, data = send_request("rechazar_sugerencia", payload)
    print("✅ Solicitud enviada")

def show_menu():
    """Muestra el menú de operaciones"""
    print("\n" + "="*50)
    print("  CLIENTE SERVICIO SUGIT - PrestaLab SOA")
    print("="*50)
    print("\n[1] Registrar sugerencia")
    print("[2] Listar sugerencias")
    print("[3] Aprobar sugerencia")
    print("[4] Rechazar sugerencia")
    print("[0] Salir")
    print("\n(Ver logs detallados en contenedor soa_bus)")

def main():
    """Bucle principal del menú"""
    while True:
        show_menu()
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            op_registrar_sugerencia()
        elif opcion == "2":
            op_listar_sugerencias()
        elif opcion == "3":
            op_aprobar_sugerencia()
        elif opcion == "4":
            op_rechazar_sugerencia()
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
