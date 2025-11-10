#!/usr/bin/env python3
"""
Cliente Completo PrestaLab SOA
Simula la experiencia de usuario por consola
Sistema PrestaLab - Arquitectura Orientada a Servicios
"""

import socket
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

# Configuración del Bus SOA
BUS_ADDRESS = ('localhost', 5000)

# Estado de sesión del usuario
class Session:
    def __init__(self):
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None
        self.user_type: Optional[str] = None
        self.user_email: Optional[str] = None
        self.logged_in: bool = False
    
    def login(self, user_id: int, name: str, tipo: str, email: str):
        self.user_id = user_id
        self.user_name = name
        self.user_type = tipo
        self.user_email = email
        self.logged_in = True
    
    def logout(self):
        self.user_id = None
        self.user_name = None
        self.user_type = None
        self.user_email = None
        self.logged_in = False
    
    def is_admin(self) -> bool:
        return self.user_type == "ADMIN"

# Sesión global
session = Session()

# ============================================
# FUNCIONES DE COMUNICACIÓN CON EL BUS SOA
# ============================================

def send_to_bus(service: str, operation: str, payload: dict) -> Tuple[Optional[str], Optional[dict]]:
    """
    Envía una solicitud al bus SOA y retorna la respuesta
    
    Args:
        service: Nombre del servicio (5 caracteres)
        operation: Operación a ejecutar
        payload: Datos a enviar
    
    Returns:
        (status, data): Tupla con el estado (OK/NK) y los datos de respuesta
    """
    try:
        # Preparar el mensaje según protocolo: NNNNNSSSSSDATOS
        service_padded = service.ljust(5)[:5]
        data_str = f"{operation} {json.dumps(payload)}"
        message_body = f"{service_padded}{data_str}"
        message_len = len(message_body)
        formatted_message = f"{message_len:05d}{message_body}".encode('utf-8')
        
        # Conectar y enviar
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Timeout de 10 segundos
        
        try:
            sock.connect(BUS_ADDRESS)
            sock.sendall(formatted_message)
            
            # Leer respuesta: NNNNNSSSSSSTDATOS
            length_bytes = sock.recv(5)
            if not length_bytes:
                return None, {"error": "Sin respuesta del bus"}
            
            amount_expected = int(length_bytes.decode('utf-8'))
            data_received = b''
            
            while len(data_received) < amount_expected:
                chunk = sock.recv(amount_expected - len(data_received))
                if not chunk:
                    break
                data_received += chunk
            
            response_str = data_received.decode('utf-8')
            
            # Parsear respuesta
            # response_service = response_str[:5]  # No usado
            status = response_str[5:7]  # OK o NK
            response_data = response_str[7:]
            
            # Intentar parsear como JSON
            try:
                parsed_data = json.loads(response_data)
            except json.JSONDecodeError:
                # Si falla, puede ser que el status esté pegado al JSON
                # Intentar encontrar donde empieza el JSON
                try:
                    # Buscar el primer { o [
                    json_start = -1
                    for i, char in enumerate(response_data):
                        if char in ['{', '[']:
                            json_start = i
                            break
                    
                    if json_start >= 0:
                        parsed_data = json.loads(response_data[json_start:])
                    else:
                        parsed_data = {"raw_response": response_data}
                except:
                    parsed_data = {"raw_response": response_data}
            
            # DEBUG: Mostrar respuesta para diagnosticar problemas
            if os.getenv("DEBUG_SOA"):
                print(f"\n[DEBUG] Status: {status}")
                print(f"[DEBUG] Data: {parsed_data}")
            
            return status, parsed_data
            
        finally:
            sock.close()
            
    except socket.timeout:
        return None, {"error": "Timeout en la conexión con el bus"}
    except ConnectionRefusedError:
        return None, {"error": "No se pudo conectar al bus SOA. ¿Está corriendo docker-compose?"}
    except Exception as e:
        return None, {"error": f"Error de comunicación: {str(e)}"}

def print_response(status: Optional[str], data: Optional[dict], show_success: bool = True):
    """Imprime la respuesta del servicio de forma amigable"""
    if status is None:
        print("\n❌ ERROR DE COMUNICACIÓN:")
        if data and "error" in data:
            print(f"   {data['error']}")
        return False
    
    if status == "OK":
        if show_success:
            print("\n✅ OPERACIÓN EXITOSA")
        if data:
            # Mostrar mensaje si existe
            if "message" in data:
                print(f"   📝 {data['message']}")
            
            # Mostrar datos específicos según el tipo
            # El servicio regis usa "user" en vez de "usuario"
            user_data = data.get("usuario") or data.get("user")
            if user_data:
                print_usuario(user_data)
            elif "items" in data and isinstance(data["items"], list):
                print_items(data["items"])
            elif "solicitudes" in data and isinstance(data["solicitudes"], list):
                print_solicitudes(data["solicitudes"])
            elif "multas" in data and isinstance(data["multas"], list):
                print_multas(data["multas"])
            elif "sugerencias" in data and isinstance(data["sugerencias"], list):
                print_sugerencias(data["sugerencias"])
            elif "lista_espera" in data and isinstance(data["lista_espera"], list):
                print_lista_espera(data["lista_espera"])
            elif "historial" in data and isinstance(data["historial"], list):
                print_historial(data["historial"])
            elif "reporte" in data:
                print_reporte(data["reporte"])
        return True
    else:
        print("\n❌ ERROR EN LA OPERACIÓN:")
        if data and "error" in data:
            print(f"   {data['error']}")
        elif data and "message" in data:
            print(f"   {data['message']}")
        else:
            print(f"   Respuesta del servidor: {data}")
        return False

