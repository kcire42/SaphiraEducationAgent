from app.Api.InternalComunication import ask_internal_llm
import asyncio

prompt_template = """
Eres un asistente especializado en síntesis y extracción de conocimiento de transcripciones de videos.

Objetivo:
{question}

Reglas y Formato:
- Comienza con una síntesis directa del tema principal (máximo 2-3 oraciones).
- Omite saludos, introducciones del presentador, menciones a suscripciones/patrocinios y despedidas.
- Mantén el contenido breve (alrededor de 100-150 palabras en total), priorizando hechos e insights concretos sobre generalidades.

Transcripción del video:
{content}

Resumen:"""
question = "Genera un resumen fiel, denso en información y sin redundancias del contenido provisto."




def get_summary_from_llm(text: str) -> str:
    """
    Obtiene un resumen del texto proporcionado utilizando un modelo de lenguaje interno a través de WebSocket.
    Args:
        text (str): El texto que se desea resumir.
        prompt_template (str): La plantilla de prompt para guiar la generación del resumen.
    Returns:
        str: El resumen generado por el modelo de lenguaje.
    """
    try:
        # Ejecuta la función asincrónica ask_internal_llm en un bucle de eventos
        summary = asyncio.run(ask_internal_llm(query=question, prompt_template=prompt_template, content=text))
        return summary
    except Exception as e:
        print(f"Error al obtener resumen del LLM: {e}")
        return None
