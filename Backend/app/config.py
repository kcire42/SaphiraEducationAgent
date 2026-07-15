import os 
from pathlib import Path


#BASE_DIR = Path(__file__).resolve().parent.parent



class Settings:
    ENV = os.getenv("APP_ENV", "local")
    MODELS_EMBEDDINGS_REGISTRY = {
        "all-MiniLM-L6-v2": {
            "max_tokens": 256,
            "chars_per_token": 4,
            "api_model": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "Gemini Embedding 1B": {
            "max_tokens": 512,
            "chars_per_token": 4,
            "api_model": "gemini-embedding-001",
        },
        "Gemini Embedding 2B": {
            "max_tokens": 512,
            "chars_per_token": 4,
            "api_model": "gemini-embedding-001",
        },
    }
    MODELS_EMBEDDINGS = list(MODELS_EMBEDDINGS_REGISTRY.keys())
    MODELS_LLM_REGISTRY = {
        'gemini-3.1-flash-lite': {'api_model': 'gemini-3.1-flash-lite'},
        'gemini-3.1-flash': {'api_model': 'gemini-3.1-flash'}, 
        'gemini-3.1': {'api_model': 'gemini-3.1'},
        'gemini-3.1-turbo': {'api_model': 'gemini-3.1-turbo'}}
    MODELS_LLM = list(MODELS_LLM_REGISTRY.keys())
    QDRANT_URL = os.getenv(
        "QDRANT_URL", 
        "http://qdrant:6333" if ENV == "docker" else "http://localhost:6333"
    )
settings = Settings()