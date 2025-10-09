"""
Bus Client - Módulo reutilizable para registro en el ESB
=========================================================
Este módulo permite a cualquier servicio registrarse automáticamente
en el Enterprise Service Bus (ESB) siguiendo patrones SOA.

Uso:
    from bus_client import register_service
    
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        await register_service(
            app=app,
            service_name="mi_servicio",
            service_url="http://mi_servicio:8000",
            description="Mi servicio SOA"
        )
"""

import httpx
import asyncio
import os
from typing import List, Optional
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

# Configuración del bus desde variables de entorno
BUS_URL = os.getenv("BUS_URL", "http://bus:8000")
MAX_RETRIES = int(os.getenv("BUS_REGISTER_RETRIES", "5"))
RETRY_DELAY = int(os.getenv("BUS_REGISTER_DELAY", "3"))


async def register_service(
    app: FastAPI,
    service_name: str,
    service_url: str,
    description: Optional[str] = None,
    version: str = "1.0.0",
    custom_endpoints: Optional[List[str]] = None
) -> bool:
    """
    Registra un servicio en el Enterprise Service Bus.
    
    Args:
        app: Instancia de FastAPI
        service_name: Nombre único del servicio (ej: "regist", "multa")
        service_url: URL base del servicio (ej: "http://regist:8000")
        description: Descripción del servicio
        version: Versión del servicio
        custom_endpoints: Lista personalizada de endpoints (opcional)
    
    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    
    Ejemplo:
        @app.on_event("startup")
        async def startup():
            await register_service(
                app=app,
                service_name="regist",
                service_url="http://regist:8000",
                description="Gestión de usuarios y autenticación"
            )
    """
    
    # Extraer endpoints de la aplicación FastAPI si no se proporcionan
    if custom_endpoints is None:
        endpoints = []
        for route in app.routes:
            if hasattr(route, "path"):
                endpoints.append(route.path)
        endpoints = list(set(endpoints))  # Eliminar duplicados
    else:
        endpoints = custom_endpoints
    
    # Datos de registro
    registration_data = {
        "service_name": service_name,
        "service_url": service_url,
        "description": description or f"Servicio {service_name}",
        "version": version,
        "endpoints": endpoints
    }
    
    # Intentar registro con reintentos
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{BUS_URL}/register",
                    json=registration_data
                )
                
                if response.status_code in [200, 201]:
                    logger.info(
                        f"✓ Servicio '{service_name}' registrado exitosamente en el bus "
                        f"({len(endpoints)} endpoints)"
                    )
                    return True
                else:
                    logger.warning(
                        f"⚠ Bus respondió con código {response.status_code}: {response.text}"
                    )
                    
        except httpx.ConnectError:
            logger.warning(
                f"⚠ Intento {attempt}/{MAX_RETRIES}: Bus no disponible en {BUS_URL}"
            )
        except Exception as e:
            logger.error(f"⚠ Error registrando servicio: {type(e).__name__}: {e}")
        
        # Esperar antes del siguiente intento (excepto en el último)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
    
    # Si llegamos aquí, todos los intentos fallaron
    logger.error(
        f"✗ No se pudo registrar '{service_name}' en el bus tras {MAX_RETRIES} intentos. "
        f"El servicio continuará funcionando pero no será descubrible."
    )
    return False


async def send_heartbeat(service_name: str) -> bool:
    """
    Envía un heartbeat al bus para indicar que el servicio está activo.
    
    Args:
        service_name: Nombre del servicio
    
    Returns:
        bool: True si el heartbeat fue exitoso
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{BUS_URL}/heartbeat/{service_name}"
            )
            return response.status_code == 200
    except Exception as e:
        logger.debug(f"Heartbeat falló: {e}")
        return False


def setup_heartbeat(service_name: str, interval: int = 30):
    """
    Configura un heartbeat periódico al bus (opcional, recomendado para producción).
    
    Args:
        service_name: Nombre del servicio
        interval: Intervalo en segundos entre heartbeats
    
    Ejemplo:
        @app.on_event("startup")
        async def startup():
            await register_service(...)
            setup_heartbeat("mi_servicio", interval=30)
    """
    async def heartbeat_task():
        while True:
            await asyncio.sleep(interval)
            await send_heartbeat(service_name)
    
    asyncio.create_task(heartbeat_task())


async def call_service_via_bus(
    target_service: str,
    method: str,
    endpoint: str,
    payload: Optional[dict] = None,
    timeout: int = 30
) -> dict:
    """
    Llama a otro servicio a través del bus (comunicación servicio-a-servicio).
    
    Args:
        target_service: Nombre del servicio destino
        method: Método HTTP (GET, POST, PUT, DELETE)
        endpoint: Endpoint del servicio
        payload: Datos a enviar (opcional)
        timeout: Timeout en segundos
    
    Returns:
        dict: Respuesta del servicio
    
    Ejemplo:
        # Desde el servicio 'multa', llamar al servicio 'regist'
        usuario = await call_service_via_bus(
            target_service="regist",
            method="GET",
            endpoint="/usuarios/123"
        )
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{BUS_URL}/route",
                json={
                    "target_service": target_service,
                    "method": method,
                    "endpoint": endpoint,
                    "payload": payload
                }
            )
            result = response.json()
            
            if result.get("success"):
                return result.get("data")
            else:
                raise Exception(result.get("error", "Error desconocido"))
                
    except Exception as e:
        logger.error(f"Error llamando a {target_service}: {e}")
        raise