# ============================================
# FUNCIONES DE IMPRESIÓN FORMATEADA
# ============================================

def print_usuario(usuario: dict):
    """Imprime información de un usuario"""
    print("\n   👤 DATOS DEL USUARIO:")
    print(f"      ID: {usuario.get('id')}")
    print(f"      Nombre: {usuario.get('nombre')}")
    print(f"      Correo: {usuario.get('correo')}")
    print(f"      Tipo: {usuario.get('tipo')}")
    print(f"      Teléfono: {usuario.get('telefono', 'N/A')}")
    print(f"      Estado: {usuario.get('estado')}")

def print_items(items: list):
    """Imprime listado de items del catálogo"""
    if not items:
        print("   📚 No se encontraron items")
        return
    
    print(f"\n   📚 ITEMS ENCONTRADOS ({len(items)}):")
    print("   " + "-" * 80)
    for item in items[:10]:  # Mostrar solo los primeros 10
        print(f"   ID: {item.get('id')} | {item.get('nombre', 'Sin nombre')}")
        print(f"      Tipo: {item.get('tipo')} | Autor: {item.get('autor', 'N/A')}")
        print(f"      ISBN: {item.get('isbn', 'N/A')} | Disponibles: {item.get('disponibles', 0)}")
        print("   " + "-" * 80)
    
    if len(items) > 10:
        print(f"   ... y {len(items) - 10} items más")

def print_solicitudes(solicitudes: list):
    """Imprime listado de solicitudes"""
    if not solicitudes:
        print("   📋 No se encontraron solicitudes")
        return
    
    print(f"\n   📋 SOLICITUDES ({len(solicitudes)}):")
    print("   " + "-" * 80)
    for sol in solicitudes:
        print(f"   ID: {sol.get('id')} | Estado: {sol.get('estado')}")
        print(f"      Tipo: {sol.get('tipo')} | Fecha: {sol.get('fecha_solicitud', 'N/A')}")
        if sol.get('items'):
            print(f"      Items: {', '.join([str(i.get('nombre', i.get('id'))) for i in sol.get('items', [])])}")
        print("   " + "-" * 80)

def print_multas(multas: list):
    """Imprime listado de multas"""
    if not multas:
        print("   💰 No tiene multas registradas")
        return
    
    print(f"\n   💰 MULTAS ({len(multas)}):")
    print("   " + "-" * 80)
    total = 0
    for multa in multas:
        valor = multa.get('valor', 0)
        total += valor if multa.get('estado') == 'PENDIENTE' else 0
        print(f"   ID: {multa.get('id')} | Estado: {multa.get('estado')}")
        print(f"      Motivo: {multa.get('motivo')}")
        print(f"      Valor: ${valor} | Fecha: {multa.get('fecha_generacion', 'N/A')}")
        print("   " + "-" * 80)
    
    if total > 0:
        print(f"   💸 TOTAL PENDIENTE: ${total}")

def print_sugerencias(sugerencias: list):
    """Imprime listado de sugerencias"""
    if not sugerencias:
        print("   💡 No hay sugerencias registradas")
        return
    
    print(f"\n   💡 SUGERENCIAS ({len(sugerencias)}):")
    print("   " + "-" * 80)
    for sug in sugerencias:
        print(f"   ID: {sug.get('id')} | Estado: {sug.get('estado')}")
        print(f"      Usuario: {sug.get('usuario_nombre', f"ID {sug.get('usuario_id')}")}")
        print(f"      Sugerencia: {sug.get('sugerencia')}")
        print(f"      Fecha: {sug.get('fecha_sugerencia', 'N/A')}")
        print("   " + "-" * 80)

def print_lista_espera(lista: list):
    """Imprime lista de espera"""
    if not lista:
        print("   ⏳ Lista de espera vacía")
        return
    
    print(f"\n   ⏳ LISTA DE ESPERA ({len(lista)}):")
    print("   " + "-" * 80)
    for idx, registro in enumerate(lista, 1):
        print(f"   Posición #{idx} | Estado: {registro.get('estado')}")
        print(f"      Usuario: {registro.get('usuario_nombre', f"ID {registro.get('usuario_id')}")}")
        print(f"      Fecha registro: {registro.get('fecha_registro', 'N/A')}")
        print("   " + "-" * 80)

def print_historial(historial: list):
    """Imprime historial de préstamos"""
    if not historial:
        print("   📖 No hay historial de préstamos")
        return
    
    print(f"\n   📖 HISTORIAL DE PRÉSTAMOS ({len(historial)}):")
    print("   " + "-" * 80)
    for prest in historial:
        print(f"   ID: {prest.get('id')} | Estado: {prest.get('estado')}")
        print(f"      Item: {prest.get('item_nombre', 'N/A')}")
        print(f"      Fecha préstamo: {prest.get('fecha_prestamo', 'N/A')}")
        print(f"      Fecha límite: {prest.get('fecha_limite', 'N/A')}")
        if prest.get('fecha_devolucion'):
            print(f"      Fecha devolución: {prest.get('fecha_devolucion')}")
        print("   " + "-" * 80)

