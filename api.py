from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zmdeportes.com",  # Permitir la URL de tu sitio web
        "http://zmdeportes.com",  # Permitir la URL de tu sitio web
        "https://www.zmdeportes.com",  # Permitir la URL de tu sitio web
        "*"
        ],  # Permitir todas las URLs de origen
        allow_methods=["*"],  # Permitir todos los métodos HTTP
        allow_headers=["*"],  # Permitir todos los encabezados
        allow_credentials=True,  # Permitir el envío de cookies y credenciales
)

class Mensaje(BaseModel):
    texto: str

@app.get("/")
async def root():
    return {"mensaje": "API de ZM Deportes Agentes"}

@app.post("/chat")
async def chat(mensaje: Mensaje):
    return {"respuesta": "El asistente está funcionando"}
