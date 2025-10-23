# PrestaLab SOA# PrestaLab SOA



Sistema de préstamos bibliotecarios con **Arquitectura Orientada a Servicios (SOA)** y **Bus de Servicios TCP**.Sistema de préstamos bibliotecarios con **Arquitectura Orientada a Servicios (SOA)** y **Enterprise Service Bus (ESB)**.



------



## 📋 Arquitectura del Sistema## 📋 Arquitectura del Sistema



``````

                        ┌─────────────┐                        ┌─────────────┐

                        │  CLIENTES   │                        │  CLIENTES   │

                        └──────┬──────┘                        └──────┬──────┘

                               │                               │

                    ┌──────────▼──────────┐                    ┌──────────▼──────────┐

                    │  🚌 BUS SOA         │  ← Protocolo TCP Socket                    │  🚌 ESB (Bus SOA)   │  ← Service Registry + Discovery

                    │  localhost:5000     │     NNNNNSSSSSDATOS                    │  localhost:8000     │     Message Router + Monitoring

                    └──────────┬──────────┘                         └──────────┬──────────┘     Persistencia SQLite

                               │                               │

        ┌──────┬──────┬────────┼────────┬──────┬──────┐        ┌──────┬──────┬────────┼────────┬──────┬──────┐

        ▼      ▼      ▼        ▼        ▼      ▼      ▼        ▼      ▼      ▼        ▼        ▼      ▼      ▼

     GEREP  LISTA  MULTA    NOTIS    PRART  REGIS SUGIT     GEREP  LISTA  MULTA    NOTIS    PRART  REGIST SUGIT

                              │     :8001  :8002  :8003    :8004    :8005  :8006  :8007

                       ┌──────▼──────┐        │      │      │        │        │      │      │

                       │ MySQL:3307  │        └──────┴──────┴────────┴────────┴──────┴──────┘

                       │ phpMyAdmin  │                              │

                       │   :8088     │                       ┌──────▼──────┐

                       └─────────────┘                       │  MySQL DB   │

```                       │   :3307     │

                       └─────────────┘

### Componentes Principales```



| Componente | Puerto | Función |### Componentes Principales

|------------|--------|---------|

| **Bus SOA** | 5000 | Orquestador central con protocolo TCP binario || Componente | Puerto | Función |

| **GEREP** | - | Gestión de reportes e historial ||------------|--------|---------|

| **LISTA** | - | Gestión de listas de espera || **ESB (Bus)** | 8000 | Orquestador central: registro, descubrimiento, enrutamiento |

| **MULTA** | - | Gestión de multas y bloqueos || **GEREP** | 8001 | Gestión de reportes e historial |

| **NOTIS** | - | Gestión de notificaciones multicanal || **LISTA** | 8002 | Gestión de listas de espera |

| **PRART** | - | Gestión de préstamos y artículos || **MULTA** | 8003 | Gestión de multas y bloqueos |

| **REGIS** | - | Registro y autenticación de usuarios || **NOTIS** | 8004 | Gestión de notificaciones multicanal |

| **SUGIT** | - | Gestión de sugerencias || **PRART** | 8005 | Gestión de préstamos y artículos |

| **MySQL** | 3307 | Base de datos principal || **REGIST** | 8006 | Registro y autenticación de usuarios |

| **phpMyAdmin** | 8088 | Administración de BD || **SUGIT** | 8007 | Gestión de sugerencias |

| **MySQL** | 3307 | Base de datos principal |

> **Nota**: Los servicios no exponen puertos HTTP. Toda comunicación ocurre a través del Bus SOA usando sockets TCP.| **phpMyAdmin** | 8080 | Administración de BD |



---### Características del ESB



## 🔌 Protocolo del Bus SOA✅ **Auto-registro** - Servicios se registran automáticamente al iniciar  

✅ **Health Monitoring** - Monitoreo de salud cada 30s

El bus utiliza un **protocolo binario TCP** con la siguiente estructura:✅ **Persistencia SQLite** - Registro sobrevive reinicios  

