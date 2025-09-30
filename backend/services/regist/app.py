from fastapi import FastAPI, HTTPException, Body, status
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "Servicio REGIST disponible"}

# Registrar usuario
@app.post("/usuarios", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: dict = Body(...)):
    query = text("""
        INSERT INTO usuario (id, nombre, correo, tipo, telefono, estado, preferencias_notificacion, registro_instante)
        VALUES (:id, :nombre, :correo, :tipo, :telefono, :estado, :preferencias_notificacion, NOW())
    """)
    with engine.begin() as conn:
        result = conn.execute(query, usuario)
        return {"id": result.lastrowid, "message": "Usuario registrado"}

# Login usuario
@app.post("/auth/login")
def login(auth: dict = Body(...)):
    correo = auth.get("correo")
    password = auth.get("password")
    query = text("SELECT * FROM usuario WHERE correo = :correo")
    with engine.begin() as conn:
        user = conn.execute(query, {"correo": correo}).fetchone()
        if not user or password != "mock_password":
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        return {"message": f"Usuario {correo} autenticado", "token": "fake-jwt-token"}

# Retrieve usuario
@app.get("/usuarios/{id}")
def consultar_usuario(id: int):
    query = text("SELECT * FROM usuario WHERE id = :id")
    with engine.begin() as conn:
        user = conn.execute(query, {"id": id}).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return dict(user._mapping)

# Update usuario
@app.put("/usuarios/{id}")
def actualizar_usuario(id: int, datos: dict = Body(...)):
    sets = ", ".join([f"{k} = :{k}" for k in datos.keys()])
    query = text(f"UPDATE usuario SET {sets} WHERE id = :id")
    datos["id"] = id
    with engine.begin() as conn:
        conn.execute(query, datos)
        return {"message": f"Usuario {id} actualizado"}