def print_reporte(reporte: dict):
    """Imprime un reporte de circulación"""
    print("\n   📊 REPORTE DE CIRCULACIÓN:")
    print(f"      Sede: {reporte.get('sede_nombre', 'N/A')}")
    print(f"      Período: {reporte.get('periodo', 'N/A')}")
    print(f"      Total préstamos: {reporte.get('total_prestamos', 0)}")
    print(f"      Total devoluciones: {reporte.get('total_devoluciones', 0)}")
    print(f"      Items más prestados: {', '.join(reporte.get('items_populares', []))}")

# ============================================
# MÓDULO: AUTENTICACIÓN Y REGISTRO
# ============================================

def menu_autenticacion():
    """Menú de autenticación"""
    while not session.logged_in:
        print("\n" + "="*60)
        print("  🔐 PRESTALAB - SISTEMA DE AUTENTICACIÓN")
        print("="*60)
        print("\n[1] Iniciar Sesión")
        print("[2] Registrarse")
        print("[0] Salir del Sistema")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            login()
        elif opcion == "2":
            registro()
        elif opcion == "0":
            print("\n👋 Gracias por usar PrestaLab\n")
            exit(0)
        else:
            print("\n❌ Opción inválida")

def login():
    """Iniciar sesión"""
    print("\n" + "="*60)
    print("  INICIAR SESIÓN")
    print("="*60)
    
    correo = input("📧 Correo electrónico: ").strip()
    password = input("🔑 Contraseña: ").strip()
    
    if not correo or not password:
        print("\n❌ Debe ingresar correo y contraseña")
        return
    
    print("\n⏳ Autenticando...")
    status, data = send_to_bus("regis", "login", {
        "correo": correo,
        "password": password
    })
    
    if status == "OK" and data:
        # El servicio regis devuelve "user" en vez de "usuario"
        user = data.get("user") or data.get("usuario")
        if user:
            session.login(
                user_id=user.get("id"),
                name=user.get("nombre"),
                tipo=user.get("tipo"),
                email=user.get("correo")
            )
            print(f"\n✅ ¡Bienvenido/a, {session.user_name}!")
            print(f"   Tipo de cuenta: {session.user_type}")
            input("\nPresione Enter para continuar...")
        else:
            print("\n❌ Error: Respuesta del servidor sin datos de usuario")
            print(f"   Respuesta: {data}")
            input("\nPresione Enter para continuar...")
    else:
        print_response(status, data, show_success=False)
        input("\nPresione Enter para continuar...")

def registro():
    """Registrar nuevo usuario"""
    print("\n" + "="*60)
    print("  REGISTRAR NUEVO USUARIO")
    print("="*60)
    
    correo = input("📧 Correo electrónico: ").strip()
    password = input("🔑 Contraseña: ").strip()
    nombre = input("👤 Nombre completo: ").strip()
    
    print("\nTipo de usuario:")
    print("  [1] Estudiante")
    print("  [2] Profesor")
    tipo_op = input("Seleccione: ").strip()
    tipo = "ESTUDIANTE" if tipo_op == "1" else "PROFESOR" if tipo_op == "2" else "ESTUDIANTE"
    
    telefono = input("📱 Teléfono: ").strip()
    
    if not all([correo, password, nombre]):
        print("\n❌ Correo, contraseña y nombre son obligatorios")
        return
    
    print("\n⏳ Registrando usuario...")
    status, data = send_to_bus("regis", "register", {
        "correo": correo,
        "password": password,
        "nombre": nombre,
        "tipo": tipo,
        "telefono": telefono
    })
    
    if print_response(status, data):
        print("\n   ℹ️  Su solicitud de registro será revisada por un administrador")
        print("   ℹ️  Recibirá una notificación cuando sea aprobada")
    
    input("\nPresione Enter para continuar...")

# ============================================
# MÓDULO: CATÁLOGO Y BÚSQUEDA
# ============================================

def menu_catalogo():
    """Menú del catálogo de items"""
    while True:
        print("\n" + "="*60)
        print("  📚 CATÁLOGO DE ITEMS")
        print("="*60)
        print("\n[1] Ver todos los items")
        print("[2] Buscar items")
        print("[3] Ver detalles de un item")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            listar_todos_items()
        elif opcion == "2":
            buscar_items()
        elif opcion == "3":
            ver_detalle_item()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def listar_todos_items():
    """Listar todos los items del catálogo"""
    print("\n⏳ Cargando catálogo...")
    status, data = send_to_bus("prart", "get_all_items", {})
    print_response(status, data, show_success=False)

def buscar_items():
    """Buscar items con filtros"""
    print("\n" + "="*60)
    print("  BUSCAR ITEMS")
    print("="*60)
    print("\nIngrese los criterios de búsqueda (Enter para omitir):")
    
    filtros = {}
    
    nombre = input("📖 Nombre/Título: ").strip()
    if nombre:
        filtros["nombre"] = nombre
    
    print("\nTipo de item:")
    print("  [1] Libro")
    print("  [2] Revista")
    print("  [3] Tesis")
    print("  [4] Otro")
    tipo_op = input("Tipo: ").strip()
    if tipo_op == "1":
        filtros["tipo"] = "LIBRO"
    elif tipo_op == "2":
        filtros["tipo"] = "REVISTA"
    elif tipo_op == "3":
        filtros["tipo"] = "TESIS"
    elif tipo_op == "4":
        filtros["tipo"] = "OTRO"
    
    if not filtros:
        print("\n⚠️  No se especificaron filtros. Mostrando todos los items...")
    
    print("\n⏳ Buscando...")
    status, data = send_to_bus("prart", "search_items", filtros)
    print_response(status, data, show_success=False)

