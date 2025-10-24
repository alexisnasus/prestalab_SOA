#!/usr/bin/env python3
"""
Cliente interactivo para el servicio GEREP (Generación de Reportes)
Sistema PrestaLab SOA
"""

import socket
import json
import base64

BUS_ADDRESS = ('localhost', 5000)
SERVICE_NAME = "gerep"

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

def save_file(filename, content_base64):
    """Guarda un archivo desde contenido en base64"""
    try:
        content = base64.b64decode(content_base64)
        with open(filename, 'wb') as f:
            f.write(content)
        print(f"📄 Archivo guardado: {filename}")
    except Exception as e:
        print(f"❌ Error al guardar archivo: {e}")

def op_get_historial():
    """Obtener historial de préstamos de un usuario"""
    print("\n--- HISTORIAL DE USUARIO ---")
    usuario_id = input("ID del usuario: ")
    formato = input("Formato (json/csv/pdf) [json]: ").lower() or "json"
    
    payload = {
        "usuario_id": int(usuario_id),
        "formato": formato
    }
    
    status, data = send_request("get_historial", payload)
    print("✅ Solicitud enviada")
    
    # Si el formato es CSV o PDF, guardar el archivo
    if data and formato in ["csv", "pdf"]:
        if "content" in data:
            filename = data.get("filename", f"historial_{usuario_id}.{formato}")
            save_file(filename, data["content"])

def op_get_reporte_circulacion():
    """Generar reporte de circulación por sede"""
    print("\n--- REPORTE DE CIRCULACIÓN ---")
    print("Período (formato: YYYY-MM, ejemplo: 2025-10)")
    periodo = input("Período: ")
    sede_id = input("ID de la sede: ")
    
    payload = {
        "periodo": periodo,
        "sede_id": int(sede_id)
    }
    
    status, data = send_request("get_reporte_circulacion", payload)
    print("✅ Solicitud enviada")

def show_menu():
    """Muestra el menú de operaciones"""
    print("\n" + "="*60)
    print("  CLIENTE SERVICIO GEREP - PrestaLab SOA")
    print("  (Generación de Reportes)")
    print("="*60)
    print("\n[1] Historial de usuario (JSON/CSV/PDF)")
    print("[2] Reporte de circulación por sede")
    print("[0] Salir")
    print("\n(Ver logs detallados en contenedor soa_bus)")

def main():
    """Bucle principal del menú"""
    while True:
        show_menu()
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            op_get_historial()
        elif opcion == "2":
            op_get_reporte_circulacion()
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
