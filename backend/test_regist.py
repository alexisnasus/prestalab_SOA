#!/usr/bin/env python3
"""
Cliente interactivo para el servicio REGIST
Sistema PrestaLab SOA
"""

import socket
import json

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "regis"

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

def op_register():
    """Registrar nuevo usuario"""
    print("\n--- REGISTRAR USUARIO ---")
    correo = input("Correo: ")
    password = input("Password: ")
    nombre = input("Nombre completo: ")
    tipo = input("Tipo (ESTUDIANTE/PROFESOR/ADMIN): ").upper()
    telefono = input("Teléfono: ")
    
    payload = {
        "correo": correo,
        "password": password,
        "nombre": nombre,
        "tipo": tipo,
        "telefono": telefono
    }
    
    status, data = send_request("register", payload)
    print("✅ Solicitud enviada")

def op_login():
    """Login de usuario"""
    print("\n--- LOGIN ---")
    correo = input("Correo: ")
    password = input("Password: ")
    
    payload = {"correo": correo, "password": password}
    
    status, data = send_request("login", payload)
    print("✅ Solicitud enviada")

def op_get_user():
    """Consultar usuario por ID"""
    print("\n--- CONSULTAR USUARIO ---")
    user_id = input("ID del usuario: ")
    
    payload = {"id": int(user_id)}
    
    status, data = send_request("get_user", payload)
    print("✅ Solicitud enviada")

def op_update_user():
    """Actualizar datos de usuario"""
    print("\n--- ACTUALIZAR USUARIO ---")
    user_id = input("ID del usuario: ")
    
    print("Ingrese los campos a actualizar (Enter para omitir):")
    datos = {}
    nombre = input("  Nombre: ")
    if nombre:
        datos["nombre"] = nombre
    telefono = input("  Teléfono: ")
    if telefono:
        datos["telefono"] = telefono
    estado = input("  Estado (ACTIVO/INACTIVO): ")
    if estado:
        datos["estado"] = estado.upper()
    
    if not datos:
        print("⚠️  No hay datos para actualizar")
        return
    
    payload = {"id": int(user_id), "datos": datos}
    
    status, data = send_request("update_user", payload)
    print("✅ Solicitud enviada")

def op_update_solicitud():
    """Actualizar estado de solicitud"""
    print("\n--- ACTUALIZAR SOLICITUD ---")
    solicitud_id = input("ID de la solicitud: ")
    estado = input("Nuevo estado (APROBADA/RECHAZADA): ").upper()
    
    payload = {"solicitud_id": int(solicitud_id), "estado": estado}
    
    status, data = send_request("update_solicitud", payload)
    print("✅ Solicitud enviada")

def show_menu():
    """Muestra el menú de operaciones"""
    print("\n" + "="*50)
    print("  CLIENTE SERVICIO REGIST - PrestaLab SOA")
    print("="*50)
    print("\n[1] Registrar usuario")
    print("[2] Login")
    print("[3] Consultar usuario por ID")
    print("[4] Actualizar usuario")
    print("[5] Actualizar solicitud de registro")
    print("[0] Salir")
    print("\n(Ver logs detallados en contenedor soa_bus)")

def main():
    """Bucle principal del menú"""
    while True:
        show_menu()
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            op_register()
        elif opcion == "2":
            op_login()
        elif opcion == "3":
            op_get_user()
        elif opcion == "4":
            op_update_user()
        elif opcion == "5":
            op_update_solicitud()
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