✅ **Logs Centralizados** - Historial de comunicaciones

### Transacción de entrada (Cliente → Bus → Servicio):

```---

NNNNNSSSSSDATOS

```## 🚀 Comandos Esenciales

- **NNNNN**: Longitud total de lo que sigue (5 dígitos, ejemplo: `00029`)

- **SSSSS**: Nombre del servicio destino (5 caracteres, ejemplo: `regis`)### Levantar Sistema

- **DATOS**: Datos del requerimiento en formato `OPERACION {json_payload}`

**Primera vez (con rebuild):**

**Ejemplo - Login:**

``````bash

00029regislogin {"correo":"juan@mail.com","password":"123"}cd backend

```docker-compose down --volumes --remove-orphans

docker-compose up --build

**Desglose:**```

- `00029` → longitud de `regislogin {"correo":"juan@mail.com","password":"123"}`

- `regis` → servicio de registro/autenticación**Ejecuciones posteriores:**

- `login {"correo":"juan@mail.com","password":"123"}` → operación + datos JSON

```bash

### Transacción de salida (Servicio → Bus → Cliente):cd backend

```docker-compose up -d

NNNNNSSSSSSTDATOS```

```

- **NNNNN**: Longitud total de lo que sigue (5 dígitos)### Detener Sistema

- **SSSSS**: Nombre del servicio que responde (5 caracteres)

- **ST**: Status de la operación```bash

  - `OK` → Operación exitosacd backend

  - `NK` → Operación fallida (error)docker-compose down

- **DATOS**: Respuesta en formato JSON```



**Ejemplo exitoso:**### Eliminar Todo (Contenedores + Volúmenes + Redes)

```

00065regisOK{"message":"Usuario autenticado","token":"session-1","user":{...}}```bash

```cd backend

docker-compose down --volumes --remove-orphans

**Ejemplo de error:**```

```

00043regisNK{"error":"Credenciales inválidas"}### Reconstruir Imágenes (Después de cambios en código)

```

```bash

### Registro de Servicios (sinit):cd backend

Al iniciar, cada servicio se registra en el bus usando:docker-compose down

```docker-compose build --no-cache

00010sinitregisdocker-compose up -d

``````

- `00010` → longitud de `sinitregis`

- `sinit` → comando de inicialización### Ver Logs

- `regis` → nombre del servicio (5 caracteres)

```bash

El bus responde con:# Logs del bus

```docker logs -f soa_bus

00002OK

```# Logs de un servicio específico

docker logs -f soa_regist

---

# Logs de todos los servicios
docker-compose logs -f
```

---

## Comandos Esenciales

### Levantar Sistema

**Primera vez o después de cambios en código:**

```bash
cd backend
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up -d
```

**Verificar registro de servicios:**

```bash
docker logs soa_bus
# Deberías ver: "sinit recibido de regis", "sinit recibido de prart", etc.
```

**Ejecuciones normales:**

```bash
cd backend
docker-compose up -d
```

### Ver Logs

```bash
# Logs de un servicio
docker logs -f soa_regist

# Logs de todos
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

### Detener Sistema

| Endpoint | Método | Descripción |

```bash|----------|--------|-------------|

cd backend| `/ping` | GET | Health check del bus |

docker-compose down| `/` | GET | Información del bus |

```| `/discover` | GET | Lista todos los servicios registrados |

| `/register` | POST | Registro de servicios (automático) |

### Eliminar Todo (Contenedores + Volúmenes + Redes)| `/unregister/{service}` | DELETE | Desregistrar un servicio |

| `/route` | POST | Enrutar mensaje a un servicio |

```bash| `/health/{service}` | GET | Estado de un servicio específico |

cd backend| `/heartbeat/{service}` | POST | Enviar latido de vida |

docker-compose down --volumes --remove-orphans| `/broadcast` | POST | Enviar mensaje a todos los servicios |

