```markdown
# PrestaLab SOA

Sistema de préstamos bibliotecarios con **Arquitectura Orientada a Servicios (SOA)** y **Bus de Servicios TCP**.

---

## Arquitectura del Sistema

```

```
                    ┌─────────────┐
                    │  CLIENTES   │
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │  🚌 BUS SOA (TCP)   │  <-- Protocolo TCP Socket
                │  localhost:5000     │     NNNNNSSSSSDATOS
                └──────────┬──────────┘
                           │
    ┌──────┬──────┬────────┼────────┬──────┬──────┐
    ▼      ▼      ▼        ▼        ▼      ▼      ▼
 gerep  lista  multa    notis    prart  regis  sugit
                          │
                   ┌──────▼──────┐
                   │ MySQL:3307  │
                   │ phpMyAdmin  │
                   │   :8088     │
                   └─────────────┘
```

```

### Componentes Principales

| Componente     | Puerto | Función                                              |
|----------------|--------|------------------------------------------------------|
| **Bus SOA** | 5000   | Orquestador central con protocolo TCP binario        |
| **gerep** | -      | Gestión de reportes e historial                      |
| **lista** | -      | Gestión de listas de espera                          |
| **multa** | -      | Gestión de multas y bloqueos                         |
| **notis** | -      | Gestión de notificaciones multicanal                |
| **prart** | -      | Gestión de préstamos y artículos                    |
| **regis** | -      | Registro y autenticación de usuarios                 |
| **sugit** | -      | Gestión de sugerencias                             |
| **MySQL** | 3307   | Base de datos principal                              |
| **phpMyAdmin** | 8088   | Interfaz web para administración de la Base de Datos |

**Nota**: Los servicios (`gerep`, `lista`, etc.) no exponen puertos directamente. Toda la comunicación debe pasar a través del Bus SOA en el puerto 5000 usando el protocolo TCP especificado.

---

## Protocolo del Bus SOA

El bus utiliza un protocolo binario sobre TCP Sockets.

### Transacción de entrada (Cliente → Bus → Servicio):

```

NNNNNSSSSSDATOS

```

* **NNNNN**: Longitud total (5 dígitos con ceros iniciales) de los bytes correspondientes a `SSSSS` + `DATOS`.
* **SSSSS**: Nombre del servicio destino (exactamente 5 caracteres, rellenado con espacios si es necesario). Ejemplos: `regis`, `prart`.
* **DATOS**: Carga útil del mensaje. Generalmente consiste en el nombre de la operación seguido de un espacio y un objeto JSON. Ejemplo: `login {"correo":"u@mail.com","password":"123"}`.

### Transacción de salida (Servicio → Bus → Cliente):

```

NNNNNSSSSSSTDATOS

```

* **NNNNN**: Longitud total (5 dígitos).
* **SSSSS**: Nombre del servicio que responde (5 caracteres).
* **ST**: Estado de la operación (2 caracteres): `OK` para éxito, `NK` para error.
* **DATOS**: Respuesta del servicio, usualmente en formato JSON. Ejemplo: `{"message":"Usuario autenticado"}` o `{"error":"Credenciales inválidas"}`.

### Registro de Servicios (`sinit`):

Al iniciar, cada servicio se conecta al bus y envía un mensaje de registro:

```

00010sinitSSSSS

````

* Donde `SSSSS` es el nombre del servicio (5 caracteres). Ejemplo: `00010sinitregis`.
* El bus responde confirmando el registro, típicamente con `00002OK`.

---

## Comandos Esenciales

### Levantar Sistema

**Primera vez (con rebuild):**