def ver_detalle_item():
    """Ver detalles de un item específico"""
    item_id = input("\n🔍 Ingrese el ID del item: ").strip()
    
    if not item_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    # Buscar el item específico
    print("\n⏳ Consultando...")
    status, data = send_to_bus("prart", "search_items", {"id": int(item_id)})
    
    if status == "OK" and data and "items" in data and len(data["items"]) > 0:
        item = data["items"][0]
        print("\n" + "="*60)
        print("  📖 DETALLES DEL ITEM")
        print("="*60)
        print(f"\nID: {item.get('id')}")
        print(f"Nombre: {item.get('nombre')}")
        print(f"Tipo: {item.get('tipo')}")
        print(f"Autor: {item.get('autor', 'N/A')}")
        print(f"ISBN: {item.get('isbn', 'N/A')}")
        print(f"Editorial: {item.get('editorial', 'N/A')}")
        print(f"Año: {item.get('año_publicacion', 'N/A')}")
        print(f"Descripción: {item.get('descripcion', 'N/A')}")
        print(f"\nDisponibilidad:")
        print(f"  Total ejemplares: {item.get('total', 0)}")
        print(f"  Disponibles: {item.get('disponibles', 0)}")
        print(f"  Prestados: {item.get('prestados', 0)}")
    else:
        print_response(status, data, show_success=False)

# ============================================
# MÓDULO: SOLICITUDES Y PRÉSTAMOS
# ============================================

def menu_solicitudes():
    """Menú de solicitudes y préstamos"""
    while True:
        print("\n" + "="*60)
        print("  📋 MIS SOLICITUDES Y PRÉSTAMOS")
        print("="*60)
        print("\n[1] Ver mis solicitudes")
        print("[2] Crear nueva solicitud de préstamo")
        print("[3] Cancelar una solicitud")
        print("[4] Renovar un préstamo")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_mis_solicitudes()
        elif opcion == "2":
            crear_solicitud()
        elif opcion == "3":
            cancelar_solicitud()
        elif opcion == "4":
            renovar_prestamo()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def ver_mis_solicitudes():
    """Ver las solicitudes del usuario actual"""
    print("\n⏳ Cargando solicitudes...")
    status, data = send_to_bus("prart", "get_solicitudes", {
        "usuario_id": session.user_id
    })
    print_response(status, data, show_success=False)

def crear_solicitud():
    """Crear una nueva solicitud de préstamo"""
    print("\n" + "="*60)
    print("  NUEVA SOLICITUD DE PRÉSTAMO")
    print("="*60)
    
    print("\nIngrese los IDs de los items que desea solicitar")
    print("(separados por comas, ejemplo: 1,2,3)")
    items_input = input("Items: ").strip()
    
    if not items_input:
        print("\n❌ Debe ingresar al menos un item")
        return
    
    try:
        items_ids = [int(x.strip()) for x in items_input.split(',') if x.strip()]
    except ValueError:
        print("\n❌ IDs inválidos")
        return
    
    if not items_ids:
        print("\n❌ Debe ingresar al menos un item")
        return
    
    print("\n⏳ Creando solicitud...")
    status, data = send_to_bus("prart", "create_solicitud", {
        "usuario_id": session.user_id,
        "items": items_ids
    })
    
    if print_response(status, data):
        print("\n   ℹ️  Su solicitud será revisada por un administrador")
        print("   ℹ️  Recibirá una notificación cuando sea procesada")

def cancelar_solicitud():
    """Cancelar una reserva/solicitud"""
    print("\n" + "="*60)
    print("  CANCELAR RESERVA")
    print("="*60)
    
    reserva_id = input("\n🔢 Ingrese el ID de la reserva a cancelar: ").strip()
    
    if not reserva_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    confirmacion = input(f"\n⚠️  ¿Está seguro de cancelar la reserva #{reserva_id}? (s/n): ").strip().lower()
    
    if confirmacion != 's':
        print("\n❌ Cancelación abortada")
        return
    
    print("\n⏳ Cancelando reserva...")
    status, data = send_to_bus("prart", "cancel_reserva", {
        "reserva_id": int(reserva_id)
    })
    print_response(status, data)

def renovar_prestamo():
    """Renovar un préstamo existente"""
    print("\n" + "="*60)
    print("  RENOVAR PRÉSTAMO")
    print("="*60)
    
    prestamo_id = input("\n🔢 Ingrese el ID del préstamo a renovar: ").strip()
    
    if not prestamo_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n⏳ Renovando préstamo...")
    status, data = send_to_bus("prart", "renovar_prestamo", {
        "prestamo_id": int(prestamo_id)
    })
    print_response(status, data)

# ============================================
# MÓDULO: MULTAS
# ============================================

def menu_multas():
    """Menú de multas"""
    print("\n⏳ Consultando multas...")
    status, data = send_to_bus("multa", "get_multas_usuario", {
        "usuario_id": session.user_id
    })
    print_response(status, data, show_success=False)
    input("\nPresione Enter para continuar...")

