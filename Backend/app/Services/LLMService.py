#Lógica para conectarse a la API de Claude/Anthropic (manejo de prompts y streaming).
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.config import settings 
import os

load_dotenv()

def _resolve_api_model(model_name: str) -> str:
    model_info = settings.MODELS_LLM_REGISTRY.get(model_name)
    if not model_info:
        raise ValueError(f"Model '{model_name}' not found in registry.")
    return model_info["api_model"]

def callLLM_Cloud(prompt:str, model_name: str = "gemini-3.1-flash-lite") -> str:
    """
    Llama a la API de Gemini para procesar un prompt
    y obtener un respuesta generada por el modelo de lenguaje.
    Args:
        prompt (str): El prompt de entrada que se enviará al modelo de lenguaje.
        model_name (str): El nombre del modelo de lenguaje a utilizar.
    Returns:
        str: La respuesta generada por el modelo de lenguaje.
    """
    try:
        client = genai.Client(api_key=os.getenv("API_KEY_Gemini"))
        model_id = _resolve_api_model(model_name)
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=512
            )
        )
        return {
            "text": response.text, # Extrae el texto principal
            "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            "total_duration": 0 # Google no devuelve duración total en el metadata de tokens
        }
    except Exception as e:
        return {
            "error": str(e),
            "text": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration": 0
        }
    
