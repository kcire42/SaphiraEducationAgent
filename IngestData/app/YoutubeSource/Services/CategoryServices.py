import asyncio
import logging
from app.Api.InternalComunication import ask_descion_system_one_jev

logger = logging.getLogger(__name__)

query = "Which category best describes the content of the video based on the provided summary?"
criteria = {
	"Anime": "Videos related to anime, including reviews, discussions, and fan content.",
	"Coding": "Videos that focus on programming, software development, and coding tutorials.",
	"Gaming": "Videos that cover video games, gameplay, reviews, and gaming culture.",
	"Psychology": "Videos that explore psychological concepts, mental health, and human behavior.",
	"Science": "Videos that discuss scientific topics, experiments, and discoveries.",
	"Series/Cinema": "Videos that analyze, review, or discuss TV series and movies.",
	"Technology/IA": "Videos that cover technology trends, gadgets, and artificial intelligence.",
	"News": "Videos that report on current events, news stories, and journalism."
}


def get_category_from_jev(summary: str, videoID: str) -> tuple[str | None, float | None]:
	"""
	Obtiene la categoría del contenido resumido utilizando un modelo de lenguaje interno a través de WebSocket.
	Args:
		summary (str): El resumen del contenido del video.
	Returns:
		tuple[str | None, float | None]: La categoría determinada por JEV y su confianza, o (None, None) si hubo un error.
	"""
	try:
		# Ejecuta la función asincrónica ask_descion_system_one_jev en un bucle de eventos
		response = asyncio.run(ask_descion_system_one_jev(id_answer=videoID, question_type="Choice", state=summary, instructions=query, criteria=criteria))
		if response.get("error"):
			logger.error("Error devuelto por JEV para el video %s: %s", videoID, response["error"])
			return None, None
		# Respuesta esperada: {"answers": {videoID: {"type": "choice", "choice": "...", "confidence": ..., "probabilities": {...}}}}
		return response["answers"][videoID]["choice"], response["answers"][videoID]["confidence"]
	except Exception:
		logger.exception("Error al obtener categoria de JEV para el video %s", videoID)
		return None, None
