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
✅ **Service Discovery** - Descubrimiento dinámico de servicios  
✅ **Message Router** - Enrutamiento inteligente de mensajes  
✅ **Health Monitoring** - Monitoreo de salud cada 30s  
✅ **Persistencia SQLite** - Registro sobrevive reinicios  
✅ **Logs Centralizados** - Historial de comunicaciones  
✅ **Métricas** - Estadísticas por servicio  

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

## 🎯 Operaciones de Servicios (SOA)

### REGIST - Gestión de Usuarios (Puerto 8006)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/usuarios` | Registrar nuevo usuario |
| POST | `/auth/login` | Autenticar usuario |
| GET | `/usuarios/{id}` | Consultar usuario por ID |
| PUT | `/usuarios/{id}` | Actualizar datos de usuario |

### PRART - Préstamos & Artículos (Puerto 8005)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| GET | `/items?nombre=&tipo=` | Buscar artículos del catálogo |
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
| PUT | `/lista-espera/{id}` | Actualizar estado (ATENDIDA/CANCELADA) |
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
| GET | `/reportes/circulacion?periodo=YYYY-MM&sede=id` | Métricas de circulación por sede |

### SUGIT - Sugerencias (Puerto 8007)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check del servicio |
| POST | `/sugerencias` | Registrar sugerencia |
| GET | `/sugerencias` | Listar todas las sugerencias |
| PUT | `/sugerencias/{id}/aprobar` | Aprobar sugerencia |
| PUT | `/sugerencias/{id}/rechazar` | Rechazar sugerencia |

---
