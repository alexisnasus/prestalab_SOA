from sqlalchemy import Column, BigInteger, String, DateTime, func, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Generador de sesión de base de datos para inyección de dependencias"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Usuario(Base):
    __tablename__ = 'usuario'

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    correo = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(20), nullable=False)
    telefono = Column(String(15), nullable=False)
    password = Column(String(128), nullable=False)
    estado = Column(String(20), nullable=False, default='ACTIVO')
    preferencias_notificacion = Column(BigInteger, nullable=False, default=1)
    registro_instante = Column(DateTime, nullable=False, server_default=func.now())

    sugerencias = relationship("Sugerencia", back_populates="usuario")

class Sugerencia(Base):
    __tablename__ = 'sugerencia'

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    sugerencia = Column(String(100), nullable=False)
    estado = Column(String(20), nullable=False, default='PENDIENTE')
    registro_instante = Column(DateTime, nullable=False, server_default=func.now())

    usuario = relationship("Usuario", back_populates="sugerencias")
