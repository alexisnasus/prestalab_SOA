from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, Text
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
    preferencias_notificacion = Column(Integer, nullable=False, default=0)
    notificaciones = relationship("Notificacion", back_populates="usuario")

class Notificacion(Base):
    __tablename__ = 'notificacion'
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    canal = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)
    mensaje = Column(Text, nullable=False)
    registro_instante = Column(DateTime, default=datetime.now, nullable=False)
    usuario = relationship("Usuario", back_populates="notificaciones")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