# ============================================
# MÓDULO: LISTAS DE ESPERA
# ============================================

def menu_lista_espera():
    """Menú de listas de espera"""
    while True:
        print("\n" + "="*60)
        print("  ⏳ LISTAS DE ESPERA")
        print("="*60)
        print("\n[1] Ver lista de espera de un item")
        print("[2] Unirse a una lista de espera")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_lista_espera()
        elif opcion == "2":
            unirse_lista_espera()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def ver_lista_espera():
    """Ver la lista de espera de un item"""
    item_id = input("\n🔢 Ingrese el ID del item: ").strip()
    
    if not item_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n⏳ Consultando lista de espera...")
    status, data = send_to_bus("lista", "get_lista_espera", {
        "item_id": int(item_id)
    })
    print_response(status, data, show_success=False)

def unirse_lista_espera():
    """Unirse a una lista de espera"""
    print("\n" + "="*60)
    print("  UNIRSE A LISTA DE ESPERA")
    print("="*60)
    
    # Primero necesitamos una solicitud
    print("\nPara unirse a una lista de espera, primero debe tener")
    print("una solicitud de préstamo creada.")
    
    solicitud_id = input("\n🔢 ID de su solicitud: ").strip()
    item_id = input("🔢 ID del item: ").strip()
    
    if not solicitud_id.isdigit() or not item_id.isdigit():
        print("\n❌ IDs inválidos")
        return
    
    print("\n⏳ Registrando en lista de espera...")
    status, data = send_to_bus("lista", "create_lista_espera", {
        "solicitud_id": int(solicitud_id),
        "item_id": int(item_id),
        "estado": "EN ESPERA"
    })
    print_response(status, data)

# ============================================
# MÓDULO: SUGERENCIAS
# ============================================

def menu_sugerencias():
    """Menú de sugerencias"""
    while True:
        print("\n" + "="*60)
        print("  💡 SUGERENCIAS")
        print("="*60)
        print("\n[1] Ver todas las sugerencias")
        print("[2] Enviar una sugerencia")
        
        if session.is_admin():
            print("[3] Aprobar sugerencia")
            print("[4] Rechazar sugerencia")
        
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            listar_sugerencias()
        elif opcion == "2":
            enviar_sugerencia()
        elif opcion == "3" and session.is_admin():
            aprobar_sugerencia()
        elif opcion == "4" and session.is_admin():
            rechazar_sugerencia()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def listar_sugerencias():
    """Listar todas las sugerencias"""
    print("\n⏳ Cargando sugerencias...")
    status, data = send_to_bus("sugit", "listar_sugerencias", {})
    print_response(status, data, show_success=False)

def enviar_sugerencia():
    """Enviar una nueva sugerencia"""
    print("\n" + "="*60)
    print("  ENVIAR SUGERENCIA")
    print("="*60)
    
    print("\nEscriba su sugerencia para mejorar el sistema:")
    sugerencia = input("💬 Sugerencia: ").strip()
    
    if not sugerencia:
        print("\n❌ La sugerencia no puede estar vacía")
        return
    
    print("\n⏳ Enviando sugerencia...")
    status, data = send_to_bus("sugit", "registrar_sugerencia", {
        "usuario_id": session.user_id,
        "sugerencia": sugerencia
    })
    
    if print_response(status, data):
        print("\n   ℹ️  Gracias por su sugerencia. Será revisada por el equipo.")

def aprobar_sugerencia():
    """Aprobar una sugerencia (solo admin)"""
    sugerencia_id = input("\n🔢 ID de la sugerencia a aprobar: ").strip()
    
    if not sugerencia_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n⏳ Aprobando sugerencia...")
    status, data = send_to_bus("sugit", "aprobar_sugerencia", {
        "id": int(sugerencia_id)
    })
    print_response(status, data)

def rechazar_sugerencia():
    """Rechazar una sugerencia (solo admin)"""
    sugerencia_id = input("\n🔢 ID de la sugerencia a rechazar: ").strip()
    
    if not sugerencia_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n⏳ Rechazando sugerencia...")
    status, data = send_to_bus("sugit", "rechazar_sugerencia", {
        "id": int(sugerencia_id)
    })
    print_response(status, data)

# ============================================
# MÓDULO: REPORTES
# ============================================

def menu_reportes():
    """Menú de reportes"""
    while True:
        print("\n" + "="*60)
        print("  📊 REPORTES E HISTORIAL")
        print("="*60)
        print("\n[1] Mi historial de préstamos (JSON)")
        print("[2] Mi historial de préstamos (CSV)")
        print("[3] Mi historial de préstamos (PDF)")
        
        if session.is_admin():
            print("[4] Reporte de circulación por sede")
        
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_historial("json")
        elif opcion == "2":
            ver_historial("csv")
        elif opcion == "3":
            ver_historial("pdf")
        elif opcion == "4" and session.is_admin():
            reporte_circulacion()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def ver_historial(formato: str):
    """Ver historial de préstamos en diferentes formatos"""
    print(f"\n⏳ Generando historial en formato {formato.upper()}...")
    
    status, data = send_to_bus("gerep", "get_historial", {
        "usuario_id": session.user_id,
        "formato": formato
    })
    
    if status == "OK" and data:
        if formato == "json":
            print_response(status, data, show_success=False)
        elif formato in ["csv", "pdf"]:
            if "content" in data and "filename" in data:
                # Guardar archivo
                try:
                    filename = data["filename"]
                    content = base64.b64decode(data["content"])
                    
                    with open(filename, 'wb') as f:
                        f.write(content)
                    
                    print(f"\n✅ Archivo generado: {filename}")
                    print(f"   📁 Ubicación: {os.path.abspath(filename)}")
                except Exception as e:
                    print(f"\n❌ Error al guardar archivo: {e}")
            else:
                print_response(status, data, show_success=False)
    else:
        print_response(status, data, show_success=False)