```bash
cd backend
docker-compose down --volumes --remove-orphans
docker-compose up --build -d
````

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

-----

## Operaciones de Servicios (SOA)

Las operaciones se invocan enviando el mensaje correspondiente al Bus SOA (puerto 5000) con el formato `NNNNNSSSSSDATOS`. La parte `DATOS` usualmente es `OPERACION {json_payload}`.

### `regis` - Gestión de Usuarios

  * `register {payload}`: Registra un nuevo usuario.
  * `login {payload}`: Autentica un usuario.
  * `get_user {payload}`: Consulta usuario por ID.
  * `update_user {payload}`: Actualiza datos de usuario.
  * `update_solicitud {payload}`: Cambia estado de una solicitud (ej. aprobación).

### `prart` - Préstamos y Artículos

  * `get_all_items {}`: Obtiene todos los artículos.
  * `search_items {payload}`: Busca artículos con filtros.
  * `get_solicitudes {payload}`: Lista solicitudes de un usuario.
  * `create_solicitud {payload}`: Crea una solicitud de préstamo o ventana.
  * `create_reserva {payload}`: Crea una reserva (ventana) asociada a una solicitud.
  * `cancel_reserva {payload}`: Cancela una reserva.
  * `create_prestamo {payload}`: Registra un préstamo asociado a una solicitud.
  * `create_devolucion {payload}`: Registra la devolución de un préstamo.
  * `renovar_prestamo {payload}`: Renueva un préstamo activo.
  * `update_item_estado {payload}`: Actualiza el estado de una existencia física.

### `multa` - Multas y Bloqueos

  * `get_multas_usuario {payload}`: Consulta multas de un usuario.
  * `crear_multa {payload}`: Registra una nueva multa.
  * `update_bloqueo {payload}`: Cambia el estado de un usuario.

### `lista` - Listas de Espera

  * `Notesa_espera {payload}`: Agrega una solicitud a la lista de espera de un item.
  * `update_lista_espera {payload}`: Actualiza el estado de un registro en la lista.
  * `get_lista_espera {payload}`: Consulta la lista de espera para un item.

### `notis` - Notificaciones

  * `crear_notificacion {payload}`: Registra una notificación.
  * `get_preferencias {payload}`: Obtiene las preferencias de notificación.
  * `update_preferencias {payload}`: Actualiza las preferencias.

### `gerep` - Reportes e Historial

  * `get_historial {payload}`: Obtiene historial de préstamos (JSON, CSV, PDF).
  * `get_reporte_circulacion {payload}`: Obtiene métricas de circulación por sede y período.

### `sugit` - Sugerencias

  * `registrar_sugerencia {payload}`: Registra una sugerencia.
  * `listar_sugerencias {}`: Lista todas las sugerencias.
  * `aprobar_sugerencia {payload}`: Marca una sugerencia como aceptada.
  * `rechazar_sugerencia {payload}`: Marca una sugerencia como rechazada.

-----

## Pruebas de Servicios

Se incluyen scripts de prueba individuales (`test_*.py`) para cada servicio (ej. `test_regist.py`, `test_prart.py`). Estos scripts permiten enviar operaciones específicas a cada servicio a través del Bus SOA mediante un menú interactivo en la consola.

**Ejecución de un script de prueba:**

```bash
cd backend
python test_regist.py # O el script del servicio deseado
```

Estos scripts utilizan una función `send_to_bus` para encapsular la comunicación TCP con el bus, siguiendo el protocolo `NNNNNSSSSSDATOS`.

-----

## Base de Datos

### Conexión

```
Host: localhost (o 'db' desde otros contenedores)
Puerto: 3307
Usuario: usoa_user
Password: psoa_password
Base de datos: soa_db
```

### phpMyAdmin

Interfaz web para gestionar la base de datos:

```
URL: http://localhost:8088
```

-----

## Troubleshooting

### El servicio no se conecta al bus

1.  Verificar que el bus (`soa_bus`) esté corriendo: `docker logs soa_bus`. Debería indicar "Bus SOA escuchando...".
2.  Verificar que el servicio esté en la misma red Docker (`soa_net`).
3.  Revisar logs del servicio específico: `docker logs soa_regist`. Buscar errores al conectar a `('bus', 5000)`.

### Error "Connection refused" en servicios

  * El bus (`soa_bus`) no está corriendo o no inició correctamente. Ejecutar: `docker-compose up -d bus`.
  * Problema de red en Docker. Intentar reiniciar Docker o `docker-compose down && docker-compose up -d`.

### El servicio no responde a las solicitudes

  * Verificar registro `sinit` en logs del servicio y confirmación `OK` del bus.
  * Revisar logs del servicio para ver si recibió la transacción.
  * Verificar nombre del servicio (`SSSSS`, 5 chars) y `OPERACION` en el mensaje enviado.

### Errores de base de datos en servicios

  * Verificar que MySQL (`soa_db`) esté corriendo y saludable: `docker-compose ps`.
  * Verificar `DATABASE_URL` en `docker-compose.yml`.
  * Si persisten problemas: `docker-compose down --volumes && docker-compose up --build -d` (Borra todos los datos).

-----

## Referencias

  * **Imagen del Bus:** `jrgiadach/soabus:latest`
  * **Protocolo:** Documento `ArquiSW_soa.pdf`.
  * **Arquitectura:** SOA (Service-Oriented Architecture).

<!-- end list -->

```
```
