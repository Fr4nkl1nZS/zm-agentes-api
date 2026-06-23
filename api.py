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
                Eres el asistente de ventas de ZM Deportes, con 15 años de experiencia en uniformes personalizados.

                TU MISIÓN: Convertir cada conversación en una cotización formal, incluso con datos parciales.

                REGLAS:
                1. SIEMPRE pregunta: deporte, cantidad, colores, logo, tela y fecha de entrega.
                2. SI el cliente pide una cotización o da un número de teléfono, DEBES generar una cotización BASE (con los datos que tengas) y preguntar por los faltantes.
                3. Cotización base:
                - Uniforme de fútbol: $50,000
                - Uniforme de baloncesto: $55,000
                - Personalización (logo/nombre/número): $15,000 adicional
                - Envío a todo Colombia: se paga contra-entrega

                4. SI el cliente da su número, responde:
                "Perfecto, te envío la cotización por WhatsApp. ¿Confirmas que los detalles son: [lista de datos]? Si falta algo, dímelo y lo ajusto."

                TONO: Amable, profesional, persuasivo y en español.
                """},
                {"role": "user", "content": mensaje.texto}
            ],
        temperature=0.7,
        max_tokens=1024,
        )
        respuesta_asistente = response.choices[0].message.content

        # --- DETECTAR SI EL CLIENTE ENVIÓ SU NÚMERO ---
        texto_limpio = re.sub(r'[\s\-]', '', mensaje.texto)
        numeros_encontrados = re.findall(r'(\d{10})', texto_limpio)

        # --- DETECTAR SI EL CLIENTE PIDIÓ UNA COTIZACIÓN ---
        if "cotización" in mensaje.texto.lower() or "precio" in mensaje.texto.lower():
            # Buscar cantidad en el mensaje
            cantidades = re.findall(r'(\d+)', mensaje.texto)
            cantidad = int(cantidades[0]) if cantidades else 10  # Por defecto 10
            
            # Buscar deporte
            deporte = "fútbol" if "futbol" in mensaje.texto.lower() else "baloncesto" if "baloncesto" in mensaje.texto.lower() else "deporte"
            
            # Precio base
            precio_base = 50000 if deporte == "fútbol" else 55000
            total = precio_base * cantidad
            
            # Generar cotización
            cotizacion = f"""
        📋 COTIZACIÓN ZM DEPORTES
        Deporte: {deporte}
        Cantidad: {cantidad}
        Precio unitario: ${precio_base:,}
        Subtotal: ${total:,}
        Personalización: $15,000 adicional (opcional)
        Envío: contra-entrega
        TOTAL ESTIMADO: ${total:,}

        *Esta es una cotización base. Los detalles finales pueden ajustar el precio.
        """
            # Añadir la cotización a la respuesta
            respuesta_asistente += "\n\n" + cotizacion
        
        
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
    

    
      