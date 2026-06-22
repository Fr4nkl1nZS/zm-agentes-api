from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from coordinador import client

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
     # Aquí usas tu cliente de OpenAI/Groq
    response = client.chat.completions.create(
        model="llama3.2",  # O el modelo que uses
        messages=[
            {"role": "system", "content": """
            Eres el asistente de ZM Deportes, una empresa con 15 años de experiencia en uniformes deportivos personalizados.
            Tu objetivo es ayudar a los clientes a diseñar y cotizar sus uniformes.

            Reglas importantes:
            1. Pregunta siempre: deporte, cantidad de uniformes, colores, si necesitan logo y tipo de tela.
            2. Menciona los beneficios de ZM Deportes: durabilidad, comodidad y tecnología innovadora.
            3. Ofrece ejemplos de personalización: nombres, números, parches.
            4. Si el cliente no sabe qué quiere, pregúntale sobre el estilo de su equipo (moderno, clásico, agresivo).
            5. Termina siempre preguntando si necesita una cotización formal.

            Ejemplo de cotización:
            - Uniforme de fútbol: desde $50,000
            - Envío: paga el cliente, se envía contra-entrega a todo Colombia
            """},
            {"role": "user", "content": mensaje.texto}
        ],
        temperature=0.8
    )
    return {"respuesta": response.choices[0].message.content}
