"""
Ejemplo de Cliente para comunicarse con el Bus SOA
===================================================
Este script muestra cómo un cliente puede usar el bus para comunicarse
con los diferentes servicios sin conocer sus URLs directas.
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
import json


class SOAClient:
    """Cliente para interactuar con el Enterprise Service Bus"""
    
    def __init__(self, bus_url: str = "http://localhost:8000"):
        self.bus_url = bus_url
        self.timeout = 30
    
    async def discover_services(self) -> Dict:
        """Descubre todos los servicios disponibles"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bus_url}/discover")
            return response.json()
    
    async def get_service_health(self, service_name: str) -> Dict:
        """Obtiene el estado de salud de un servicio"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bus_url}/health/{service_name}")
            return response.json()
    
    async def call_service(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Llama a un servicio a través del bus
        
        Args:
            service_name: Nombre del servicio (gerep, lista, multa, etc.)
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint del servicio (/usuarios/123, etc.)
            payload: Datos a enviar (opcional)
            timeout: Timeout en segundos
        
        Returns:
            Respuesta del servicio
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.bus_url}/route",
                json={
                    "target_service": service_name,
                    "method": method.upper(),
                    "endpoint": endpoint,
                    "payload": payload,
                    "timeout": timeout
                },
                timeout=timeout + 5  # Timeout del cliente > timeout del mensaje
            )
            result = response.json()
            
            if not result.get("success"):
                raise Exception(f"Error: {result.get('error')}")
            
            return result.get("data")
    
    async def get_bus_stats(self) -> Dict:
        """Obtiene estadísticas del bus"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.bus_url}/stats")
            return response.json()


# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

