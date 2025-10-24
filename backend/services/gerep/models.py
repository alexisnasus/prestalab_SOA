from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Item(Base):
    __tablename__ = 'item'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    tipo = Column(String(20), nullable=False)
    existencias = relationship("ItemExistencia", back_populates="item")

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
    registro_instante = Column(DateTime, nullable=False)
    item = relationship("Item", back_populates="existencias")
    sede = relationship("Sede", back_populates="existencias")
    prestamos = relationship("Prestamo", back_populates="item_existencia")

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    solicitudes = relationship("Solicitud", back_populates="usuario")

class Solicitud(Base):
    __tablename__ = 'solicitud'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    usuario = relationship("Usuario", back_populates="solicitudes")
    prestamos = relationship("Prestamo", back_populates="solicitud")

class Prestamo(Base):
    __tablename__ = 'prestamo'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    item_existencia_id = Column(BigInteger, ForeignKey('item_existencia.id'), nullable=False)
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), nullable=False)
    fecha_prestamo = Column(DateTime, nullable=False)
    fecha_devolucion = Column(DateTime, nullable=True)
    estado = Column(String(20), nullable=False)
    item_existencia = relationship("ItemExistencia", back_populates="prestamos")
    solicitud = relationship("Solicitud", back_populates="prestamos")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
