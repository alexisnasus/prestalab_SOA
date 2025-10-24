#!/usr/bin/env python3
"""
Cliente interactivo para el servicio NOTIS
Sistema PrestaLab SOA
"""

import socket
import json

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "notis"

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

def op_crear_notificacion():
    """Crear una nueva notificación"""
    print("\n--- CREAR NOTIFICACIÓN ---")
    usuario_id = input("ID del usuario: ")
    tipo = input("Tipo (PRESTAMO/MULTA/LISTA_ESPERA/SOLICITUD): ")
    canal = input("Canal (EMAIL/SMS/PUSH): ")
    mensaje = input("Mensaje: ")
    
    payload = {
        "usuario_id": int(usuario_id),
        "tipo": tipo,
        "canal": canal,
        "mensaje": mensaje
    }
    
    status, data = send_request("crear_notificacion", payload)
    print("✅ Solicitud enviada")

def op_get_preferencias():
    """Obtener preferencias de notificación"""
    print("\n--- CONSULTAR PREFERENCIAS ---")
    usuario_id = input("ID del usuario: ")
    
    payload = {"usuario_id": int(usuario_id)}
    
    status, data = send_request("get_preferencias", payload)
    print("✅ Solicitud enviada")

def op_update_preferencias():
    """Actualizar preferencias de notificación"""
    print("\n--- ACTUALIZAR PREFERENCIAS ---")
    usuario_id = input("ID del usuario: ")
    print("\nTipos de notificación (Enter para omitir):")
    print("Opciones para cada tipo: EMAIL/SMS/PUSH (separar con comas si son varios)")
    
    prefs = {}
    
    tipos = ["PRESTAMO", "MULTA", "LISTA_ESPERA", "SOLICITUD"]
    for tipo in tipos:
        canales = input(f"{tipo}: ")
        if canales:
            prefs[tipo] = [c.strip() for c in canales.split(",")]
    
    if not prefs:
        print("⚠️  No hay preferencias para actualizar")
        return
        
    payload = {
        "usuario_id": int(usuario_id),
        "preferencias": prefs
    }
    
    status, data = send_request("update_preferencias", payload)
    print("✅ Solicitud enviada")

def show_menu():
    """Muestra el menú de operaciones"""
    print("\n" + "="*50)
    print("  CLIENTE SERVICIO NOTIS - PrestaLab SOA")
    print("="*50)
    print("\n[1] Crear notificación")
    print("[2] Consultar preferencias")
    print("[3] Actualizar preferencias")
    print("[0] Salir")
    print("\n(Ver logs detallados en contenedor soa_bus)")

def main():
    """Bucle principal del menú"""
    while True:
        show_menu()
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            op_crear_notificacion()
        elif opcion == "2":
            op_get_preferencias()
        elif opcion == "3":
            op_update_preferencias()
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