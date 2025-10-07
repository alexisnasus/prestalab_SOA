"""
Enterprise Service Bus (ESB) - Arquitectura SOA
================================================
Este bus permite la comunicación centralizada entre servicios y clientes,
implementando registro dinámico, enrutamiento, descubrimiento y monitoreo.
Con persistencia SQLite para sobrevivir reinicios.
"""

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import asyncio
import logging
from enum import Enum
import aiosqlite
import json
import os
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SOA_BUS")

# Configuración de persistencia
DB_PATH = Path(os.getenv("BUS_DB_PATH", "./bus_data.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Enterprise Service Bus (ESB)",
    description="Bus de servicios para arquitectura SOA - PrestaLab (con persistencia SQLite)",
    version="2.0.0"
)

# ============================================================================
# MODELOS DE DATOS
# ============================================================================

class ServiceStatus(str, Enum):
    """Estados posibles de un servicio"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class ServiceInfo(BaseModel):
    """Información de un servicio registrado"""
    service_name: str = Field(..., description="Nombre único del servicio")
    service_url: str = Field(..., description="URL base del servicio")
    description: Optional[str] = Field(None, description="Descripción del servicio")
    version: Optional[str] = Field("1.0.0", description="Versión del servicio")
    endpoints: Optional[List[str]] = Field(default_factory=list, description="Endpoints disponibles")
    status: ServiceStatus = Field(ServiceStatus.UNKNOWN, description="Estado del servicio")
    last_heartbeat: Optional[datetime] = Field(None, description="Último latido recibido")
    registered_at: datetime = Field(default_factory=datetime.now, description="Fecha de registro")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MessageRequest(BaseModel):
    """Mensaje para enrutar a un servicio"""
    target_service: str = Field(..., description="Servicio destino")
    method: str = Field("GET", description="Método HTTP")
    endpoint: str = Field(..., description="Endpoint del servicio")
    payload: Optional[Dict[str, Any]] = Field(None, description="Datos a enviar")
    headers: Optional[Dict[str, str]] = Field(None, description="Headers adicionales")
    timeout: Optional[int] = Field(30, description="Timeout en segundos")


class MessageResponse(BaseModel):
    """Respuesta de un mensaje enrutado"""
    success: bool
    status_code: Optional[int] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# REGISTRO DE SERVICIOS CON PERSISTENCIA SQLITE
# ============================================================================

class ServiceRegistry:
    """Registro centralizado de servicios con persistencia SQLite"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}  # Caché en memoria
        self.message_logs: List[Dict] = []
        self.max_logs = 1000
        self.db_path = DB_PATH
        self._initialized = False
    
    async def initialize_db(self):
        """Inicializa la base de datos SQLite"""
        if self._initialized:
            return
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Tabla de servicios
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS services (
                        service_name TEXT PRIMARY KEY,
                        service_url TEXT NOT NULL,
                        description TEXT,
                        version TEXT DEFAULT '1.0.0',
                        endpoints TEXT,
                        status TEXT DEFAULT 'UNKNOWN',
                        last_heartbeat TEXT,
                        registered_at TEXT NOT NULL
                    )
                """)
                
                # Tabla de logs de mensajes
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS message_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        service TEXT NOT NULL,
                        method TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        status TEXT NOT NULL,
                        status_code INTEGER,
                        error TEXT
                    )
                """)
                
                # Tabla de estadísticas
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS statistics (
                        key TEXT PRIMARY KEY,
                        value INTEGER DEFAULT 0
                    )
                """)
                
                await db.commit()
                
            self._initialized = True
            logger.info(f"✓ Base de datos SQLite inicializada: {self.db_path}")
            
            # Cargar servicios existentes en la caché
            await self._load_services_from_db()
            
        except Exception as e:
            logger.error(f"✗ Error inicializando base de datos: {e}")
            raise
    
    async def _load_services_from_db(self):
        """Carga servicios desde SQLite a la caché en memoria"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT * FROM services") as cursor:
                    rows = await cursor.fetchall()
                    
                for row in rows:
                    service = ServiceInfo(
                        service_name=row[0],
                        service_url=row[1],
                        description=row[2],
                        version=row[3],
                        endpoints=json.loads(row[4]) if row[4] else [],
                        status=ServiceStatus(row[5]),
                        last_heartbeat=datetime.fromisoformat(row[6]) if row[6] else None,
                        registered_at=datetime.fromisoformat(row[7])
                    )
                    self.services[service.service_name] = service
                
                logger.info(f"✓ Cargados {len(self.services)} servicios desde SQLite")
        except Exception as e:
            logger.error(f"✗ Error cargando servicios: {e}")
    
    async def register(self, service: ServiceInfo) -> bool:
        """Registra un servicio (memoria + SQLite)"""
        try:
            service.status = ServiceStatus.ACTIVE
            service.last_heartbeat = datetime.now()
            
            # Guardar en memoria
            self.services[service.service_name] = service
            
            # Persistir en SQLite
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO services 
                    (service_name, service_url, description, version, endpoints, 
                     status, last_heartbeat, registered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    service.service_name,
                    service.service_url,
                    service.description,
                    service.version,
                    json.dumps(service.endpoints),
                    service.status.value,
                    service.last_heartbeat.isoformat(),
                    service.registered_at.isoformat()
                ))
                await db.commit()
            
            logger.info(f"✓ Servicio registrado: {service.service_name} @ {service.service_url}")
            await self._increment_stat("total_registrations")
            return True
        except Exception as e:
            logger.error(f"✗ Error registrando servicio {service.service_name}: {e}")
            return False
    
    async def unregister(self, service_name: str) -> bool:
        """Desregistra un servicio (memoria + SQLite)"""
        try:
            # Eliminar de memoria
            if service_name in self.services:
                del self.services[service_name]
            
            # Eliminar de SQLite
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM services WHERE service_name = ?", (service_name,))
                await db.commit()
            
            logger.info(f"✓ Servicio desregistrado: {service_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Error desregistrando servicio: {e}")
            return False
    
    def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Obtiene información de un servicio (desde memoria)"""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Obtiene todos los servicios registrados (desde memoria)"""
        return self.services
    
    async def update_heartbeat(self, service_name: str) -> bool:
        """Actualiza el último latido de un servicio"""
        try:
            if service_name in self.services:
                # Actualizar en memoria
                self.services[service_name].last_heartbeat = datetime.now()
                self.services[service_name].status = ServiceStatus.ACTIVE
                
                # Actualizar en SQLite
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        UPDATE services 
                        SET last_heartbeat = ?, status = ?
                        WHERE service_name = ?
                    """, (
                        datetime.now().isoformat(),
                        ServiceStatus.ACTIVE.value,
                        service_name
                    ))
                    await db.commit()
                
                return True
            return False
        except Exception as e:
            logger.error(f"✗ Error actualizando heartbeat: {e}")
            return False
    
    async def update_service_status(self, service_name: str, status: ServiceStatus):
        """Actualiza el estado de un servicio (memoria + SQLite)"""
        try:
            if service_name in self.services:
                # Actualizar en memoria
                self.services[service_name].status = status
                
                # Actualizar en SQLite
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        UPDATE services 
                        SET status = ?
                        WHERE service_name = ?
                    """, (status.value, service_name))
                    await db.commit()
        except Exception as e:
            logger.error(f"✗ Error actualizando estado: {e}")
    
    async def log_message(self, log_entry: Dict):
        """Registra un mensaje (memoria + SQLite)"""
        try:
            # Guardar en memoria
            self.message_logs.append(log_entry)
            if len(self.message_logs) > self.max_logs:
                self.message_logs = self.message_logs[-self.max_logs:]
            
            # Persistir en SQLite (solo últimos N)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO message_logs 
                    (timestamp, service, method, endpoint, status, status_code, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry.get("timestamp"),
                    log_entry.get("service"),
                    log_entry.get("method"),
                    log_entry.get("endpoint"),
                    log_entry.get("status"),
                    log_entry.get("status_code"),
                    log_entry.get("error")
                ))
                
                # Mantener solo últimos 1000 logs en SQLite
                await db.execute("""
                    DELETE FROM message_logs 
                    WHERE id NOT IN (
                        SELECT id FROM message_logs 
                        ORDER BY id DESC LIMIT ?
                    )
                """, (self.max_logs,))
                
                await db.commit()
        except Exception as e:
            logger.error(f"✗ Error guardando log: {e}")
    
    async def get_logs(self, limit: int = 100) -> List[Dict]:
        """Obtiene logs desde SQLite"""
        try:
            logs = []
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT timestamp, service, method, endpoint, status, status_code, error
                    FROM message_logs 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    
                for row in rows:
                    log = {
                        "timestamp": row[0],
                        "service": row[1],
                        "method": row[2],
                        "endpoint": row[3],
                        "status": row[4],
                    }
                    if row[5]:
                        log["status_code"] = row[5]
                    if row[6]:
                        log["error"] = row[6]
                    logs.append(log)
            
            return logs
        except Exception as e:
            logger.error(f"✗ Error obteniendo logs: {e}")
            return self.message_logs[-limit:]  # Fallback a memoria
    
    async def _increment_stat(self, key: str, value: int = 1):
        """Incrementa una estadística en SQLite"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO statistics (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = value + ?
                """, (key, value, value))
                await db.commit()
        except Exception as e:
            logger.error(f"✗ Error incrementando estadística: {e}")
    
    async def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas desde SQLite"""
        try:
            stats = {}
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT key, value FROM statistics") as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        stats[row[0]] = row[1]
            return stats
        except Exception as e:
            logger.error(f"✗ Error obteniendo estadísticas: {e}")
            return {}


# Instancia global del registro
registry = ServiceRegistry()


# ============================================================================
# HEALTH CHECKS Y MONITOREO
# ============================================================================

async def check_service_health(service_name: str, service_url: str) -> ServiceStatus:
    """Verifica el estado de salud de un servicio"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/")
            if response.status_code == 200:
                return ServiceStatus.ACTIVE
            else:
                return ServiceStatus.DEGRADED
    except httpx.TimeoutException:
        logger.warning(f"⚠ Timeout al verificar {service_name}")
        return ServiceStatus.DEGRADED
    except Exception as e:
        logger.error(f"✗ Error verificando {service_name}: {e}")
        return ServiceStatus.INACTIVE


