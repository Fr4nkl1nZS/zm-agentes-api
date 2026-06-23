from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from urllib.parse import quote
import re

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- MODELO ---
class Mensaje(BaseModel):
    texto: str

# --- GROQ ---
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- WHATSAPP ---
NUMERO_WHATSAPP = "573167568428"

def enviar_whatsapp(numero, mensaje):
    numero_limpio = ''.join(filter(str.isdigit, numero))
    mensaje_codificado = quote(mensaje)
    return f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_codificado}"

# --- FUNCIÓN PARA EXTRAER DATOS ---
def extraer_datos(texto):
    datos = {
        "nombre": None,
        "deporte": None,
        "cantidad": None,
        "colores": None,
        "logo": None,
        "tela": None,
        "fecha": None,
        "numero": None
    }
    
    # Detectar nombre
    nombre_match = re.search(r'(?:me llamo|soy|mi nombre es)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+)?)', texto.lower())
    if nombre_match:
        datos["nombre"] = nombre_match.group(1).title()
    else:
        palabras = texto.split()
        for palabra in palabras:
            if palabra[0].isupper() and len(palabra) > 2 and palabra.lower() not in ["yo", "mi", "un", "una", "el", "la", "los", "las"]:
                datos["nombre"] = palabra
                break
    
    # Detectar deporte
    if "futbol" in texto.lower():
        datos["deporte"] = "fútbol"
    elif "baloncesto" in texto.lower():
        datos["deporte"] = "baloncesto"
    elif "ciclismo" in texto.lower():
        datos["deporte"] = "ciclismo"
    elif "voleibol" in texto.lower():
        datos["deporte"] = "voleibol"
    
    # Detectar cantidad
    numeros = re.findall(r'(\d+)', texto)
    if numeros:
        datos["cantidad"] = int(numeros[0])
    
    # Detectar colores
    colores = ["rojo", "azul", "verde", "blanco", "negro", "amarillo", "naranja", "morado", "rosado", "gris"]
    for color in colores:
        if color in texto.lower():
            if datos["colores"]:
                datos["colores"] += f", {color}"
            else:
                datos["colores"] = color
    
    # Detectar número de teléfono
    texto_limpio = re.sub(r'[\s\-]', '', texto)
    numeros_telefono = re.findall(r'(\d{10})', texto_limpio)
    if numeros_telefono:
        datos["numero"] = numeros_telefono[0]
    
    # Detectar logo
    if "logo" in texto.lower() or "personalizado" in texto.lower():
        datos["logo"] = "Sí"
    elif "no logo" in texto.lower():
        datos["logo"] = "No"
    
    # Detectar tela
    if "algodón" in texto.lower() or "algodon" in texto.lower():
        datos["tela"] = "Algodón"
    elif "poliéster" in texto.lower() or "poliester" in texto.lower():
        datos["tela"] = "Poliéster"
    elif "dri-fit" in texto.lower() or "dri fit" in texto.lower():
        datos["tela"] = "Dri-Fit"
    
    # Detectar fecha
    fecha_match = re.search(r'(\d{1,2}\s*de\s*\w+\s*de\s*\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', texto)
    if fecha_match:
        datos["fecha"] = fecha_match.group(0)
    
    return datos

# --- FUNCIÓN PARA DETECTAR EL PASO ---
def detectar_paso(datos_cliente, es_primera_interaccion):
    if es_primera_interaccion:
        return 0
    if not datos_cliente["nombre"]:
        return 0
    if datos_cliente["nombre"] and not datos_cliente["deporte"]:
        return 1
    if datos_cliente["nombre"] and datos_cliente["deporte"] and not datos_cliente["cantidad"]:
        return 2
    if datos_cliente["nombre"] and datos_cliente["deporte"] and datos_cliente["cantidad"] and not datos_cliente["colores"]:
        return 3
    if datos_cliente["nombre"] and datos_cliente["deporte"] and datos_cliente["cantidad"] and datos_cliente["colores"]:
        return 7
    return 0

# --- ENDPOINTS ---
@app.get("/")
async def root():
    return {"mensaje": "API de ZM Deportes - Flujo con Saludo y Nombre"}