async def ejemplo_registro_usuario():
    """Ejemplo: Registrar un nuevo usuario"""
    print("\n=== Ejemplo 1: Registrar Usuario ===")
    client = SOAClient()
    
    try:
        resultado = await client.call_service(
            service_name="regist",
            method="POST",
            endpoint="/usuarios",
            payload={
                "id": 99999,
                "nombre": "Juan Pérez",
                "correo": "juan.perez@example.com",
                "tipo": "ESTUDIANTE",
                "telefono": "123456789",
                "estado": "ACTIVO",
                "preferencias_notificacion": "EMAIL,SMS"
            }
        )
        print(f"✓ Usuario registrado: {json.dumps(resultado, indent=2)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_consultar_usuario():
    """Ejemplo: Consultar información de un usuario"""
    print("\n=== Ejemplo 2: Consultar Usuario ===")
    client = SOAClient()
    
    try:
        usuario = await client.call_service(
            service_name="regist",
            method="GET",
            endpoint="/usuarios/1"
        )
        print(f"✓ Usuario encontrado: {json.dumps(usuario, indent=2, default=str)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_multas_usuario():
    """Ejemplo: Consultar multas de un usuario"""
    print("\n=== Ejemplo 3: Consultar Multas ===")
    client = SOAClient()
    
    try:
        multas = await client.call_service(
            service_name="multa",
            method="GET",
            endpoint="/usuarios/1/multas"
        )
        print(f"✓ Multas del usuario: {json.dumps(multas, indent=2, default=str)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_crear_sugerencia():
    """Ejemplo: Crear una sugerencia"""
    print("\n=== Ejemplo 4: Crear Sugerencia ===")
    client = SOAClient()
    
    try:
        resultado = await client.call_service(
            service_name="sugit",
            method="POST",
            endpoint="/sugerencias",
            payload={
                "usuario_id": 1,
                "sugerencia": "Sería útil tener una app móvil para préstamos"
            }
        )
        print(f"✓ Sugerencia registrada: {json.dumps(resultado, indent=2)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_lista_espera():
    """Ejemplo: Consultar lista de espera de un ítem"""
    print("\n=== Ejemplo 5: Consultar Lista de Espera ===")
    client = SOAClient()
    
    try:
        lista = await client.call_service(
            service_name="lista",
            method="GET",
            endpoint="/lista-espera/1"
        )
        print(f"✓ Lista de espera: {json.dumps(lista, indent=2, default=str)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_crear_notificacion():
    """Ejemplo: Crear una notificación"""
    print("\n=== Ejemplo 6: Crear Notificación ===")
    client = SOAClient()
    
    try:
        resultado = await client.call_service(
            service_name="notis",
            method="POST",
            endpoint="/notificaciones",
            payload={
                "usuario_id": 1,
                "canal": "EMAIL",
                "tipo": "RECORDATORIO",
                "mensaje": "Tu préstamo vence mañana"
            }
        )
        print(f"✓ Notificación creada: {json.dumps(resultado, indent=2)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_historial_usuario():
    """Ejemplo: Obtener historial de préstamos en formato JSON"""
    print("\n=== Ejemplo 7: Historial de Usuario ===")
    client = SOAClient()
    
    try:
        historial = await client.call_service(
            service_name="gerep",
            method="GET",
            endpoint="/usuarios/1/historial",
            payload={"formato": "json"}
        )
        print(f"✓ Historial: {json.dumps(historial, indent=2, default=str)}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_descubrir_servicios():
    """Ejemplo: Descubrir servicios disponibles"""
    print("\n=== Ejemplo 8: Descubrir Servicios ===")
    client = SOAClient()
    
    try:
        servicios = await client.discover_services()
        print(f"✓ Servicios disponibles: {servicios['total_services']}")
        for nombre, info in servicios['services'].items():
            print(f"  • {nombre}: {info['status']} - {info['description']}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_estadisticas_bus():
    """Ejemplo: Obtener estadísticas del bus"""
    print("\n=== Ejemplo 9: Estadísticas del Bus ===")
    client = SOAClient()
    
    try:
        stats = await client.get_bus_stats()
        print(f"✓ Estadísticas:")
        print(f"  • Total de servicios: {stats['total_services']}")
        print(f"  • Servicios activos: {stats['active_services']}")
        print(f"  • Servicios inactivos: {stats['inactive_services']}")
        print(f"  • Total de mensajes: {stats['total_messages']}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def ejemplo_flujo_completo():
    """Ejemplo: Flujo completo de usuario"""
    print("\n=== Ejemplo 10: Flujo Completo ===")
    client = SOAClient()
    
    try:
        # 1. Consultar usuario
        print("\n1. Consultando usuario...")
        usuario = await client.call_service("regist", "GET", "/usuarios/1")
        print(f"   Usuario: {usuario.get('nombre')}")
        
        # 2. Verificar multas
        print("\n2. Verificando multas...")
        multas = await client.call_service("multa", "GET", "/usuarios/1/multas")
        print(f"   Multas pendientes: {len(multas.get('multas', []))}")
        
        # 3. Consultar historial
        print("\n3. Consultando historial...")
        historial = await client.call_service(
            "gerep", "GET", "/usuarios/1/historial",
            payload={"formato": "json"}
        )
        print(f"   Préstamos históricos: {len(historial.get('historial', []))}")
        
        # 4. Crear notificación
        print("\n4. Creando notificación...")
        notif = await client.call_service(
            "notis", "POST", "/notificaciones",
            payload={
                "usuario_id": 1,
                "canal": "EMAIL",
                "tipo": "INFO",
                "mensaje": "Bienvenido al sistema"
            }
        )
        print(f"   Notificación creada: ID {notif.get('id')}")
        
        print("\n✓ Flujo completado exitosamente")
        
    except Exception as e:
        print(f"\n✗ Error en el flujo: {e}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Ejecuta todos los ejemplos"""
    print("=" * 70)
    print(" Cliente SOA - Ejemplos de Uso del Bus")
    print("=" * 70)
    
    # Verificar que el bus está disponible
    client = SOAClient()
    try:
        stats = await client.get_bus_stats()
        print(f"\n✓ Bus conectado - {stats['total_services']} servicios registrados")
    except Exception as e:
        print(f"\n✗ Error: No se puede conectar al bus: {e}")
        print("   Asegúrate de que el bus esté corriendo en http://localhost:8000")
        return
    
    # Ejecutar ejemplos
    print("\n" + "=" * 70)
    print(" Ejecutando Ejemplos")
    print("=" * 70)
    
    await ejemplo_descubrir_servicios()
    await ejemplo_estadisticas_bus()
    
    # Descomentar para probar otros ejemplos
    # await ejemplo_consultar_usuario()
    # await ejemplo_multas_usuario()
    # await ejemplo_crear_sugerencia()
    # await ejemplo_lista_espera()
    # await ejemplo_crear_notificacion()
    # await ejemplo_historial_usuario()
    # await ejemplo_flujo_completo()
    
    print("\n" + "=" * 70)
    print(" Ejemplos Completados")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
