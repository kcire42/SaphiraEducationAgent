import os
from google import genai
from google.genai import types
from app.config import settings


def _resolve_api_model(model_name: str) -> str:
    model_info = settings.MODELS_EMBEDDINGS_REGISTRY.get(model_name)
    if not model_info:
        raise ValueError(f"Model '{model_name}' not found in registry.")
    return model_info["api_model"]


def get_embedding(
    text: str,
    model_name: str = "Gemini Embedding 2B",
    task_type: str = "retrieval_document",
) -> list[float]:
    """
    Genera el embedding de un texto usando la API de Gemini.

    Args:
        text: Texto a vectorizar.
        model_name: Clave del modelo en MODELS_EMBEDDINGS_REGISTRY.
        task_type: "retrieval_document" para chunks indexados,
            "retrieval_query" para la pregunta del usuario.
    """

    """
    retrieval_document (La "Huella" del Contenido)
    Se utiliza durante la fase de Ingesta (Indexing).

    Propósito: Transformar tus documentos (chunks) en vectores que representan su significado semántico.

    ¿Qué sucede aquí? Cuando procesas un texto largo, lo divides en trozos (chunks). 
    Cada uno pasa por un modelo de embedding para crear un vector.

    El objetivo: Que Qdrant entienda de qué trata ese fragmento de información. 
    Es el material que quedará almacenado en tu base de datos esperando ser consultado.

    retrieval_query (El "Espejo" de la Pregunta)
    Se utiliza durante la fase de Consulta (Querying).

    Propósito: Transformar la pregunta del usuario en un vector que coincida con los vectores de los documentos.

    ¿Qué sucede aquí? Cuando el usuario escribe una pregunta, debes usar exactamente el mismo modelo de 
    embedding que usaste para los documentos. Si usaste text-embedding-3-small para los chunks, 
    debes usar text-embedding-3-small para la pregunta.

    El objetivo: Traducir la intención del usuario al "espacio vectorial". 
    Al hacer esto, el vector de la pregunta quedará "cerca" 
    (matemáticamente hablando, por similitud de coseno) de los vectores de los documentos 
    que contienen la respuesta.
    """
    api_model = _resolve_api_model(model_name)
    client = genai.Client(api_key=os.getenv("API_KEY_Gemini"))

    result = client.models.embed_content(
        model=api_model,
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return result.embeddings[0].values


def get_embeddings_batch(
    chunks: list[str],
    model_name: str = "Gemini Embedding 2B",
    task_type: str = "retrieval_document",
) -> list[list[float]]:
    """
    Genera embeddings para una lista de chunks en una sola llamada a la API.
    """
    api_model = _resolve_api_model(model_name)
    client = genai.Client(api_key=os.getenv("API_KEY_Gemini"))

    result = client.models.embed_content(
        model=api_model,
        contents=chunks,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [embedding.values for embedding in result.embeddings]
