import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_PORT = int(os.getenv("POSTGRES_PORT"))
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
    MODELS_DIR = Path(os.getenv("MODELS_DIR", "/app/models"))
    MODEL_WHISPER = os.getenv("MODEL_WHISPER", "base")
    API_WS_URL = os.getenv("API_WS_URL", "ws://api:8000/ws/llm")
    API_WS_URL_DECISION = os.getenv("API_WS_URL_DECISION", "ws://api:8000/ws/decision")


settings = Settings()
    