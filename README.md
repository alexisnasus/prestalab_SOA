# PrestaLab SOA

Sistema de préstamos bibliotecarios con **Arquitectura Orientada a Servicios (SOA)** y **Enterprise Service Bus (ESB)**.

---

## 📋 Arquitectura del Sistema

```
                        ┌─────────────┐
                        │  CLIENTES   │
                        └──────┬──────┘
                               │
                    ┌──────────▼──────────┐
                    │  🚌 ESB (Bus SOA)   │  ← Service Registry + Discovery
                    │  localhost:8000     │     Message Router + Monitoring
                    └──────────┬──────────┘     Persistencia SQLite
                               │
        ┌──────┬──────┬────────┼────────┬──────┬──────┐
        ▼      ▼      ▼        ▼        ▼      ▼      ▼
     GEREP  LISTA  MULTA    NOTIS    PRART  REGIST SUGIT
     :8001  :8002  :8003    :8004    :8005  :8006  :8007
        │      │      │        │        │      │      │
        └──────┴──────┴────────┴────────┴──────┴──────┘
                              │
                       ┌──────▼──────┐
                       │  MySQL DB   │
                       │   :3307     │
                       └─────────────┘
```

### Componentes Principales

| Componente | Puerto | Función |
|------------|--------|---------|
| **ESB (Bus)** | 8000 | Orquestador central: registro, descubrimiento, enrutamiento |
| **GEREP** | 8001 | Gestión de reportes e historial |
| **LISTA** | 8002 | Gestión de listas de espera |
| **MULTA** | 8003 | Gestión de multas y bloqueos |
| **NOTIS** | 8004 | Gestión de notificaciones multicanal |
| **PRART** | 8005 | Gestión de préstamos y artículos |
| **REGIST** | 8006 | Registro y autenticación de usuarios |
| **SUGIT** | 8007 | Gestión de sugerencias |
| **MySQL** | 3307 | Base de datos principal |
| **phpMyAdmin** | 8080 | Administración de BD |

### Características del ESB

✅ **Auto-registro** - Servicios se registran automáticamente al iniciar  
✅ **Health Monitoring** - Monitoreo de salud cada 30s
✅ **Persistencia SQLite** - Registro sobrevive reinicios  
✅ **Logs Centralizados** - Historial de comunicaciones

---

## 🚀 Comandos Esenciales

### Levantar Sistema

**Primera vez (con rebuild):**

```bash
cd backend
docker-compose down --volumes --remove-orphans
docker-compose up --build
```

**Ejecuciones posteriores:**

```bash
cd backend
docker-compose up -d
```

### Detener Sistema

```bash
cd backend
docker-compose down
```

### Eliminar Todo (Contenedores + Volúmenes + Redes)

```bash
cd backend
docker-compose down --volumes --remove-orphans
```

### Reconstruir Imágenes (Después de cambios en código)

```bash
cd backend
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Ver Logs

```bash
# Logs del bus
docker logs -f soa_bus

# Logs de un servicio específico
docker logs -f soa_regist

# Logs de todos los servicios
docker-compose logs -f
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo el bus
docker-compose restart bus

# Reiniciar un servicio específico
docker-compose restart regist
```

---

## 📊 Endpoints del Bus

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/ping` | GET | Health check del bus |
| `/` | GET | Información del bus |
| `/discover` | GET | Lista todos los servicios registrados |
| `/register` | POST | Registro de servicios (automático) |
| `/unregister/{service}` | DELETE | Desregistrar un servicio |
| `/route` | POST | Enrutar mensaje a un servicio |
| `/health/{service}` | GET | Estado de un servicio específico |
| `/heartbeat/{service}` | POST | Enviar latido de vida |
| `/broadcast` | POST | Enviar mensaje a todos los servicios |
| `/logs` | GET | Logs de mensajes enrutados |
| `/stats` | GET | Estadísticas del bus |
| `/docs` | GET | Documentación interactiva (Swagger) |

---

## 🔧 Gestión de Servicios

### Registrar un Servicio

**PowerShell:**

```powershell
$body = @{
    service_name = "mi_servicio"
    service_url = "http://localhost:8010"
    description = "Mi nuevo servicio"
    version = "1.0.0"
    endpoints = @("/users", "/health")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/register" -Method Post -ContentType "application/json" -Body $body
```

**Bash:**

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "mi_servicio",
    "service_url": "http://localhost:8010",
    "description": "Mi nuevo servicio",
    "version": "1.0.0",
    "endpoints": ["/users", "/health"]
  }'
```

### Desregistrar un Servicio

**PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/unregister/mi_servicio" -Method Delete
```

**Bash:**

```bash
curl -X DELETE http://localhost:8000/unregister/mi_servicio
```

### Enviar Heartbeat

**PowerShell:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/heartbeat/mi_servicio" -Method Post
```

**Bash:**

```bash
curl -X POST http://localhost:8000/heartbeat/mi_servicio
```

---

## 🔍 Monitoreo y Trazabilidad del Sistema

El sistema incluye **logs detallados con colores** y **trazabilidad de transacciones** mediante Trace IDs únicos.

### Monitor Automático (Recomendado)

**Ejecutar en una terminal PowerShell:**

```powershell
cd backend
.\monitor_services.ps1
```

**¿Qué hace?**

1. Levanta todos los servicios con `docker-compose up -d`
2. Abre 8 ventanas de PowerShell (una por cada servicio + bus)
3. Muestra logs en tiempo real con colores:
   - 🟦 **Cyan**: Requests recibidos
   - 🟩 **Green**: Respuestas exitosas
   - 🟥 **Red**: Errores
   - 🟨 **Yellow**: Warnings y consultas SQL
   - 🟪 **Magenta**: Registros de servicios

4. **Al presionar cualquier tecla**: Cierra todas las ventanas y detiene los servicios automáticamente

### Ver Logs Manualmente

```bash
# Logs del bus (muestra Trace IDs y enrutamiento)
docker logs -f soa_bus

