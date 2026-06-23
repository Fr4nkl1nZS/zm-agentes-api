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
        "https://zmdeportes.com",
        "http://zmdeportes.com",
        "https://www.zmdeportes.com",
        "*"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- MODELO DE DATOS ---
class Mensaje(BaseModel):
    texto: str

# --- CONFIGURACIÓN DE GROQ ---
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- CONFIGURACIÓN DE WHATSAPP ---
NUMERO_WHATSAPP = "573167568428"  # Reemplaza con tu número

def enviar_whatsapp(numero, mensaje):
    numero_limpio = ''.join(filter(str.isdigit, numero))
    mensaje_codificado = quote(mensaje)
    return f"https://api.whatsapp.com/send?phone={numero_limpio}&text={mensaje_codificado}"

# --- FUNCIÓN PARA EXTRAER DATOS DEL MENSAJE ---
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

    # --- DETECTAR NOMBRE ---
    # Buscar frases como "me llamo", "soy", "mi nombre es"
    nombre_match = re.search(r'(?:me llamo|soy|mi nombre es)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+)?)', texto.lower())
    if nombre_match:
        datos["nombre"] = nombre_match.group(1).title()
    else:
        # Si no hay frase explícita, buscar palabras que parezcan nombres (capitalizadas)
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
    
    # Detectar cantidad (números)
    numeros = re.findall(r'(\d+)', texto)
    if numeros:
        datos["cantidad"] = int(numeros[0])
    
    # Detectar colores
    colores = ["rojo", "azul", "verde", "blanco", "negro", "amarillo", 
               "naranja", "morado", "rosado", "gris", "blanco"]
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

# --- FUNCIÓN PARA DETECTAR EL PASO DE LA CONVERSACIÓN ---
def detectar_paso(datos_cliente):
    """Determina en qué paso está el cliente según los datos extraídos"""
    # Si no tiene nombre, el paso es 0 (preguntar nombre)
    if not datos_cliente["nombre"]:
        return 0
    
    # Si tiene nombre y deporte, pero no cantidad
    if datos_cliente["nombre"] and datos_cliente["deporte"] and not datos_cliente["cantidad"]:
        return 2
    
    # Si tiene nombre, deporte y cantidad, pero no colores
    if datos_cliente["nombre"] and datos_cliente["deporte"] and datos_cliente["cantidad"] and not datos_cliente["colores"]:
        return 3
    
    # Si tiene todos los datos básicos
    if datos_cliente["nombre"] and datos_cliente["deporte"] and datos_cliente["cantidad"] and datos_cliente["colores"]:
        return 7  # Paso final: cotización
    
    # Si solo tiene nombre (paso 1)
    return 1
   

# --- ENDPOINT PRINCIPAL ---
@app.get("/")
async def root():
    return {"mensaje": "API de ZM Deportes Agentes con Flujo Guiado"}

@app.post("/chat")
async def chat(mensaje: Mensaje):
    try:
        # --- EXTRAER DATOS DEL MENSAJE ---
        datos_cliente = extraer_datos(mensaje.texto)
        paso = detectar_paso(datos_cliente)
        
        # --- CONSTRUIR PROMPT CON FLUJO GUIADO ---
        prompt_sistema = f"""
Eres el asistente de ventas de ZM Deportes.

PASO ACTUAL: {paso}
NOMBRE DEL CLIENTE: {nombre}

REGLAS:
- PASO 0: Pregunta "¡Hola! Bienvenido a ZM Deportes. Antes de comenzar, ¿cómo te llamas?"
- PASO 1: "¡Hola {nombre}! ¿Para qué deporte necesitas uniformes? Tenemos: ⚽ Fútbol, 🏀 Baloncesto, 🚴 Ciclismo, 🏐 Voleibol."
- PASO 2: "Perfecto, {nombre}. ¿Cuántos uniformes necesitas?"
- PASO 3: "¿Qué colores principales te gustarían, {nombre}?"
- PASO 4: "¿Necesitas incluir logo, nombres o números personalizados, {nombre}?"
- PASO 5: "¿Qué tipo de tela prefieres? (Algodón, Poliéster, Dri-Fit), {nombre}?"
- PASO 6: "¿Cuándo necesitas la entrega, {nombre}? (Fecha aproximada)"
- PASO 7: Genera la cotización con el nombre de {nombre} en el encabezado.

SIEMPRE usa el nombre del cliente en cada interacción.
SOLO AVANZAS AL SIGUIENTE PASO CUANDO EL CLIENTE RESPONDA.
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
        
        # --- GENERAR COTIZACIÓN CON NOMBRE ---
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
                    f"Hola {nombre_cliente}, soy de ZM Deportes. Aquí tienes tu cotización para {cantidad} uniformes de {deporte} con colores {colores}: ${total:,}. ¿Confirmamos?"
                )
                respuesta_asistente += f"\n\n📲 Haz clic aquí para confirmar tu cotización por WhatsApp, {nombre_cliente}: {url_whatsapp}"
            else:
                respuesta_asistente += f"\n\n📱 {nombre_cliente}, para confirmar tu cotización, comparte tu número de teléfono y te enviaremos el enlace de WhatsApp."
        
        return {"respuesta": respuesta_asistente}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"respuesta": f"Lo siento, tuve un problema: {str(e)}"}