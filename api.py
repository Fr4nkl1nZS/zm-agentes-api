from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from coordinador import Coordinador

app = FastAPI()
coordinador = Coordinador()

class Mensaje(BaseModel):
    texto: str

@app.post("/chat")
async def chat(mensaje: Mensaje):
    try:
        respuesta = coordinador.procesar(mensaje.texto)
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"mensaje": "API de ZM Deportes Agentes"}