from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def root():
    return {"message": "Servie NOTIS is running"}

#
#@app.get("/items")
#def get_items():
#    with engine.connect() as conn:
#        result = conn.execute(text("SELECT id, nombre, cantidad, tipo FROM item"))
#        items = [dict(row._mapping) for row in result]
#    return {"items": items}