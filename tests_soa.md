# Guía de Pruebas SOA con cURL para CMD

Esta guía contiene los comandos `curl` necesarios para probar cada operación de los servicios de la arquitectura PrestaLab SOA. Los comandos están diseñados para ser ejecutados en la terminal **CMD de Windows**.

---

## 1. Servicio REGIST (Puerto 8006) - Gestión de Usuarios

### Registrar un nuevo usuario
```cmd
curl -X POST http://localhost:8006/usuarios -H "Content-Type: application/json" -d "{\"nombre\": \"Usuario de Prueba\", \"correo\": \"prueba@test.com\", \"tipo\": \"ESTUDIANTE\", \"telefono\": \"123456789\", \"password\": \"1234\"}"
```

### Autenticar un usuario
```cmd
curl -X POST http://localhost:8006/auth/login -H "Content-Type: application/json" -d "{\"correo\": \"prueba@test.com\", \"password\": \"1234\"}"
```

### Consultar usuario por ID (ej: ID 1)
```cmd
curl -X GET http://localhost:8006/usuarios/1
```

### Actualizar datos de un usuario (ej: ID 1)
```cmd
curl -X PUT http://localhost:8006/usuarios/1 -H "Content-Type: application/json" -d "{\"telefono\": \"123456789\"}"
```

### Aprobar una solicitud de registro pendiente (ej: Solicitud ID 1)
```cmd
curl -X PUT http://localhost:8006/solicitudes-registro/1/actualizar -H "Content-Type: application/json" -d "{\"estado\": \"APROBADA\"}"
```

---

## 2. Servicio PRART (Puerto 8005) - Préstamos y Artículos

### Buscar artículos en el catálogo
```cmd
curl -X GET http://localhost:8005/items?tipo=LIBRO
```

### Crear una solicitud de préstamo (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8005/solicitudes -H "Content-Type: application/json" -d "{\"usuario_id\": 1, \"tipo\": \"PRESTAMO\"}"
```

### Listar solicitudes de un usuario (ej: Usuario ID 1)
```cmd
curl -X GET "http://localhost:8005/solicitudes?usuario_id=1"
```

### Registrar un préstamo (ej: Solicitud ID 1, Existencia ID 1)
```cmd
curl -X POST http://localhost:8005/prestamos -H "Content-Type: application/json" -d "{\"solicitud_id\": 1, \"item_existencia_id\": 1}"
```

### Registrar una devolución (ej: Préstamo ID 1)
```cmd
curl -X POST http://localhost:8005/devoluciones -H "Content-Type: application/json" -d "{\"prestamo_id\": 1}"
```

### Renovar un préstamo (ej: Préstamo ID 1)
```cmd
curl -X PUT http://localhost:8005/prestamos/1/renovar
```

---

## 3. Servicio MULTA (Puerto 8003) - Multas y Bloqueos

### Consultar multas de un usuario (ej: Usuario ID 1)
```cmd
curl -X GET http://localhost:8003/usuarios/1/multas
```

### Registrar una nueva multa (ej: Préstamo ID 1)
```cmd
curl -X POST http://localhost:8003/multas -H "Content-Type: application/json" -d "{\"prestamo_id\": 1, \"motivo\": \"Entrega tardía\", \"valor\": 10.50, \"estado\": \"PENDIENTE\"}"
```

### Bloquear a un usuario (ej: Usuario ID 1)
```cmd
curl -X PUT http://localhost:8003/usuarios/1/estado -H "Content-Type: application/json" -d "{\"estado\": \"BLOQUEADO\"}"
```

---

## 4. Servicio LISTA (Puerto 8002) - Listas de Espera

### Agregar usuario a lista de espera (ej: Solicitud ID 2, Item ID 3)
```cmd
curl -X POST http://localhost:8002/lista-espera -H "Content-Type: application/json" -d "{\"solicitud_id\": 2, \"item_id\": 3}"
```

### Consultar lista de espera por artículo (ej: Item ID 3)
```cmd
curl -X GET http://localhost:8002/lista-espera/3
```

### Actualizar estado de un registro en lista de espera (ej: Registro ID 1)
```cmd
curl -X PUT http://localhost:8002/lista-espera/1 -H "Content-Type: application/json" -d "{\"estado\": \"ATENDIDA\"}"
```

---

## 5. Servicio NOTIS (Puerto 8004) - Notificaciones

### Crear una notificación (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8004/notificaciones -H "Content-Type: application/json" -d "{\"usuario_id\": 1, \"canal\": 1, \"tipo\": \"RECORDATORIO\", \"mensaje\": \"Tu préstamo vence pronto.\"}"
```

### Obtener preferencias de notificación de un usuario (ej: Usuario ID 1)
```cmd
curl -X GET http://localhost:8004/preferencias/1
```

### Actualizar preferencias de notificación (ej: Usuario ID 1, Preferencia 2)
```cmd
curl -X PUT http://localhost:8004/preferencias/1 -H "Content-Type: application/json" -d "{\"preferencias_notificacion\": 2}"
```

---

## 6. Servicio GEREP (Puerto 8001) - Reportes e Historial

### Obtener historial de préstamos de un usuario (ej: Usuario ID 1, formato JSON)
```cmd
curl -X GET "http://localhost:8001/usuarios/1/historial?formato=json"
```

### Obtener historial en formato CSV
```cmd
curl -X GET "http://localhost:8001/usuarios/1/historial?formato=csv"
```

### Obtener reporte de circulación (ej: Periodo 2025-10, Sede 1)
```cmd
curl -X GET "http://localhost:8001/reportes/circulacion?periodo=2025-10&sede_id=1"
```

---

## 7. Servicio SUGIT (Puerto 8007) - Sugerencias

### Registrar una nueva sugerencia (ej: Usuario ID 1)
```cmd
curl -X POST http://localhost:8007/sugerencias -H "Content-Type: application/json" -d "{\"usuario_id\": 1, \"sugerencia\": \"Me gustaría que trajeran más libros de ciencia ficción.\"}"
```

### Listar todas las sugerencias
```cmd
curl -X GET http://localhost:8007/sugerencias
```

### Aprobar una sugerencia (ej: Sugerencia ID 1)
```cmd
curl -X PUT http://localhost:8007/sugerencias/1/aprobar
```

### Rechazar una sugerencia (ej: Sugerencia ID 2)
```cmd
curl -X PUT http://localhost:8007/sugerencias/2/rechazar
```
