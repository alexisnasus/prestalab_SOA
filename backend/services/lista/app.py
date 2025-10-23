from fastapi import FastAPI, HTTPException, Body, Path, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
import sys
sys.path.append('/app')
from bus_client import register_service
from service_logger import create_service_logger
from models import ListaEspera, get_db, Item, Solicitud

app = FastAPI(title="Servicio de Gestión de Listas de Espera")

logger = create_service_logger("lista")

@app.on_event("startup")
async def startup():
    """Registra el servicio en el bus al iniciar"""
    logger.startup("http://lista:8000")
    
    await register_service(
        app=app,
        service_name="lista",
        service_url="http://lista:8000",
        description="Gestión de listas de espera para artículos",
        version="1.0.0"
    )
    
    logger.registered(os.getenv("BUS_URL", "http://bus:5000"))

@app.get("/")
def root():
    return {"message": "Servicio LISTA is running"}

@app.post("/lista-espera", status_code=status.HTTP_201_CREATED)
def agregar_lista_espera(
    solicitud_id: int = Body(..., embed=True),
    item_id: int = Body(..., embed=True),
    estado: str = Body("EN ESPERA", embed=True),
    db: Session = Depends(get_db)
):
    logger.request_received("POST", "/lista-espera", {"solicitud_id": solicitud_id, "item_id": item_id, "estado": estado})
    
    now = datetime.now()
    
    nuevo_registro = ListaEspera(
        solicitud_id=solicitud_id,
        item_id=item_id,
        fecha_ingreso=now,
        estado=estado,
        registro_instante=now
    )
    
    try:
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        response_data = {
            "message": "Registro agregado exitosamente",
            "id": nuevo_registro.id,
            "solicitud_id": solicitud_id,
            "item_id": item_id,
            "fecha_ingreso": now.isoformat(),
            "estado": estado
        }
        logger.response_sent(201, "Registro agregado a lista de espera", f"ID: {nuevo_registro.id}")
        return response_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        # Verificar si es una violación de llave foránea
        if "foreign key constraint fails" in str(e).lower():
            # Verificar si el item_id existe
            item = db.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"El item con ID {item_id} no existe.")
            # Verificar si la solicitud_id existe
            solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
            if not solicitud:
                raise HTTPException(status_code=404, detail=f"La solicitud con ID {solicitud_id} no existe.")
        raise HTTPException(status_code=500, detail="Error al interactuar con la base de datos.")

@app.put("/lista-espera/{id}", status_code=status.HTTP_200_OK)
def actualizar_estado_lista_espera(
    id: int = Path(..., gt=0),
    nuevo_estado: str = Body(..., embed=True, alias="estado"),
    db: Session = Depends(get_db)
):
    logger.request_received("PUT", f"/lista-espera/{id}", {"nuevo_estado": nuevo_estado})
    
    nuevo_estado_upper = nuevo_estado.upper().strip()
    if nuevo_estado_upper not in ("ATENDIDA", "CANCELADA"):
        logger.response_sent(400, "Estado debe ser 'ATENDIDA' o 'CANCELADA'")
        raise HTTPException(status_code=400, detail="El estado debe ser 'ATENDIDA' o 'CANCELADA'")

    try:
        registro = db.query(ListaEspera).filter(ListaEspera.id == id).first()
        
        if not registro:
            logger.response_sent(404, "Registro no encontrado")
            raise HTTPException(status_code=404, detail="Registro no encontrado")
            
        registro.estado = nuevo_estado_upper
        registro.registro_instante = datetime.now()
        
        db.commit()
        
        response_data = {"message": f"Registro {id} actualizado correctamente a {nuevo_estado_upper}"}
        logger.response_sent(200, f"Estado actualizado a {nuevo_estado_upper}", f"ID: {id}")
        return response_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al actualizar el registro.")

@app.get("/lista-espera/{item_id}", status_code=status.HTTP_200_OK)
def obtener_lista_por_item(item_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    logger.request_received("GET", f"/lista-espera/{item_id}", {})
    try:
        registros = db.query(ListaEspera).filter(ListaEspera.item_id == item_id).order_by(ListaEspera.fecha_ingreso.asc()).all()
        
        if not registros:
            logger.response_sent(404, "No se encontraron registros para este ítem")
            raise HTTPException(status_code=404, detail="No se encontraron registros para este ítem")
            
        resultado = [
            {
                "id": r.id,
                "solicitud_id": r.solicitud_id,
                "item_id": r.item_id,
                "fecha_ingreso": r.fecha_ingreso.isoformat(),
                "estado": r.estado,
                "registro_instante": r.registro_instante.isoformat()
            } for r in registros
        ]
        
        logger.response_sent(200, f"Se encontraron {len(resultado)} registros", f"Item ID: {item_id}")
        return {"item_id": item_id, "registros": resultado}
    except SQLAlchemyError as e:
        logger.error("SQLAlchemyError", str(e))
        raise HTTPException(status_code=500, detail="Error al consultar la base de datos.")
