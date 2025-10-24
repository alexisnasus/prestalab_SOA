from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, Numeric, func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(BigInteger, primary_key=True)
    estado = Column(String(20), nullable=False)
    solicitudes = relationship("Solicitud", back_populates="usuario")

class Solicitud(Base):
    __tablename__ = 'solicitud'
    id = Column(BigInteger, primary_key=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    usuario = relationship("Usuario", back_populates="solicitudes")
    prestamos = relationship("Prestamo", back_populates="solicitud")

class Prestamo(Base):
    __tablename__ = 'prestamo'
    id = Column(BigInteger, primary_key=True)
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), nullable=False)
    solicitud = relationship("Solicitud", back_populates="prestamos")
    multas = relationship("Multa", back_populates="prestamo")

class Multa(Base):
    __tablename__ = 'multa'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    prestamo_id = Column(BigInteger, ForeignKey('prestamo.id'), nullable=False)
    motivo = Column(String(20), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), nullable=False)
    registro_instante = Column(DateTime, default=datetime.now, nullable=False)
    prestamo = relationship("Prestamo", back_populates="multas")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