```| `/logs` | GET | Logs de mensajes enrutados |

| `/stats` | GET | Estadísticas del bus |

### Reconstruir Imágenes (Después de cambios en código)| `/docs` | GET | Documentación interactiva (Swagger) |



```bash---

cd backend

docker-compose down## 🔧 Gestión de Servicios

docker-compose build --no-cache

docker-compose up -d### Registrar un Servicio

```

**PowerShell:**

### Ver Logs

```powershell

```bash$body = @{

# Logs del bus    service_name = "mi_servicio"

docker logs -f soa_bus    service_url = "http://localhost:8010"

    description = "Mi nuevo servicio"

# Logs de un servicio específico    version = "1.0.0"

docker logs -f soa_regist    endpoints = @("/users", "/health")

} | ConvertTo-Json

# Logs de todos los servicios

docker-compose logs -fInvoke-RestMethod -Uri "http://localhost:8000/register" -Method Post -ContentType "application/json" -Body $body

``````



### Reiniciar Servicios**Bash:**



```bash```bash

# Reiniciar todocurl -X POST http://localhost:8000/register \

docker-compose restart  -H "Content-Type: application/json" \

  -d '{

# Reiniciar solo el bus    "service_name": "mi_servicio",

docker-compose restart bus    "service_url": "http://localhost:8010",

    "description": "Mi nuevo servicio",

# Reiniciar un servicio específico    "version": "1.0.0",

docker-compose restart regist    "endpoints": ["/users", "/health"]

```  }'

```

---

### Desregistrar un Servicio

## 🎯 Operaciones de Servicios (SOA)

**PowerShell:**

### REGIS - Gestión de Usuarios

```powershell

**Nombre del servicio:** `regis`Invoke-RestMethod -Uri "http://localhost:8000/unregister/mi_servicio" -Method Delete

```

#### 1. Registrar Usuario

**Bash:**

**Transacción de entrada:**

``````bash

NNNNNregisregister {"nombre":"Juan Pérez","correo":"juan@mail.com","password":"123456","tipo":"ESTUDIANTE"}curl -X DELETE http://localhost:8000/unregister/mi_servicio

``````



**Campos del payload:**### Enviar Heartbeat

- `nombre` (string, requerido): Nombre completo

- `correo` (string, requerido): Email único**PowerShell:**

- `password` (string, requerido): Contraseña

- `tipo` (string, requerido): `ESTUDIANTE`, `DOCENTE`, `ADMIN````powershell

- `telefono` (string, opcional): Número de teléfonoInvoke-RestMethod -Uri "http://localhost:8000/heartbeat/mi_servicio" -Method Post

- `estado` (string, opcional): `ACTIVO` (por defecto), `BLOQUEADO````

- `preferencias_notificacion` (int, opcional): 1 (por defecto)

**Bash:**

**Respuesta exitosa (OK):**

```json```bash

{curl -X POST http://localhost:8000/heartbeat/mi_servicio

  "message": "Usuario registrado",```

  "user": {

    "id": 1,---

    "nombre": "Juan Pérez",

    "correo": "juan@mail.com",## 🔍 Monitoreo y Trazabilidad del Sistema

    "tipo": "ESTUDIANTE",

    "telefono": "",El sistema incluye **logs detallados con colores** y **trazabilidad de transacciones** mediante Trace IDs únicos.

    "estado": "ACTIVO",

    "preferencias_notificacion": 1,### Monitor Automático (Recomendado)

    "registro_instante": "2025-10-23T10:30:00"

  }**Ejecutar en una terminal PowerShell:**

}

``````powershell

cd backend

**Respuesta de error (NK):**.\monitor_services.ps1

```json```

{"error": "El correo ya está registrado"}

```**¿Qué hace?**



#### 2. Login (Autenticación)1. Levanta todos los servicios con `docker-compose up -d`

2. Abre 8 ventanas de PowerShell (una por cada servicio + bus)

**Transacción de entrada:**3. Muestra logs en tiempo real con colores:

```   - 🟦 **Cyan**: Requests recibidos