async def monitor_services():
    """Monitorea constantemente el estado de los servicios"""
    while True:
        try:
            for service_name, service_info in registry.get_all_services().items():
                # Verificar si el servicio ha enviado heartbeat recientemente
                if service_info.last_heartbeat:
                    time_since_heartbeat = datetime.now() - service_info.last_heartbeat
                    if time_since_heartbeat > timedelta(minutes=5):
                        # Sin heartbeat en 5 minutos, verificar salud
                        status = await check_service_health(service_name, service_info.service_url)
                        await registry.update_service_status(service_name, status)
                        logger.info(f"Estado de {service_name}: {status}")
            
            await asyncio.sleep(30)  # Verificar cada 30 segundos
        except Exception as e:
            logger.error(f"Error en monitor: {e}")
            await asyncio.sleep(30)


# ============================================================================
# ENRUTAMIENTO DE MENSAJES
# ============================================================================

async def route_message(message: MessageRequest) -> MessageResponse:
    """Enruta un mensaje al servicio correspondiente"""
    
    # Verificar que el servicio existe
    service = registry.get_service(message.target_service)
    if not service:
        return MessageResponse(
            success=False,
            error=f"Servicio '{message.target_service}' no encontrado en el registro",
            service=message.target_service
        )
    
    # Verificar estado del servicio
    if service.status == ServiceStatus.INACTIVE:
        return MessageResponse(
            success=False,
            error=f"Servicio '{message.target_service}' está inactivo",
            service=message.target_service
        )
    
    # Construir URL completa
    url = f"{service.service_url}{message.endpoint}"
    
    # Registrar mensaje
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "service": message.target_service,
        "method": message.method,
        "endpoint": message.endpoint,
        "status": "PROCESSING"
    }
    
    try:
        async with httpx.AsyncClient(timeout=message.timeout) as client:
            # Seleccionar método HTTP
            if message.method.upper() == "GET":
                response = await client.get(url, params=message.payload, headers=message.headers or {})
            elif message.method.upper() == "POST":
                response = await client.post(url, json=message.payload, headers=message.headers or {})
            elif message.method.upper() == "PUT":
                response = await client.put(url, json=message.payload, headers=message.headers or {})
            elif message.method.upper() == "DELETE":
                response = await client.delete(url, headers=message.headers or {})
            else:
                raise ValueError(f"Método HTTP no soportado: {message.method}")
            
            # Parsear respuesta
            try:
                data = response.json()
            except:
                data = response.text
            
            log_entry["status"] = "SUCCESS"
            log_entry["status_code"] = response.status_code
            await registry.log_message(log_entry)
            await registry._increment_stat("total_messages")
            
            return MessageResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                data=data,
                service=message.target_service
            )
            
    except httpx.TimeoutException:
        log_entry["status"] = "TIMEOUT"
        await registry.log_message(log_entry)
        await registry._increment_stat("timeout_errors")
        return MessageResponse(
            success=False,
            error=f"Timeout al comunicarse con {message.target_service}",
            service=message.target_service
        )
    except Exception as e:
        log_entry["status"] = "ERROR"
        log_entry["error"] = str(e)
        await registry.log_message(log_entry)
        await registry._increment_stat("total_errors")
        return MessageResponse(
            success=False,
            error=f"Error: {str(e)}",
            service=message.target_service
        )


