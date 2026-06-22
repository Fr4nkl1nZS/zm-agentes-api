import os
from dotenv import load_dotenv

from config import PRECIOS
load_dotenv()  # Cargar variables de entorno desde el archivo .env
from openai import OpenAI

# Configurar la API key de openAI
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

class Coordinador:
    def __init__(self):
        self.agentes = {
            "servicio":AgenteServicio(),
            "diseño": AgenteDiseño(),
            "marketing": AgenteMarketing(),
            "control": AgenteControl(),
            "cotización": AgenteCotización()
        }

    def procesar(self, mensaje_usuario):
        print(f"\n👤 Usuario: {mensaje_usuario}")

        #1. Identificar que agente debe atender
        agente_asignado = self._identificar_agente(mensaje_usuario)
        print(f"🤖 Asignado a: {agente_asignado.nombre}")

        #2. El agente procesa la consulta
        respuesta = agente_asignado.procesar(mensaje_usuario)

        #3. Mostrar la respuesta del agente
        print(f"🌨️ Respuesta: {respuesta}")
        return respuesta
    
    def _identificar_agente(self, mensaje):
        # Palabras clave para identificar la intención del usuario
        if any(palabra in mensaje.lower() for palabra in ["pedido", "estado", "entrega", "reclamo", "problema"]):
            return self.agentes["servicio"]
        elif any(palabra in mensaje.lower() for palabra in ["diseño", "color", "uniforme", "personalizar", "cear"]):
            return self.agentes["diseño"]
        elif any(palabra in mensaje.lower() for palabra in ["promoción", "oferta", "precio", "descuento"]):
            return self.agentes["marketing"]
        elif any(palabra in mensaje.lower() for palabra in ["cotización", "precio", "oferta"]):
            return self.agentes["cotización"]
        else:
                return self.agentes["servicio"]  # Por defecto, asignar al agente de servicio
        
class AgenteServicio:
    def __init__(self):
        self.nombre = "Servicio al Cliente"

    def procesar(self, mensaje):
        # Usar openAi para generar una respuesta basada en el mensaje del usuario
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {"role": "system", "content": """ Eres el agente de servicio al cliente de ZM Deportes. Tu objetivo es ayudar a los clientes con sus consultas. 
                 Responde de manera amable y útil.
                 Si no sabes algo, sé honesto y ofrece contactar por whatsapp.
                 """},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    
class AgenteDiseño:
    def __init__(self):
        self.nombre = "Diseñador creativo"

    def procesar(self, mensaje):
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {"role": "system", "content": """ Eres el agente de diseño de ZM Deportes, una empresa con 15 años de experiencia en uniformes personalizados. 
                 Tu objetivo es asesorar a los clientes para que diseñen el uniforme perfecto.

                 Reglas: 
                 - Pregunta siempre por: deporte, cantidad, colores, tipo de tela y si necesitan logo.
                 - Sugiere combinaciones basadas en tendencias actuales.
                 - Ofrece ejemplos de personalización (nombres, números, parches, etc).
                 - Menciona los beneficios de los materiales de ZM Deportes: durabilidad, comodidad y tecnologia innovadora.
                 - Si el cliente no sabe qué quiere, preg+untale sobre el estilo de su equipo (moderno, clásico, agresivo).


                 Termina siempre preguntando si necesita una cotización formal. 
                 """},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content
    
class AgenteMarketing:
    def __init__(self):
        self.nombre = "Marketing Maverick"

    def procesar(self, mensaje):
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {"role": "system", "content": """ Eres el agente de marketing de ZM Deportes. 
                 Eres persuacivo y conoces las tendencias deportivas. 
                 Sugiere promociones y productos según la consulta.
                 """},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.9,
        )
        return response.choices[0].message.content
    
class AgenteControl:
    def __init__(self):
        self.nombre = "Control de Calidad"

    def procesar(self, mensaje):
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {"role": "system", "content": """ Eres el agente de control de calidad de ZM Deportes. 
                 Monitorea que todo funcione correctamente. 
                 Si detectas algún problema, notificalo y sugiere mejoras.
                 """},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content
    
    from config import PRECIOS, MENSAJES
    
class AgenteCotización:
    def __init__(self):
        # 1. Extraer deporte y cantidad del mensaje
        self.nombre = "Agente de Cotización"
        self.precios_base = PRECIOS

    def procesar(self, mensaje):
        # 1. Extraer deporte y cantidad del mensaje
        deporte = self._detectar_deporte(mensaje)
        cantidad = self._detectar_cantidad(mensaje)

        # 2. Calcular precio
        if deporte in self.precios_base:
            precio_unitario = self.precios_base[deporte]
            precio_total = precio_unitario * cantidad
            respuesta = f"📋 Cotización para {cantidad} uniformes de {deporte}:\n"
            respuesta += f"💰 Precio unitario: ${precio_unitario:,}\n"
            respuesta += f"💵 Total: ${precio_total:,}\n"
            respuesta += "📦 Incluye: envío a todo Colombia y personalización básica.\n"
            respuesta += "¿Quieres que te envíe la cotización formal por WhatsApp?"
        else:
            respuesta = "Por favor, indícame el deporte y la cantidad para darte una cotización precisa."
        return respuesta

    def _detectar_deporte(self, mensaje):
        if "futbol" in mensaje.lower():
            return "futbol"
        elif "baloncesto" in mensaje.lower():
            return "baloncesto"
        elif "ciclismo" in mensaje.lower():
            return "ciclismo"
        else:
            return "futbol"  # Por defecto
    
    def _detectar_cantidad(self, mensaje):
        import re
        numeros = re.findall(r'\d+', mensaje)
        return int(numeros[0]) if numeros else 10  # Por defecto 10

    

# === PUNTO DE ENTRADA ===
if __name__ == "__main__":
    coordinador = Coordinador()
    print("=" * 50)
    print("🤖 ZM Deportes - Sistema de Agentes")
    print("=" * 50)
    print("Escribe 'salir' para terminar")
    print("=" * 50)

    while True:
        mensaje = input("\n👤 Tú: ")
        if mensaje.lower() == "salir":
            print("👋 ¡Hasta luego!")
            break
        if mensaje.strip() == "":
            continue
        respuesta = coordinador.procesar(mensaje)