NNNNNregislogin {"correo":"juan@mail.com","password":"123456"}   - 🟩 **Green**: Respuestas exitosas

```   - 🟥 **Red**: Errores

   - 🟨 **Yellow**: Warnings y consultas SQL

**Respuesta exitosa (OK):**   - 🟪 **Magenta**: Registros de servicios

```json

{4. **Al presionar cualquier tecla**: Cierra todas las ventanas y detiene los servicios automáticamente

  "message": "Usuario juan@mail.com autenticado",

  "token": "session-1",### Ver Logs Manualmente

  "user": {

    "id": 1,```bash

    "nombre": "Juan Pérez",# Logs del bus (muestra Trace IDs y enrutamiento)

    "correo": "juan@mail.com",docker logs -f soa_bus

    "tipo": "ESTUDIANTE",

    "estado": "ACTIVO"# Logs de un servicio específico

  }docker logs -f soa_regist

}

```# Todos los logs mezclados

docker-compose logs -f

**Respuesta de error (NK):**```

```json

{"error": "Credenciales inválidas"}### Endpoints de Monitoreo

```

| Endpoint | Descripción |

#### 3. Consultar Usuario|----------|-------------|

| `GET /stats` | Estadísticas del bus (requests, errores, etc.) |

**Transacción de entrada:**| `GET /discover` | Servicios registrados y su estado |

```| `GET /logs?limit=50` | Últimos logs de comunicación |

NNNNNregisget_user {"id":1}| `GET /health/{service}` | Estado de salud de un servicio |

```

### Cómo Funciona la Trazabilidad

**Respuesta exitosa (OK):**

```json1. **Trace ID Único**: Cada request que entra al bus recibe un UUID único

{2. **Propagación**: El Trace ID se propaga a través del bus → servicio → base de datos

  "id": 1,3. **Logs Correlacionados**: Todos los logs comparten el mismo Trace ID, permitiendo seguir una transacción completa

  "nombre": "Juan Pérez",4. **Medición de Latencia**: Se mide el tiempo desde que llega al bus hasta que se envía la respuesta

  "correo": "juan@mail.com",5. **Persistencia**: Los logs se guardan en SQLite (`bus_data/bus_data.db`) y se muestran en consola

  "tipo": "ESTUDIANTE",

  "telefono": "",---

  "estado": "ACTIVO",

  "preferencias_notificacion": 1,## 🎯 Operaciones de Servicios (SOA)

  "registro_instante": "2025-10-23T10:30:00"

}### REGIST - Gestión de Usuarios (Puerto 8006)

```

| Método | Endpoint | Descripción |

**Respuesta de error (NK):**|--------|----------|-------------|

```json| GET | `/` | Health check del servicio |

{"error": "Usuario no encontrado"}| POST | `/usuarios` | Registrar nuevo usuario |

```| POST | `/auth/login` | Autenticar usuario |

| GET | `/usuarios/{id}` | Consultar usuario por ID |

#### 4. Actualizar Usuario| PUT | `/usuarios/{id}` | Actualizar datos de usuario |

| PUT | /solicitudes-registro/{id}/actualizar | Aprobar o rechazar solicitud de registro |

**Transacción de entrada:**

```### PRART - Préstamos & Artículos (Puerto 8005)

NNNNNregisupdate_user {"id":1,"datos":{"telefono":"555-1234","preferencias_notificacion":2}}

```| Método | Endpoint | Descripción |

|--------|----------|-------------|

**Respuesta exitosa (OK):**| GET | `/` | Health check del servicio |

```json| GET | `/items/all` | Obtener todos los artículos del catálogo |

{"message": "Usuario 1 actualizado"}| GET | `/items?nombre=&tipo=` | Buscar artículos del catálogo con filtros |

```| GET | `/solicitudes?usuario_id=&correo=` | Listar solicitudes de un usuario |

| POST | `/solicitudes` | Crear solicitud de préstamo |

**Respuesta de error (NK):**| POST | `/reservas` | Crear reserva de artículo |

```json| DELETE | `/reservas/{id}` | Cancelar reserva |

{"error": "Usuario no encontrado"}| POST | `/prestamos` | Registrar préstamo |

```| POST | `/devoluciones` | Registrar devolución |

| PUT | `/prestamos/{id}/renovar` | Renovar préstamo |

#### 5. Actualizar Solicitud de Registro| PUT | `/items/{existencia_id}/estado` | Actualizar estado de artículo |



**Transacción de entrada (aprobar):**### MULTA - Multas & Bloqueos (Puerto 8003)

```

NNNNNregisupdate_solicitud {"solicitud_id":1,"estado":"APROBADA"}| Método | Endpoint | Descripción |

```|--------|----------|-------------|

| GET | `/` | Health check del servicio |

**Transacción de entrada (rechazar):**| GET | `/usuarios/{id}/multas` | Consultar multas de usuario |

```| POST | `/multas` | Registrar nueva multa |

NNNNNregisupdate_solicitud {"solicitud_id":2,"estado":"RECHAZADA"}| PUT | `/usuarios/{id}/estado` | Cambiar estado de usuario (bloquear/desbloquear) |

```

### LISTA - Listas de Espera (Puerto 8002)

**Respuesta exitosa (OK):**

```json| Método | Endpoint | Descripción |

{"message": "Solicitud 1 actualizada a APROBADA"}|--------|----------|-------------|

```| GET | `/` | Health check del servicio |

| POST | `/lista-espera` | Agregar usuario a lista de espera |

**Respuestas de error (NK):**| PUT | `/lista-espera/{id}` | Actualizar estado (ATENDIDA/CANCELADA). Body: `{"estado": "ATENDIDA"}` |

```json| GET | `/lista-espera/{item_id}` | Consultar lista de espera por artículo |

{"error": "Solicitud no encontrada"}

{"error": "La solicitud ya fue procesada (estado: APROBADA)"}### NOTIS - Notificaciones (Puerto 8004)

{"error": "Faltan datos o el estado es inválido"}

```| Método | Endpoint | Descripción |

|--------|----------|-------------|

---| GET | `/` | Health check del servicio |

| POST | `/notificaciones` | Crear notificación |

### PRART - Préstamos & Artículos| GET | `/preferencias/{usuario_id}` | Obtener preferencias de notificación |

| PUT | `/preferencias/{usuario_id}` | Actualizar preferencias de notificación |

**Nombre del servicio:** `prart`

### GEREP - Reportes & Historial (Puerto 8001)

#### Operaciones disponibles:

- `get_all_items` - Obtener todos los artículos del catálogo| Método | Endpoint | Descripción |

- `search_items` - Buscar artículos con filtros (nombre, tipo)|--------|----------|-------------|

- `get_solicitudes` - Listar solicitudes de un usuario| GET | `/` | Health check del servicio |

- `create_solicitud` - Crear solicitud de préstamo| GET | `/usuarios/{id}/historial?formato=json\|csv\|pdf` | Historial de préstamos de usuario |

- `create_reserva` - Crear reserva de artículo| GET | `/reportes/circulacion?periodo=YYYY-MM&sede_id=id` | Métricas de circulación por sede |

- `cancel_reserva` - Cancelar reserva

- `create_prestamo` - Registrar préstamo### SUGIT - Sugerencias (Puerto 8007)

- `create_devolucion` - Registrar devolución

- `renovar_prestamo` - Renovar préstamo| Método | Endpoint | Descripción |

- `update_item_estado` - Actualizar estado de artículo|--------|----------|-------------|

| GET | `/` | Health check del servicio |

---| POST | `/sugerencias` | Registrar sugerencia |

| GET | `/sugerencias` | Listar todas las sugerencias |

### MULTA - Multas & Bloqueos| PUT | `/sugerencias/{id}/aprobar` | Aprobar sugerencia |

| PUT | `/sugerencias/{id}/rechazar` | Rechazar sugerencia |

**Nombre del servicio:** `multa`

---

#### Operaciones disponibles:

- `get_multas` - Consultar multas de usuario## 🧪 Ejemplos de Uso (cURL)

- `create_multa` - Registrar nueva multa

- `update_user_estado` - Cambiar estado de usuario (bloquear/desbloquear)### REGIST - Aprobar/Rechazar Solicitudes



---**Aprobar una solicitud:**



### LISTA - Listas de Espera

**Nombre del servicio:** `lista`

#### Operaciones disponibles:

- `create_lista_espera` - Agregar usuario a lista de espera
- `update_lista_espera` - Actualizar estado (ATENDIDA/CANCELADA)
- `get_lista_espera` - Consultar lista de espera por artículo

---

### NOTIS - Notificaciones

**Nombre del servicio:** `notis`

#### Operaciones disponibles:

- `create_notificacion` - Crear notificación
- `get_preferencias` - Obtener preferencias de notificación
- `update_preferencias` - Actualizar preferencias de notificación

---

### GEREP - Reportes & Historial

**Nombre del servicio:** `gerep`

#### Operaciones disponibles:

- `get_historial` - Historial de préstamos de usuario (formato: json/csv/pdf)
- `get_reporte_circulacion` - Métricas de circulación por sede

---

### SUGIT - Sugerencias

**Nombre del servicio:** `sugit`

#### Operaciones disponibles:

- `create_sugerencia` - Registrar sugerencia
- `get_sugerencias` - Listar todas las sugerencias
- `aprobar_sugerencia` - Aprobar sugerencia
- `rechazar_sugerencia` - Rechazar sugerencia

---



#### Operaciones disponibles:```json

- `create_sugerencia` - Registrar sugerencia{

- `get_sugerencias` - Listar todas las sugerencias  "message": "Solicitud 1 aprobada",

- `aprobar_sugerencia` - Aprobar sugerencia  "solicitud_id": 1,

- `rechazar_sugerencia` - Rechazar sugerencia

---

## 🧪 Ejemplo de Cliente Python

```python
import socket
import json

def send_to_bus(service_name, operation, payload):
    """
    Envía una transacción al bus y espera la respuesta.
    
    Args:
        service_name: Nombre del servicio (max 5 caracteres)
        operation: Operación a ejecutar
        payload: Diccionario con los datos
    """
    # Crear socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Conectar al bus
        sock.connect(('localhost', 5000))
        
        # Preparar mensaje: OPERACION {json_payload}
        data = f"{operation} {json.dumps(payload)}"
        
        # Preparar transacción: NNNNNSSSSSDATOS
        service_padded = service_name.ljust(5)[:5]
        message = f"{service_padded}{data}"
        message_len = len(message)
        formatted_message = f"{message_len:05d}{message}".encode('utf-8')
        
        print(f"Enviando: {formatted_message!r}")
        sock.sendall(formatted_message)
        
        # Esperar respuesta
        length_bytes = sock.recv(5)
        response_length = int(length_bytes.decode('utf-8'))
        
        response_data = b''
        while len(response_data) < response_length:
            chunk = sock.recv(response_length - len(response_data))
            if not chunk:
                break
            response_data += chunk
        
        response_str = response_data.decode('utf-8')
        print(f"Respuesta: {response_str!r}")
        
        # Parsear respuesta: SSSSSSTDATOS
        service_response = response_str[:5]
        status = response_str[5:7]  # OK o NK
        datos = response_str[7:]
        
        print(f"Servicio: {service_response.strip()}")
        print(f"Status: {status}")
        print(f"Datos: {datos}")
        
        return status, json.loads(datos)
        
    finally:
        sock.close()

# Ejemplo 1: Login
status, response = send_to_bus(
    'regis',
    'login',
    {'correo': 'juan@mail.com', 'password': '123456'}
)

if status == 'OK':
    print(f"Login exitoso! Token: {response['token']}")
else:
    print(f"Error: {response['error']}")

# Ejemplo 2: Registrar usuario
status, response = send_to_bus(
    'regis',
    'register',
    {
        'nombre': 'María García',
        'correo': 'maria@mail.com',
        'password': '123456',
        'tipo': 'ESTUDIANTE'
    }
)

if status == 'OK':
    print(f"Usuario registrado con ID: {response['user']['id']}")
else:
    print(f"Error: {response['error']}")
```

### Probar el Sistema

Crear archivo `test_bus.py` en directorio `backend`:

```python
import socket
import json

def send_to_bus(service, operation, payload):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 5000))
    
    data = f"{operation} {json.dumps(payload)}"
    service_padded = service.ljust(5)[:5]
    message = f"{service_padded}{data}"
    formatted = f"{message_len:05d}{message}".encode('utf-8')
    
    sock.sendall(formatted)
    
    length_bytes = sock.recv(5)
    response_length = int(length_bytes.decode('utf-8'))
    response_data = sock.recv(response_length).decode('utf-8')
    
    status = response_data[5:7]
    datos = response_data[7:]
    
    sock.close()
    return status, json.loads(datos)

# Probar registro
status, resp = send_to_bus('regis', 'register', {
    'nombre': 'Test User',
    'correo': 'test@mail.com',
    'password': '123456',
    'tipo': 'ESTUDIANTE'
})
print(f"Register: {status} - {resp}")

# Probar login
status, resp = send_to_bus('regis', 'login', {
    'correo': 'test@mail.com',
    'password': '123456'
})
print(f"Login: {status} - {resp}")
```

Ejecutar:

```bash
cd backend
python test_bus.py
```

---

## Notas Técnicas

### Características del Bus
- **Puerto:** 5000 (TCP)
- **Protocolo:** Binario con longitud fija
- **Registro:** Automático al iniciar servicios con `sinit`
- **Imagen Docker:** `jrgiadach/soabus:latest`

### Estructura de los Servicios
- **Lenguaje:** Python 3.11
- **Base de datos:** MySQL 8.0 (SQLAlchemy ORM)
- **Comunicación:** Sockets TCP puros (sin HTTP/REST)
- **Registro automático:** Al iniciar, cada servicio se conecta al bus y se registra

### Formato de Mensajes
- Todos los campos de longitud fija deben tener exactamente el tamaño especificado
- Los números de longitud son **5 dígitos** con padding de ceros a la izquierda
- Los nombres de servicio son **5 caracteres** con padding de espacios a la derecha
- El status es **2 caracteres**: `OK` o `NK`
- Los datos JSON no tienen restricción de tamaño

---

## 📝 Base de Datos

### Conexión
```
Host: localhost
Puerto: 3307
Usuario: usoa_user
Password: psoa_password
Base de datos: soa_db
```

### phpMyAdmin
```
URL: http://localhost:8088
```

---

## 🐛 Troubleshooting

### El servicio no se conecta al bus
1. Verificar que el bus esté corriendo: `docker logs soa_bus`
2. Verificar que el servicio esté en la misma red: `docker network inspect soa_net`
3. Revisar logs del servicio: `docker logs soa_regist`

### Error "Connection refused"
- El bus no está corriendo o no está escuchando en el puerto 5000
- Ejecutar: `docker-compose up bus -d`

### El servicio no responde
- Verificar que se registró correctamente en el bus
- Revisar logs del servicio para ver si recibió la transacción
- Verificar que el nombre del servicio en la transacción sea correcto (5 caracteres)

### Errores de base de datos
- Verificar que MySQL esté corriendo: `docker logs soa_db`
- Esperar a que el healthcheck pase: `docker-compose ps`
- Recrear la BD si es necesario: `docker-compose down --volumes && docker-compose up --build`

---

## 📚 Referencias

- **Imagen del Bus:** [jrgiadach/soabus:latest](https://hub.docker.com/r/jrgiadach/soabus)
- **Protocolo:** Basado en longitud fija con sockets TCP
- **Arquitectura:** SOA (Service-Oriented Architecture)
