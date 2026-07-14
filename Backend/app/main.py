#El punto de entrada de la aplicación FastAPI. Inicializa el servidor.
from fastapi import FastAPI, Request
import logging

app = FastAPI()

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para procesar cada solicitud HTTP."""
    response = await call_next(request)
    
    # Ahora esto funcionará perfecto sin romper el formato
    logger.info(f"Request: {request.method} {request.url} - Response status: {response.status_code}")
    
    return response