def reporte_circulacion():
    """Generar reporte de circulación (solo admin)"""
    print("\n" + "="*60)
    print("  REPORTE DE CIRCULACIÓN")
    print("="*60)
    
    periodo = input("\n📅 Período (YYYY-MM, ejemplo: 2025-10): ").strip()
    sede_id = input("🏢 ID de la sede: ").strip()
    
    if not sede_id.isdigit():
        print("\n❌ ID de sede inválido")
        return
    
    print("\n⏳ Generando reporte...")
    status, data = send_to_bus("gerep", "get_reporte_circulacion", {
        "periodo": periodo,
        "sede_id": int(sede_id)
    })
    print_response(status, data, show_success=False)

# ============================================
# MÓDULO: NOTIFICACIONES
# ============================================

def menu_notificaciones():
    """Menú de notificaciones"""
    while True:
        print("\n" + "="*60)
        print("  🔔 NOTIFICACIONES Y PREFERENCIAS")
        print("="*60)
        print("\n[1] Ver mis preferencias de notificación")
        print("[2] Actualizar preferencias de notificación")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_preferencias()
        elif opcion == "2":
            actualizar_preferencias()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def ver_preferencias():
    """Ver preferencias de notificación"""
    print("\n⏳ Consultando preferencias...")
    status, data = send_to_bus("notis", "get_preferencias", {
        "usuario_id": session.user_id
    })
    print_response(status, data, show_success=False)

def actualizar_preferencias():
    """Actualizar preferencias de notificación"""
    print("\n" + "="*60)
    print("  ACTUALIZAR PREFERENCIAS DE NOTIFICACIÓN")
    print("="*60)
    
    print("\nCanales disponibles: EMAIL, SMS, PUSH")
    print("Para cada tipo de notificación, ingrese los canales separados por comas")
    print("(Ejemplo: EMAIL,SMS)")
    print("Presione Enter para no recibir ese tipo de notificación\n")
    
    prefs = {}
    
    tipos = [
        ("PRESTAMO", "Notificaciones de préstamos"),
        ("MULTA", "Notificaciones de multas"),
        ("LISTA_ESPERA", "Notificaciones de lista de espera"),
        ("SOLICITUD", "Notificaciones de solicitudes")
    ]
    
    for tipo, descripcion in tipos:
        canales_input = input(f"{descripcion}: ").strip()
        if canales_input:
            canales = [c.strip().upper() for c in canales_input.split(',')]
            # Validar canales
            canales_validos = [c for c in canales if c in ["EMAIL", "SMS", "PUSH"]]
            if canales_validos:
                prefs[tipo] = canales_validos
    
    if not prefs:
        print("\n⚠️  No se especificaron preferencias")
        return
    
    print("\n⏳ Actualizando preferencias...")
    status, data = send_to_bus("notis", "update_preferencias", {
        "usuario_id": session.user_id,
        "preferencias": prefs
    })
    print_response(status, data)

# ============================================
# MÓDULO: ADMINISTRACIÓN (Solo Admin)
# ============================================

def menu_admin():
    """Menú de administración (solo para admins)"""
    if not session.is_admin():
        print("\n❌ Acceso denegado. Esta sección es solo para administradores.")
        input("\nPresione Enter para continuar...")
        return
    
    while True:
        print("\n" + "="*60)
        print("  ⚙️  PANEL DE ADMINISTRACIÓN")
        print("="*60)
        print("\n[1] Aprobar/Rechazar solicitudes de registro")
        print("[2] Gestionar solicitudes de préstamo")
        print("[3] Registrar préstamo manualmente")
        print("[4] Registrar devolución")
        print("[5] Crear multa")
        print("[6] Bloquear/Desbloquear usuario")
        print("[7] Actualizar estado de item")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            gestionar_solicitudes_registro()
        elif opcion == "2":
            gestionar_solicitudes_prestamo()
        elif opcion == "3":
            registrar_prestamo_manual()
        elif opcion == "4":
            registrar_devolucion()
        elif opcion == "5":
            crear_multa_manual()
        elif opcion == "6":
            gestionar_bloqueo_usuario()
        elif opcion == "7":
            actualizar_estado_item()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def gestionar_solicitudes_registro():
    """Aprobar o rechazar solicitudes de registro de usuarios"""
    print("\n" + "="*60)
    print("  GESTIONAR SOLICITUDES DE REGISTRO")
    print("="*60)
    
    solicitud_id = input("\n🔢 ID de la solicitud: ").strip()
    
    if not solicitud_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n[1] Aprobar")
    print("[2] Rechazar")
    accion = input("Acción: ").strip()
    
    estado = "APROBADA" if accion == "1" else "RECHAZADA" if accion == "2" else None
    
    if not estado:
        print("\n❌ Acción inválida")
        return
    
    print(f"\n⏳ Actualizando solicitud a {estado}...")
    status, data = send_to_bus("regis", "update_solicitud", {
        "solicitud_id": int(solicitud_id),
        "estado": estado
    })
    print_response(status, data)

