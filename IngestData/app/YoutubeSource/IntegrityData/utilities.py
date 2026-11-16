from app.YoutubeSource.Database.DatabaseManager import reset_youtube_ingestion, get_video_metadata
import logging

logger = logging.getLogger(__name__)

# Mapa código -> nombre de estado del pipeline de ingesta.
INGESTION_STATUS: dict[int, str] = {
	1: "pending",
	2: "downloaded",
	3: "validate",
	4: "processed",
	5: "summary",
	6: "category",
	7: "manual_review",
	8: "vector",
	9: "learning",
	10: "completed",
	11: "error",
}


def return_status_youtube_ingestion(video_id: str, status: int) -> bool:
	"""
	Devuelve el video al estado indicado en la base de datos,
	permitiendo reintentar el proceso desde ese punto.

	Args:
		video_id (str): ID del video a reiniciar.
		status (int): Código del estado destino (ver INGESTION_STATUS).

	Returns:
		bool: True si el estado se actualizó correctamente, False en caso contrario.
	"""
	# Validación sin tocar la BD: un solo lookup en lugar de `in` + `.get()`
	status_name: str | None = INGESTION_STATUS.get(status)
	if status_name is None:
		logger.error(
			"Estado inválido: %s. Debe ser un número entre %d y %d.",
			status, min(INGESTION_STATUS), max(INGESTION_STATUS),
		)
		return False

	try:
		if not get_video_metadata(video_id):
			logger.error("El video con ID %s no existe en la base de datos.", video_id)
			return False

		if not reset_youtube_ingestion(video_id, status_name):
			logger.error("No se pudo reiniciar el estado del video %s.", video_id)
			return False
	except Exception:
		# logger.exception incluye el traceback completo
		logger.exception("Error al reiniciar el estado del video %s", video_id)
		return False

	logger.info("Estado del video %s reiniciado a '%s'.", video_id, status_name)
	return True
