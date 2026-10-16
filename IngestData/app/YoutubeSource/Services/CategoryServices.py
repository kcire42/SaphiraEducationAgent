import asyncio
from app.Api.InternalComunication import ask_descion_system_one_jev

query = "Which category best describes the content of the video based on the provided summary?"
criteria = {
    "Anime": "Videos related to anime, including reviews, discussions, and fan content.",
    "Coding": "Videos that focus on programming, software development, and coding tutorials.",
    "Gaming": "Videos that cover video games, gameplay, reviews, and gaming culture.",
    "Psychology": "Videos that explore psychological concepts, mental health, and human behavior.",
    "Science": "Videos that discuss scientific topics, experiments, and discoveries.",
    "News": "Videos that report on current events, news stories, and journalism."}

def get_category_from_jev(summary: str,videoID: str) -> str:
    """
    Obtiene la categoría del contenido resumido utilizando un modelo de lenguaje interno a través de WebSocket.
    Args:
        summary (str): El resumen del contenido del video.
    Returns:
        str: La categoría determinada por el modelo de lenguaje.
    """
    try:
        # Ejecuta la función asincrónica ask_internal_llm en un bucle de eventos
        category = asyncio.run(ask_descion_system_one_jev(id_answer=videoID, question_type="choice", state=summary, instructions=query, criteria={}))
        return category
    except Exception as e:
        print(f"Error al obtener categoria de JEV: {e}")
        return None