def gestionar_solicitudes_prestamo():
    """Ver y gestionar solicitudes de préstamo pendientes"""
    # Primero, listar solicitudes de un usuario
    usuario_id = input("\n🔢 ID del usuario (Enter para omitir): ").strip()
    
    if usuario_id and usuario_id.isdigit():
        print("\n⏳ Consultando solicitudes...")
        status, data = send_to_bus("prart", "get_solicitudes", {
            "usuario_id": int(usuario_id)
        })
        print_response(status, data, show_success=False)

def registrar_prestamo_manual():
    """Registrar un préstamo manualmente"""
    print("\n" + "="*60)
    print("  REGISTRAR PRÉSTAMO MANUAL")
    print("="*60)
    
    solicitud_id = input("\n🔢 ID de la solicitud: ").strip()
    item_existencia_id = input("🔢 ID de la existencia del item: ").strip()
    usuario_id = input("🔢 ID del usuario: ").strip()
    
    # Calcular fecha límite (por ejemplo, 7 días desde hoy)
    fecha_limite = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"\n📅 Fecha límite calculada: {fecha_limite}")
    confirmar = input("¿Usar esta fecha? (s/n): ").strip().lower()
    
    if confirmar != 's':
        fecha_limite = input("📅 Ingrese fecha límite (YYYY-MM-DD): ").strip()
    
    if not all([solicitud_id.isdigit(), item_existencia_id.isdigit(), usuario_id.isdigit()]):
        print("\n❌ IDs inválidos")
        return
    
    print("\n⏳ Registrando préstamo...")
    status, data = send_to_bus("prart", "create_prestamo", {
        "solicitud_id": int(solicitud_id),
        "item_existencia_id": int(item_existencia_id),
        "usuario_id": int(usuario_id),
        "fecha_limite": fecha_limite
    })
    print_response(status, data)

def registrar_devolucion():
    """Registrar la devolución de un préstamo"""
    print("\n" + "="*60)
    print("  REGISTRAR DEVOLUCIÓN")
    print("="*60)
    
    prestamo_id = input("\n🔢 ID del préstamo: ").strip()
    
    if not prestamo_id.isdigit():
        print("\n❌ ID inválido")
        return
    
    print("\n⏳ Registrando devolución...")
    status, data = send_to_bus("prart", "create_devolucion", {
        "prestamo_id": int(prestamo_id)
    })
    print_response(status, data)

def crear_multa_manual():
    """Crear una multa manualmente"""
    print("\n" + "="*60)
    print("  CREAR MULTA")
    print("="*60)
    
    prestamo_id = input("\n🔢 ID del préstamo: ").strip()
    motivo = input("💬 Motivo de la multa: ").strip()
    valor = input("💰 Valor de la multa: ").strip()
    
    print("\nEstado:")
    print("  [1] Pendiente")
    print("  [2] Pagada")
    print("  [3] Cancelada")
    estado_op = input("Estado: ").strip()
    
    estado_map = {"1": "PENDIENTE", "2": "PAGADA", "3": "CANCELADA"}
    estado = estado_map.get(estado_op, "PENDIENTE")
    
    if not prestamo_id.isdigit():
        print("\n❌ ID de préstamo inválido")
        return
    
    try:
        valor_float = float(valor)
    except ValueError:
        print("\n❌ Valor inválido")
        return
    
    print("\n⏳ Creando multa...")
    status, data = send_to_bus("multa", "crear_multa", {
        "prestamo_id": int(prestamo_id),
        "motivo": motivo,
        "valor": valor_float,
        "estado": estado
    })
    print_response(status, data)

def gestionar_bloqueo_usuario():
    """Bloquear o desbloquear un usuario"""
    print("\n" + "="*60)
    print("  GESTIONAR BLOQUEO DE USUARIO")
    print("="*60)
    
    usuario_id = input("\n🔢 ID del usuario: ").strip()
    
    print("\nNuevo estado:")
    print("  [1] Activo")
    print("  [2] Bloqueado")
    print("  [3] Inactivo")
    estado_op = input("Estado: ").strip()
    
    estado_map = {"1": "ACTIVO", "2": "BLOQUEADO", "3": "INACTIVO"}
    estado = estado_map.get(estado_op)
    
    if not usuario_id.isdigit() or not estado:
        print("\n❌ Datos inválidos")
        return
    
    print(f"\n⏳ Actualizando estado del usuario a {estado}...")
    status, data = send_to_bus("multa", "update_bloqueo", {
        "usuario_id": int(usuario_id),
        "estado": estado
    })
    print_response(status, data)

def actualizar_estado_item():
    """Actualizar el estado de un item físico"""
    print("\n" + "="*60)
    print("  ACTUALIZAR ESTADO DE ITEM")
    print("="*60)
    
    item_id = input("\n🔢 ID del item: ").strip()
    
    print("\nNuevo estado:")
    print("  [1] Disponible")
    print("  [2] No disponible")
    print("  [3] Perdido")
    print("  [4] Dañado")
    estado_op = input("Estado: ").strip()
    
    estado_map = {
        "1": "DISPONIBLE",
        "2": "NO_DISPONIBLE",
        "3": "PERDIDO",
        "4": "DAÑADO"
    }
    estado = estado_map.get(estado_op)
    
    if not item_id.isdigit() or not estado:
        print("\n❌ Datos inválidos")
        return
    
    print(f"\n⏳ Actualizando estado del item a {estado}...")
    status, data = send_to_bus("prart", "update_item_estado", {
        "item_id": int(item_id),
        "estado": estado
    })
    print_response(status, data)