# ============================================================================
# ENDPOINTS DEL BUS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos y el monitoreo al arrancar el bus"""
    await registry.initialize_db()
    logger.info("🚀 Enterprise Service Bus iniciado con persistencia SQLite")
    asyncio.create_task(monitor_services())


@app.get("/")
def root():
    """Endpoint raíz del bus"""
    return {
        "message": "Enterprise Service Bus (ESB) - PrestaLab SOA",
        "version": "2.0.0",
        "status": "ACTIVE",
        "persistence": "SQLite",
        "db_path": str(DB_PATH),
        "registered_services": len(registry.get_all_services()),
        "endpoints": {
            "register": "POST /register - Registrar un servicio",
            "unregister": "DELETE /unregister/{service_name} - Desregistrar servicio",
            "discover": "GET /discover - Listar servicios disponibles",
            "route": "POST /route - Enrutar mensaje a un servicio",
            "health": "GET /health/{service_name} - Estado de un servicio",
            "heartbeat": "POST /heartbeat/{service_name} - Enviar latido",
            "logs": "GET /logs - Consultar logs de mensajes",
            "stats": "GET /stats - Estadísticas del bus"
        }
    }


@app.post("/register", status_code=201)
async def register_service(service: ServiceInfo):
    """Registra un nuevo servicio en el bus (con persistencia)"""
    if await registry.register(service):
        return {
            "message": f"Servicio '{service.service_name}' registrado exitosamente",
            "persistence": "SQLite",
            "service": service.dict()
        }
    raise HTTPException(status_code=500, detail="Error al registrar el servicio")


