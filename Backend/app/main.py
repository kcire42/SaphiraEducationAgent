#El punto de entrada de la aplicación FastAPI. Inicializa el servidor.
from fastapi import FastAPI, Request
from app.Api.Utilities import utilitiesRouter
from app.Api.ChatRoutes import chatRouter
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # El asterisco permite conexiones desde cualquier origen (Postman, HTML local, etc.)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(utilitiesRouter)
app.include_router(chatRouter)


logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para procesar cada solicitud HTTP."""
    
    # Si la petición va a nuestro websocket, la dejamos pasar sin interferir
    if request.url.path.startswith("/ws/"):
        return await call_next(request)
        
    response = await call_next(request)
    logger.info(f"Request: {request.method} {request.url} - Response status: {response.status_code}")
    return response