# ============================================
# MÓDULO: MI PERFIL
# ============================================

def menu_perfil():
    """Menú de perfil de usuario"""
    while True:
        print("\n" + "="*60)
        print("  👤 MI PERFIL")
        print("="*60)
        print("\n[1] Ver mis datos")
        print("[2] Actualizar mis datos")
        print("[0] Volver al menú principal")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_mis_datos()
        elif opcion == "2":
            actualizar_mis_datos()
        elif opcion == "0":
            break
        else:
            print("\n❌ Opción inválida")
        
        if opcion != "0":
            input("\nPresione Enter para continuar...")

def ver_mis_datos():
    """Ver los datos del usuario actual"""
    print("\n⏳ Consultando datos...")
    status, data = send_to_bus("regis", "get_user", {
        "id": session.user_id
    })
    print_response(status, data, show_success=False)

def actualizar_mis_datos():
    """Actualizar datos del usuario actual"""
    print("\n" + "="*60)
    print("  ACTUALIZAR MIS DATOS")
    print("="*60)
    print("\nIngrese los nuevos valores (Enter para mantener):")
    
    datos = {}
    
    nombre = input("👤 Nombre: ").strip()
    if nombre:
        datos["nombre"] = nombre
    
    telefono = input("📱 Teléfono: ").strip()
    if telefono:
        datos["telefono"] = telefono
    
    if not datos:
        print("\n⚠️  No hay datos para actualizar")
        return
    
    print("\n⏳ Actualizando datos...")
    status, data = send_to_bus("regis", "update_user", {
        "id": session.user_id,
        "datos": datos
    })
    
    if print_response(status, data):
        # Actualizar sesión si se cambió el nombre
        if "nombre" in datos:
            session.user_name = datos["nombre"]

# ============================================
# MENÚ PRINCIPAL
# ============================================

def menu_principal():
    """Menú principal del sistema"""
    while session.logged_in:
        print("\n" + "="*60)
        print(f"  📚 PRESTALAB - Sistema de Préstamos Bibliotecarios")
        print("="*60)
        print(f"\n  Usuario: {session.user_name} ({session.user_type})")
        print("="*60)
        print("\n[1] 📖 Catálogo de Items")
        print("[2] 📋 Mis Solicitudes y Préstamos")
        print("[3] 💰 Mis Multas")
        print("[4] ⏳ Listas de Espera")
        print("[5] 💡 Sugerencias")
        print("[6] 📊 Reportes e Historial")
        print("[7] 🔔 Notificaciones y Preferencias")
        print("[8] 👤 Mi Perfil")
        
        if session.is_admin():
            print("\n--- Administración ---")
            print("[9] ⚙️  Panel de Administración")
        
        print("\n[0] 🚪 Cerrar Sesión")
        
        opcion = input("\n👉 Seleccione una opción: ").strip()
        
        if opcion == "1":
            menu_catalogo()
        elif opcion == "2":
            menu_solicitudes()
        elif opcion == "3":
            menu_multas()
        elif opcion == "4":
            menu_lista_espera()
        elif opcion == "5":
            menu_sugerencias()
        elif opcion == "6":
            menu_reportes()
        elif opcion == "7":
            menu_notificaciones()
        elif opcion == "8":
            menu_perfil()
        elif opcion == "9" and session.is_admin():
            menu_admin()
        elif opcion == "0":
            print(f"\n👋 Hasta pronto, {session.user_name}!")
            session.logout()
        else:
            print("\n❌ Opción inválida")

# ============================================
# PUNTO DE ENTRADA
# ============================================

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("  📚 PRESTALAB - Sistema de Préstamos Bibliotecarios")
    print("  🔧 Arquitectura Orientada a Servicios (SOA)")
    print("="*60)
    print("\n  ℹ️  INFORMACIÓN IMPORTANTE:")
    print("  • Este cliente se conecta al Bus SOA en localhost:5000")
    print("  • Asegúrese de tener docker-compose ejecutándose")
    print("  • Comando: cd backend && docker-compose up -d")
    print("  • Ver logs: docker logs -f soa_bus")
    print("="*60)
    
    input("\nPresione Enter para continuar...")
    
    # Verificar conectividad con el bus
    print("\n⏳ Verificando conexión con el Bus SOA...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(BUS_ADDRESS)
        sock.close()
        print("✅ Conexión exitosa con el Bus SOA")
    except Exception as e:
        print(f"\n❌ ERROR: No se pudo conectar al Bus SOA")
        print(f"   {str(e)}")
        print("\n   Asegúrese de ejecutar:")
        print("   cd backend && docker-compose up -d")
        input("\nPresione Enter para salir...")
        return
    
    # Bucle principal
    while True:
        menu_autenticacion()
        if session.logged_in:
            menu_principal()
        else:
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Sistema interrumpido por el usuario")
        print("👋 Gracias por usar PrestaLab\n")
    except Exception as e:
        print(f"\n\n❌ Error general del sistema: {e}")
        import traceback
        traceback.print_exc()