@app.delete("/unregister/{service_name}")
async def unregister_service(service_name: str):
    """Desregistra un servicio del bus (con persistencia)"""
    if await registry.unregister(service_name):
        return {"message": f"Servicio '{service_name}' desregistrado exitosamente"}
    raise HTTPException(status_code=404, detail=f"Servicio '{service_name}' no encontrado")


@app.get("/discover")
async def discover_services():
    """Lista todos los servicios registrados (Service Discovery)"""
    services = registry.get_all_services()
    return {
        "total_services": len(services),
        "persistence": "SQLite",
        "services": {
            name: {
                "url": info.service_url,
                "description": info.description,
                "version": info.version,
                "status": info.status.value,
                "endpoints": info.endpoints,
                "last_heartbeat": info.last_heartbeat.isoformat() if info.last_heartbeat else None
            }
            for name, info in services.items()
        }
    }


@app.post("/route")
async def route_request(message: MessageRequest):
    """Enruta un mensaje a un servicio específico"""
    response = await route_message(message)
    return response


@app.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """Obtiene el estado de salud de un servicio"""
    service = registry.get_service(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Servicio '{service_name}' no encontrado")
    
    # Realizar check en tiempo real
    status = await check_service_health(service_name, service.service_url)
    await registry.update_service_status(service_name, status)
    
    return {
        "service": service_name,
        "status": status.value,
        "url": service.service_url,
        "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None
    }


@app.post("/heartbeat/{service_name}")
async def service_heartbeat(service_name: str):
    """Recibe latido (heartbeat) de un servicio"""
    if await registry.update_heartbeat(service_name):
        return {"message": f"Heartbeat recibido de '{service_name}'"}
    raise HTTPException(status_code=404, detail=f"Servicio '{service_name}' no registrado")


@app.get("/logs")
async def get_message_logs(limit: int = 100):
    """Obtiene los logs de mensajes enrutados desde SQLite"""
    logs = await registry.get_logs(limit)
    return {
        "total_logs": len(logs),
        "showing": len(logs),
        "logs": logs,
        "persistence": "SQLite"
    }


@app.get("/stats")
async def get_statistics():
    """Obtiene estadísticas del bus desde SQLite"""
    services = registry.get_all_services()
    active = sum(1 for s in services.values() if s.status == ServiceStatus.ACTIVE)
    inactive = sum(1 for s in services.values() if s.status == ServiceStatus.INACTIVE)
    degraded = sum(1 for s in services.values() if s.status == ServiceStatus.DEGRADED)
    
    db_stats = await registry.get_stats()
    
    return {
        "total_services": len(services),
        "active_services": active,
        "inactive_services": inactive,
        "degraded_services": degraded,
        "total_messages": db_stats.get("total_messages", 0),
        "total_errors": db_stats.get("total_errors", 0),
        "timeout_errors": db_stats.get("timeout_errors", 0),
        "total_registrations": db_stats.get("total_registrations", 0),
        "persistence": "SQLite"
    }


# ============================================================================
# ENDPOINTS DE UTILIDAD
# ============================================================================

@app.post("/broadcast")
async def broadcast_message(message: Dict[str, Any] = Body(...)):
    """
    Envía un mensaje a todos los servicios registrados
    Útil para notificaciones globales o actualizaciones
    """
    services = registry.get_all_services()
    results = {}
    
    for service_name in services.keys():
        try:
            msg_request = MessageRequest(
                target_service=service_name,
                method="POST",
                endpoint="/broadcast",
                payload=message,
                timeout=10
            )
            response = await route_message(msg_request)
            results[service_name] = {
                "success": response.success,
                "status_code": response.status_code
            }
        except Exception as e:
            results[service_name] = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "message": "Broadcast completado",
        "results": results
    }


@app.get("/ping")
async def ping():
    """Simple ping para verificar que el bus está vivo"""
    return {"status": "pong", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