# Logs de un servicio específico
docker logs -f soa_regist

# Todos los logs mezclados
docker-compose logs -f
```

### Endpoints de Monitoreo

| Endpoint | Descripción |
|----------|-------------|
| `GET /stats` | Estadísticas del bus (requests, errores, etc.) |
| `GET /discover` | Servicios registrados y su estado |
| `GET /logs?limit=50` | Últimos logs de comunicación |
| `GET /health/{service}` | Estado de salud de un servicio |

### Cómo Funciona la Trazabilidad

1. **Trace ID Único**: Cada request que entra al bus recibe un UUID único
2. **Propagación**: El Trace ID se propaga a través del bus → servicio → base de datos
3. **Logs Correlacionados**: Todos los logs comparten el mismo Trace ID, permitiendo seguir una transacción completa
4. **Medición de Latencia**: Se mide el tiempo desde que llega al bus hasta que se envía la respuesta
5. **Persistencia**: Los logs se guardan en SQLite (`bus_data/bus_data.db`) y se muestran en consola

---

## 🎯 Operaciones de Servicios (SOA)

### REGIST - Gestión de Usuarios (Puerto 8006)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/usuarios` | Registrar nuevo usuario |
| POST | `/auth/login` | Autenticar usuario |
| GET | `/usuarios/{id}` | Consultar usuario por ID |
| PUT | `/usuarios/{id}` | Actualizar datos de usuario |
| PUT | /solicitudes-registro/{id}/actualizar | Aprobar o rechazar solicitud de registro |

### PRART - Préstamos & Artículos (Puerto 8005)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| GET | `/items?nombre=&tipo=` | Buscar artículos del catálogo |
| GET | `/solicitudes?usuario_id=&correo=` | Listar solicitudes de un usuario |
| POST | `/solicitudes` | Crear solicitud de préstamo |
| POST | `/reservas` | Crear reserva de artículo |
| DELETE | `/reservas/{id}` | Cancelar reserva |
| POST | `/prestamos` | Registrar préstamo |
| POST | `/devoluciones` | Registrar devolución |
| PUT | `/prestamos/{id}/renovar` | Renovar préstamo |
| PUT | `/items/{existencia_id}/estado` | Actualizar estado de artículo |

### MULTA - Multas & Bloqueos (Puerto 8003)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| GET | `/usuarios/{id}/multas` | Consultar multas de usuario |
| POST | `/multas` | Registrar nueva multa |
| PUT | `/usuarios/{id}/estado` | Cambiar estado de usuario (bloquear/desbloquear) |

### LISTA - Listas de Espera (Puerto 8002)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/lista-espera` | Agregar usuario a lista de espera |
| PUT | `/lista-espera/{id}` | Actualizar estado (ATENDIDA/CANCELADA). Body: `{"estado": "ATENDIDA"}` |
| GET | `/lista-espera/{item_id}` | Consultar lista de espera por artículo |

### NOTIS - Notificaciones (Puerto 8004)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/notificaciones` | Crear notificación |
| GET | `/preferencias/{usuario_id}` | Obtener preferencias de notificación |
| PUT | `/preferencias/{usuario_id}` | Actualizar preferencias de notificación |

### GEREP - Reportes & Historial (Puerto 8001)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| GET | `/usuarios/{id}/historial?formato=json\|csv\|pdf` | Historial de préstamos de usuario |
| GET | `/reportes/circulacion?periodo=YYYY-MM&sede_id=id` | Métricas de circulación por sede |

### SUGIT - Sugerencias (Puerto 8007)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/sugerencias` | Registrar sugerencia |
| GET | `/sugerencias` | Listar todas las sugerencias |
| PUT | `/sugerencias/{id}/aprobar` | Aprobar sugerencia |
| PUT | `/sugerencias/{id}/rechazar` | Rechazar sugerencia |

---

## 🧪 Ejemplos de Uso (cURL)

### REGIST - Aprobar/Rechazar Solicitudes

**Aprobar una solicitud:**

```bash
# Bash/Linux/Mac
curl -X PUT http://localhost:8006/solicitudes/1/actualizar \
  -H "Content-Type: application/json" \
  -d '{"estado": "APROBADA"}'
```

```powershell
# PowerShell
$body = @{ estado = "APROBADA" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8006/solicitudes/1/actualizar" `
  -Method Put `
  -ContentType "application/json" `
  -Body $body
```

**Rechazar una solicitud:**

```bash
# Bash/Linux/Mac
curl -X PUT http://localhost:8006/solicitudes/2/actualizar \
  -H "Content-Type: application/json" \
  -d '{"estado": "RECHAZADA"}'
```

```powershell
# PowerShell
$body = @{ estado = "RECHAZADA" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8006/solicitudes/2/actualizar" `
  -Method Put `
  -ContentType "application/json" `
  -Body $body
```

**Respuesta exitosa (200 OK):**

```json
{
  "message": "Solicitud 1 aprobada",
  "solicitud_id": 1,
  "nuevo_estado": "APROBADA"
}
```

**Errores posibles:**

- **404 Not Found**: Solicitud no existe
- **400 Bad Request**: Solicitud no está en estado PENDIENTE
- **422 Validation Error**: Estado debe ser "APROBADA" o "RECHAZADA"

---

### Comandos utiles

```bash
curl -X PUT http://localhost:8006/solicitudes/1/actualizar -H "Content-Type: application/json" -d "{\"estado\": \"APROBADA\"}"
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8006/solicitudes/1/actualizar" -Method Put -ContentType "application/json" -Body '{"estado": "APROBADA"}'
```