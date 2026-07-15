from fastapi import APIRouter
from app.PreData.SeedDatabase import seed

utilitiesRouter = APIRouter(prefix="/utilities")

@utilitiesRouter.get("/health")
async def health_check():
    """
    Endpoint de prueba para verificar que el servicio está activo.
    """
    return {"status": "ok"}

@utilitiesRouter.post("/training")
async def training_endpoint():
    """
    Endpoint para gestionar el entrenamiento del modelo.
    """
    result = seed("app/Data/How_AI_Ruined_the_Classroom.txt", "temario")
    print(f"Proceso de seed completado para la colección 'temario'. Total de chunks: {result['total_chunks']}")
    return result
    