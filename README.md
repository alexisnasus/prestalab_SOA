# prestalab SOA

Sistema de préstamos para ramo Arquitectura de Software 2025/S2

**Servicios disponibles:**
- phpMyAdmin: http://localhost:8080
- gerep (Reportes): http://localhost:8001
- lista (Listados): http://localhost:8002
- multa (Multas): http://localhost:8003
- notis (Notificaciones): http://localhost:8004
- prart (Préstamos): http://localhost:8005
- regist (Usuarios): http://localhost:8006
- sugit (Sugerencias): http://localhost:8007

---

## 🚀 Levantar el sistema completo

### 1. Crear entorno virtual e instalar dependencias
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```


### 2. Levantar servicios

**Primera vez o resetear BD:**
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