from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL, BigInteger
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# DB SESSION MANAGER
# ============================================================================

def get_db():
    """
    Función de dependencia que proporciona una sesión de base de datos a los endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# ORM MODELS
# ============================================================================

class Item(Base):
    __tablename__ = 'item'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    cantidad = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)
    valor = Column(DECIMAL(10, 2), nullable=False)
    tarifa_atraso = Column(DECIMAL(10, 2), nullable=False)
    descripcion = Column(String(100), nullable=False)
    cantidad_max = Column(Integer, nullable=False)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    existencias = relationship("ItemExistencia", back_populates="item")
    solicitudes = relationship("ItemSolicitud", back_populates="item")

class Sede(Base):
    __tablename__ = 'sede'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    
    existencias = relationship("ItemExistencia", back_populates="sede")

class ItemExistencia(Base):
    __tablename__ = 'item_existencia'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    item_id = Column(BigInteger, ForeignKey('item.id'), nullable=False)
    sede_id = Column(BigInteger, ForeignKey('sede.id'), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False)
    estado = Column(String(20), nullable=False)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    item = relationship("Item", back_populates="existencias")
    sede = relationship("Sede", back_populates="existencias")
    prestamos = relationship("Prestamo", back_populates="item_existencia")
    ventanas = relationship("Ventana", back_populates="item_existencia")

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    correo = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(20), nullable=False)
    telefono = Column(String(15), nullable=False)
    password = Column(String(128), nullable=False)
    estado = Column(String(20), nullable=False)
    preferencias_notificacion = Column(Integer, nullable=False, default=0)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    solicitudes = relationship("Solicitud", back_populates="usuario")

class Solicitud(Base):
    __tablename__ = 'solicitud'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    tipo = Column(String(30), nullable=False)
    estado = Column(String(20), nullable=False)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    usuario = relationship("Usuario", back_populates="solicitudes")
    items = relationship("ItemSolicitud", back_populates="solicitud")
    prestamos = relationship("Prestamo", back_populates="solicitud")
    ventanas = relationship("Ventana", back_populates="solicitud")

class ItemSolicitud(Base):
    __tablename__ = 'item_solicitud'
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), primary_key=True)
    item_id = Column(BigInteger, ForeignKey('item.id'), primary_key=True)
    cantidad = Column(Integer, nullable=False)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    solicitud = relationship("Solicitud", back_populates="items")
    item = relationship("Item", back_populates="solicitudes")

class Prestamo(Base):
    __tablename__ = 'prestamo'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    item_existencia_id = Column(BigInteger, ForeignKey('item_existencia.id'), nullable=False)
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), nullable=False)
    fecha_prestamo = Column(DateTime, nullable=False)
    fecha_devolucion = Column(DateTime, nullable=True)
    comentario = Column(Text, nullable=True)
    estado = Column(String(20), nullable=False)
    renovaciones_realizadas = Column(Integer, nullable=False, default=0)
    registro_instante = Column(DateTime, nullable=False, default=datetime.now)
    
    item_existencia = relationship("ItemExistencia", back_populates="prestamos")
    solicitud = relationship("Solicitud", back_populates="prestamos")

class Ventana(Base):
    __tablename__ = 'ventana'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), nullable=False)
    item_existencia_id = Column(BigInteger, ForeignKey('item_existencia.id'), nullable=False)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    
    solicitud = relationship("Solicitud", back_populates="ventanas")
    item_existencia = relationship("ItemExistencia", back_populates="ventanas")
