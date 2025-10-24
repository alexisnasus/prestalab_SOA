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
    listas_espera = relationship("ListaEspera", back_populates="item")

class Solicitud(Base):
    __tablename__ = 'solicitud'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    listas_espera = relationship("ListaEspera", back_populates="solicitud")

class ListaEspera(Base):
    __tablename__ = 'lista_espera'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    solicitud_id = Column(BigInteger, ForeignKey('solicitud.id'), nullable=False)
    item_id = Column(BigInteger, ForeignKey('item.id'), nullable=False)
    fecha_ingreso = Column(DateTime, nullable=False)
    estado = Column(String(20), nullable=False)
    registro_instante = Column(DateTime, nullable=False)
    
    solicitud = relationship("Solicitud", back_populates="listas_espera")
    item = relationship("Item", back_populates="listas_espera")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
