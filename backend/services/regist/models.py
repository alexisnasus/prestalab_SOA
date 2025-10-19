from sqlalchemy import Column, BigInteger, String, Integer, DateTime, func, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os
import bcrypt

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
    telefono = Column(String(15), nullable=True, default='')
    password_hash = Column('password', String(128), nullable=False)
    estado = Column(String(20), nullable=False, default='ACTIVO')
    preferencias_notificacion = Column(Integer, nullable=False, default=1)
    registro_instante = Column(DateTime, nullable=False, server_default=func.now())

    solicitudes = relationship("Solicitud", back_populates="usuario")

    def to_dict(self):
        """Convierte el objeto Usuario a un diccionario, excluyendo el password"""
        user_dict = {}
        for column in self.__table__.columns:
            # Usar el nombre de la columna en la base de datos, no el atributo del modelo
            db_column_name = column.name
            if db_column_name == 'password':
                continue  # Omitir la contraseña
            
            # Obtener el valor del atributo correspondiente
            if hasattr(self, column.key):
                value = getattr(self, column.key)
                user_dict[db_column_name] = value
        
        return user_dict

    def set_password(self, plain_password):
        """Hashea la contraseña antes de guardarla."""
        self.password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, plain_password):
        """Verifica si la contraseña proporcionada coincide con la contraseña hasheada."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Solicitud(Base):
    __tablename__ = 'solicitud'

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, nullable=False)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    tipo = Column(String(20), nullable=False)
    estado = Column(String(20), nullable=False)
    registro_instante = Column(DateTime, nullable=False, server_default=func.now())

    usuario = relationship("Usuario", back_populates="solicitudes")
