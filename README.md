# PrestaLab SOA

Sistema de préstamos bibliotecarios con arquitectura orientada a servicios (SOA).

## 📋 Arquitectura

```
┌─────────────┐
│   Clientes  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  Enterprise Service Bus     │  ← Bus central con persistencia SQLite
│  http://localhost:8000      │
└─────────┬───────────────────┘
          │
          ├──────┬──────┬──────┬──────┬──────┬──────┐
          ▼      ▼      ▼      ▼      ▼      ▼      ▼
       GEREP  LISTA  MULTA  NOTIS  PRART  REGIST  SUGIT
       :8001  :8002  :8003  :8004  :8005  :8006   :8007
          │      │      │      │      │      │      │
          └──────┴──────┴──────┴──────┴──────┴──────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   MySQL DB   │
                    │   :3307      │
                    └──────────────┘
```

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Levantar sistema completo

**Primera vez:**
```bash
cd backend
docker-compose down --volumes --remove-orphans
docker-compose up --build
```

**Ejecuciones posteriores:**
```bash
cd backend
docker-compose up
```

---

## 🌐 Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Bus ESB** | 8000 | Enterprise Service Bus (registro, enrutamiento, monitoreo) |
| **phpMyAdmin** | 8080 | Administración de base de datos |
| **gerep** | 8001 | Gestión de Reportes (historial, estadísticas) |
| **lista** | 8002 | Gestión de Listas de Espera |
| **multa** | 8003 | Gestión de Multas y bloqueos |
| **notis** | 8004 | Gestión de Notificaciones |
| **prart** | 8005 | Gestión de Préstamos y Artículos |
| **regist** | 8006 | Registro y autenticación de usuarios |
| **sugit** | 8007 | Gestión de Sugerencias |

---

## 🚌 Enterprise Service Bus (ESB)

El bus es el componente central que orquesta la comunicación entre servicios.

### Características

✅ **Registro dinámico** - Los servicios se auto-registran al iniciar  
✅ **Service Discovery** - Descubrimiento automático de servicios  
✅ **Enrutamiento inteligente** - Enruta mensajes al servicio correcto  
✅ **Health Checks** - Monitoreo constante del estado de servicios  
✅ **Persistencia SQLite** - Sobrevive reinicios del bus  
✅ **Logs centralizados** - Historial de todas las comunicaciones  

### Endpoints principales

```bash
# Ver información del bus
GET http://localhost:8000/

# Descubrir servicios disponibles
GET http://localhost:8000/discover

# Enrutar mensaje a un servicio
POST http://localhost:8000/route
{
  "target_service": "regist",
  "method": "GET",
  "endpoint": "/usuarios/1"
}

# Ver estado de un servicio
GET http://localhost:8000/health/multa

# Ver logs de comunicaciones
GET http://localhost:8000/logs

# Ver estadísticas del bus
GET http://localhost:8000/stats
```

### Persistencia

El bus usa **SQLite** para persistir:
- Servicios registrados
- Logs de mensajes (últimos 1000)
- Estadísticas acumuladas

**Archivo:** `backend/Bus/bus_data.db`

**Ventajas:**
- ✅ Cero configuración (viene con Python)
- ✅ Solo 1 dependencia adicional (`aiosqlite`)
- ✅ Alto rendimiento (caché en memoria + SQLite)
- ✅ Los servicios persisten tras reinicios

---

## 🔧 Integración de Servicios con el Bus

Cada servicio debe registrarse en el bus al iniciar. Agregar en `app.py`:

```python
import os
import httpx
from fastapi import FastAPI

app = FastAPI(title="Mi Servicio")

BUS_URL = os.getenv("BUS_URL", "http://bus:8000")

@app.on_event("startup")
async def register_with_bus():
    """Registra el servicio en el bus al iniciar"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BUS_URL}/register",
                json={
                    "service_name": "mi_servicio",
                    "service_url": "http://mi_servicio:8000",
                    "description": "Descripción del servicio",
                    "version": "1.0.0",
                    "endpoints": ["/", "/endpoint1", "/endpoint2"]
                },
                timeout=5.0
            )
            print("✓ Registrado en el bus")
    except Exception as e:
        print(f"⚠ Error registrando en bus: {e}")
```