@app.post("/chat")
async def chat(mensaje: Mensaje):
    try:
        # --- DETECTAR SI ES PRIMERA INTERACCIÓN ---
        # En una implementación real, esto vendría del frontend
        es_primera_interaccion = True  # Siempre True para este ejemplo
        
        datos_cliente = extraer_datos(mensaje.texto)
        paso = detectar_paso(datos_cliente, es_primera_interaccion)
        nombre = datos_cliente["nombre"] or "Cliente"
        
        # --- PROMPT CON SALUDO PERSONALIZADO ---
        prompt_sistema = f"""
Eres el asistente de ventas de ZM Deportes, con 15 años de experiencia en uniformes deportivos personalizados.

PASO ACTUAL: {paso}
NOMBRE: {nombre if nombre else 'No conocido'}

REGLAS:
- PASO 0: "¡Hola! 👋 Bienvenido a ZM Deportes, tu aliado en uniformes deportivos personalizados con 15 años de experiencia. Antes de comenzar, ¿cómo te llamas?"
- PASO 1: "¡Hola [NOMBRE]! ¿Para qué deporte necesitas uniformes? Tenemos: ⚽ Fútbol, 🏀 Baloncesto, 🚴 Ciclismo, 🏐 Voleibol."
- PASO 2: "Perfecto, [NOMBRE]. ¿Cuántos uniformes necesitas?"
- PASO 3: "¿Qué colores principales te gustarían, [NOMBRE]?"
- PASO 4: "¿Necesitas incluir logo, nombres o números personalizados, [NOMBRE]?"
- PASO 5: "¿Qué tipo de tela prefieres? (Algodón, Poliéster, Dri-Fit), [NOMBRE]?"
- PASO 6: "¿Cuándo necesitas la entrega, [NOMBRE]? (Fecha aproximada)"
- PASO 7: Genera la cotización con el nombre de [NOMBRE] en el encabezado.

SIEMPRE usa el nombre. SOLO AVANZAS CUANDO EL CLIENTE RESPONDA. 
TONO: Amable, profesional, cercano y persuasivo.
"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensaje.texto}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        respuesta_asistente = response.choices[0].message.content
        
        # --- GENERAR COTIZACIÓN ---
        if paso >= 7 and datos_cliente["deporte"] and datos_cliente["cantidad"]:
            nombre_cliente = datos_cliente["nombre"] or "Cliente"
            deporte = datos_cliente["deporte"] or "fútbol"
            cantidad = datos_cliente["cantidad"] or 10
            colores = datos_cliente["colores"] or "por definir"
            logo = datos_cliente["logo"] or "No especificado"
            tela = datos_cliente["tela"] or "No especificada"
            fecha = datos_cliente["fecha"] or "No especificada"
            
            precio_base = 50000 if deporte == "fútbol" else 55000 if deporte == "baloncesto" else 50000
            total = precio_base * cantidad
            
            cotizacion = f"""
📋 COTIZACIÓN PARA {nombre_cliente.upper()}
═══════════════════════════════════
👤 Cliente: {nombre_cliente}
⚽ Deporte: {deporte}
👕 Cantidad: {cantidad}
🎨 Colores: {colores}
🖼️ Logo: {logo}
🧵 Tela: {tela}
📅 Fecha de entrega: {fecha}
───────────────────────────────────
💰 Precio unitario: ${precio_base:,}
💵 Subtotal: ${total:,}
🎯 Personalización: $15,000 adicional (opcional)
📦 Envío: contra-entrega
💲 TOTAL ESTIMADO: ${total:,}
═══════════════════════════════════
*{nombre_cliente}, esta cotización es válida por 7 días.
"""
            respuesta_asistente += "\n\n" + cotizacion
            
            if datos_cliente["numero"]:
                url_whatsapp = enviar_whatsapp(
                    datos_cliente["numero"],
                    f"Hola {nombre_cliente}, soy de ZM Deportes. Cotización para {cantidad} uniformes de {deporte}: ${total:,}. ¿Confirmamos?"
                )
                respuesta_asistente += f"\n\n📲 Confirma tu cotización por WhatsApp, {nombre_cliente}: {url_whatsapp}"
            else:
                respuesta_asistente += f"\n\n📱 {nombre_cliente}, comparte tu número para enviarte el enlace de WhatsApp."
        
        return {"respuesta": respuesta_asistente}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"respuesta": f"Lo siento, tuve un problema: {str(e)}"}