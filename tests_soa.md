# Guía de Pruebas SOA con cURL para CMD

Esta guía contiene los comandos `curl` necesarios para probar cada operación de los servicios de la arquitectura PrestaLab SOA. 

**IMPORTANTE**: Todos los comandos se ejecutan a través del **Enterprise Service Bus (ESB)** en el puerto **8000**. El bus se encarga de enrutar las peticiones a los servicios correspondientes.

Los comandos están diseñados para ser ejecutados en la terminal **CMD de Windows**.

---

## 1. Servicio REGIST - Gestión de Usuarios

### Registrar un nuevo usuario
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"regist\", \"method\": \"POST\", \"endpoint\": \"/usuarios\", \"payload\": {\"nombre\": \"Usuario de Prueba\", \"correo\": \"prueba@test.com\", \"tipo\": \"ESTUDIANTE\", \"telefono\": \"123456789\", \"password\": \"1234\"}}"
```

### Autenticar un usuario

```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"regist\", \"method\": \"POST\", \"endpoint\": \"/auth/login\", \"payload\": {\"correo\": \"prueba@test.com\", \"password\": \"1234\"}}"
```

### Consultar usuario por ID (ej: ID 1)

```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"regist\", \"method\": \"GET\", \"endpoint\": \"/usuarios/1\"}"
```

### Actualizar datos de un usuario (ej: ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"regist\", \"method\": \"PUT\", \"endpoint\": \"/usuarios/1\", \"payload\": {\"telefono\": \"987654321\"}}"
```

### Aprobar una solicitud de registro pendiente (ej: Solicitud ID 1)

```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"regist\", \"method\": \"PUT\", \"endpoint\": \"/solicitudes-registro/1/actualizar\", \"payload\": {\"estado\": \"APROBADA\"}}"
```

---

## 2. Servicio PRART - Préstamos y Artículos

### Obtener todos los artículos del catálogo

```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"GET\", \"endpoint\": \"/items/all\"}"
```

### Buscar artículos en el catálogo (por tipo)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"GET\", \"endpoint\": \"/items?tipo=LIBRO\"}"
```

### Buscar artículos en el catálogo (por nombre)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"GET\", \"endpoint\": \"/items?nombre=Python\"}"
```

### Crear una solicitud de préstamo (ej: Usuario ID 1)

```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"POST\", \"endpoint\": \"/solicitudes\", \"payload\": {\"usuario_id\": 1, \"tipo\": \"PRESTAMO\"}}"
```

### Listar solicitudes de un usuario (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"GET\", \"endpoint\": \"/solicitudes?usuario_id=1\"}"
```

### Registrar un préstamo (ej: Solicitud ID 1, Existencia ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"POST\", \"endpoint\": \"/prestamos\", \"payload\": {\"solicitud_id\": 1, \"item_existencia_id\": 1}}"
```

### Registrar una devolución (ej: Préstamo ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"POST\", \"endpoint\": \"/devoluciones\", \"payload\": {\"prestamo_id\": 1}}"
```

### Renovar un préstamo (ej: Préstamo ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"prart\", \"method\": \"PUT\", \"endpoint\": \"/prestamos/1/renovar\"}"
```

---

## 3. Servicio MULTA - Multas y Bloqueos

### Consultar multas de un usuario (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"multa\", \"method\": \"GET\", \"endpoint\": \"/usuarios/1/multas\"}"
```

### Registrar una nueva multa (ej: Préstamo ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"multa\", \"method\": \"POST\", \"endpoint\": \"/multas\", \"payload\": {\"prestamo_id\": 1, \"motivo\": \"Entrega tardía\", \"valor\": 10.50, \"estado\": \"PENDIENTE\"}}"
```

### Bloquear a un usuario (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"multa\", \"method\": \"PUT\", \"endpoint\": \"/usuarios/1/estado\", \"payload\": {\"estado\": \"BLOQUEADO\"}}"
```

---

## 4. Servicio LISTA - Listas de Espera

### Agregar usuario a lista de espera (ej: Solicitud ID 2, Item ID 3)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"lista\", \"method\": \"POST\", \"endpoint\": \"/lista-espera\", \"payload\": {\"solicitud_id\": 2, \"item_id\": 3}}"
```

### Consultar lista de espera por artículo (ej: Item ID 3)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"lista\", \"method\": \"GET\", \"endpoint\": \"/lista-espera/3\"}"
```

### Actualizar estado de un registro en lista de espera (ej: Registro ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"lista\", \"method\": \"PUT\", \"endpoint\": \"/lista-espera/1\", \"payload\": {\"estado\": \"ATENDIDA\"}}"
```

---

## 5. Servicio NOTIS - Notificaciones

### Crear una notificación (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"notis\", \"method\": \"POST\", \"endpoint\": \"/notificaciones\", \"payload\": {\"usuario_id\": 1, \"canal\": 1, \"tipo\": \"RECORDATORIO\", \"mensaje\": \"Tu préstamo vence pronto.\"}}"
```

### Obtener preferencias de notificación de un usuario (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"notis\", \"method\": \"GET\", \"endpoint\": \"/preferencias/1\"}"
```

### Actualizar preferencias de notificación (ej: Usuario ID 1, Preferencia 2)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"notis\", \"method\": \"PUT\", \"endpoint\": \"/preferencias/1\", \"payload\": {\"preferencias_notificacion\": 2}}"
```

---

## 6. Servicio GEREP - Reportes e Historial

### Obtener historial de préstamos de un usuario (ej: Usuario ID 1, formato JSON)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"gerep\", \"method\": \"GET\", \"endpoint\": \"/usuarios/1/historial?formato=json\"}"
```

### Obtener historial en formato CSV
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"gerep\", \"method\": \"GET\", \"endpoint\": \"/usuarios/1/historial?formato=csv\"}"
```

### Obtener reporte de circulación (ej: Periodo 2025-10, Sede 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"gerep\", \"method\": \"GET\", \"endpoint\": \"/reportes/circulacion?periodo=2025-10&sede_id=1\"}"
```

---

## 7. Servicio SUGIT - Sugerencias

### Registrar una nueva sugerencia (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"sugit\", \"method\": \"POST\", \"endpoint\": \"/sugerencias\", \"payload\": {\"usuario_id\": 1, \"sugerencia\": \"Me gustaría que trajeran más libros de ciencia ficción.\"}}"
```

### Listar todas las sugerencias
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"sugit\", \"method\": \"GET\", \"endpoint\": \"/sugerencias\"}"
```

### Aprobar una sugerencia (ej: Sugerencia ID 1)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"sugit\", \"method\": \"PUT\", \"endpoint\": \"/sugerencias/1/aprobar\"}"
```

### Rechazar una sugerencia (ej: Sugerencia ID 2)
```cmd
curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d "{\"target_service\": \"sugit\", \"method\": \"PUT\", \"endpoint\": \"/sugerencias/2/rechazar\"}"
```

---

## 8. Endpoints del Bus (Puerto 8000)

### Descubrir servicios disponibles
```cmd
curl -X GET http://localhost:8000/discover
```

### Ver estadísticas del bus
```cmd
curl -X GET http://localhost:8000/stats
```

### Ver logs de comunicación
```cmd
curl -X GET http://localhost:8000/logs?limit=50
```

### Health check del bus
```cmd
curl -X GET http://localhost:8000/ping
```

### Estado de un servicio específico (ej: regist)
```cmd
curl -X GET http://localhost:8000/health/regist
```