---

## 🧪 Testing

### Verificar que el bus funciona
```bash
curl http://localhost:8000/ping
```

### Ver servicios registrados
```bash
curl http://localhost:8000/discover
```

### Llamar a un servicio a través del bus
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "target_service": "regist",
    "method": "GET",
    "endpoint": "/usuarios/1"
  }'
```

### Verificar persistencia
```bash
# 1. Registrar un servicio de prueba
curl -X POST http://localhost:8000/register \
  -d '{"service_name":"test","service_url":"http://test:9000"}'

# 2. Reiniciar el bus
docker-compose restart bus

# 3. Verificar que el servicio persiste
curl http://localhost:8000/discover
# Debe mostrar "test" en la lista
```

---

## � Base de Datos

**Conexión MySQL:**
- Host: `localhost`
- Puerto: `3307`
- Usuario: `soa_user`
- Password: `soa_password`
- Base de datos: `soa_db`

**phpMyAdmin:** http://localhost:8080

---

## 🛠️ Desarrollo

### Agregar un nuevo servicio

1. Crear carpeta en `backend/services/nuevo_servicio/`
2. Crear `app.py` con FastAPI
3. Crear `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

4. Agregar al `docker-compose.yml`:
```yaml
nuevo_servicio:
  build: ./services/nuevo_servicio
  container_name: soa_nuevo_servicio
  environment:
    - DATABASE_URL=mysql+pymysql://soa_user:soa_password@db:3306/soa_db
    - BUS_URL=http://bus:8000
  depends_on:
    db:
      condition: service_healthy
    bus:
      condition: service_healthy
  ports:
    - "8008:8000"
```

5. Agregar código de registro en el bus (ver sección anterior)

---

## 📝 Cliente de Ejemplo

```python
import httpx
import asyncio

class SOAClient:
    def __init__(self, bus_url="http://localhost:8000"):
        self.bus_url = bus_url
    
    async def call_service(self, service_name, method, endpoint, payload=None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.bus_url}/route",
                json={
                    "target_service": service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "payload": payload
                }
            )
            result = response.json()
            if result.get("success"):
                return result.get("data")
            raise Exception(result.get("error"))

# Uso
async def main():
    client = SOAClient()
    
    # Obtener usuario
    usuario = await client.call_service("regist", "GET", "/usuarios/1")
    print(usuario)
    
    # Consultar multas
    multas = await client.call_service("multa", "GET", "/usuarios/1/multas")
    print(multas)

asyncio.run(main())
```

---

## 🔍 Logs y Monitoreo

### Ver logs del bus
```bash
docker logs -f soa_bus
```

### Ver logs de un servicio
```bash
docker logs -f soa_gerep
```

### Inspeccionar base de datos del bus
```bash
docker exec -it soa_bus sh
sqlite3 bus_data.db
SELECT * FROM services;
SELECT * FROM message_logs LIMIT 10;
```

---

## 🐛 Troubleshooting

### El bus no responde
```bash
# Verificar que esté corriendo
docker ps | grep bus

# Ver logs
docker logs soa_bus

# Reiniciar
docker-compose restart bus
```

### Servicios no se registran
- Verificar que `BUS_URL` esté configurado en el servicio
- Verificar que el bus esté corriendo antes que los servicios
- Revisar logs del servicio: `docker logs soa_servicio`

### Base de datos no conecta
```bash
# Verificar que MySQL esté saludable
docker ps

# Reiniciar contenedor de DB
docker-compose restart db
```

---

## 📚 Tecnologías

- **Python 3.11** - Lenguaje de programación
- **FastAPI** - Framework web asíncrono
- **MySQL 8.0** - Base de datos principal
- **SQLite** - Persistencia del bus
- **Docker** - Contenedorización
- **httpx** - Cliente HTTP asíncrono
- **SQLAlchemy** - ORM para MySQL
- **aiosqlite** - SQLite asíncrono

---

## 👥 Equipo

Proyecto desarrollado para el ramo **Arquitectura de Software 2025/S2**

---

## 📄 Licencia

Este proyecto es para uso académico.