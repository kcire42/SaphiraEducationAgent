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
