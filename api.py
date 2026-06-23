from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from urllib.parse import quote
import re

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

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

NUMERO_WHATSAPP = "573167568428"

def enviar_whatsapp(numero, mensaje):
        numero_limpio = ''.join(filter(str.isdigit, numero))
        mensaje_codificado = quote(mensaje)
        return f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_codificado}"
    
    
@app.get("/")
async def root():
    return {"mensaje": "API de ZM Deportes Agentes con Groq"}

@app.post("/chat")
async def chat(mensaje: Mensaje):
    try:
     # Aquí usas tu cliente de OpenAI/Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # O el modelo que uses
            messages=[
                {"role": "system", "content": """
                Eres el asistente de ventas de ZM Deportes, una empresa con 15 años de experiencia en uniformes deportivos personalizados.
                
                Tu objetivo es convertir cada conversación en una cotización formal. Sigue estas reglas:
                1. SIEMPRE pregunta: deporte, cantidad, colores, logo, tela y fecha de entrega.
                2. MENCIONA los beneficios: durabilidad, comodidad y tecnología innovadora.
                3. OFRECE ejemplos de personalización: nombres, números, parches.
                4. Cuando el cliente dé todos los datos, GENERA una cotización con estos precios:
                   - Uniforme de fútbol: $50,000
                   - Uniforme de baloncesto: $50,000
                   - Personalización (logo/nombre/número): consulta el precio
                   - Envío a todo Colombia: se paga contra-entrega
                5. Termina SIEMPRE preguntando: "¿Te envío la cotización formal por WhatsApp?"

                Tono: Amable, profesional, persuasivo y en español.
                """},
                {"role": "user", "content": mensaje.texto}
            ],
        temperature=0.7,
        max_tokens=1024,
        )
        respuesta_asistente = response.choices[0].message.content
        
        # --- DETECTAR SI EL CLIENTE ENVIÓ SU NÚMERO ---
        numeros_encontrados = re.findall(r'(\d{10})', mensaje.texto)  # Busca 10 dígitos seguidos
        
        if numeros_encontrados:
            numero_cliente = numeros_encontrados[0]
            mensaje_cotizacion = "Hola, soy de ZM Deportes. Aquí tienes tu cotización personalizada según lo conversado."
            url_whatsapp = enviar_whatsapp(numero_cliente, mensaje_cotizacion)
            # Agregar el enlace a la respuesta del asistente
            respuesta_asistente += f"\n\n📲 Haz clic aquí para recibir tu cotización por WhatsApp: {url_whatsapp}"
        
        return {"respuesta": respuesta_asistente}
        
    except Exception as e:
        print(f"Error en Groq: {e}")
        return {"respuesta": f"Lo siento, tuve un problema: {str(e)}"}
    

    
      