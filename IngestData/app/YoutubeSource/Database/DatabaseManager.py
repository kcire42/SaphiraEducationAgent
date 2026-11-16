from datetime import datetime
from app.config import settings
import psycopg2
import os
import json
import logging

logger = logging.getLogger(__name__)


def get_connection():
	logger.debug("→ Estableciendo conexión a %s, base: %s", settings.DB_HOST, settings.DB_NAME)
	conn = psycopg2.connect(
		host=settings.DB_HOST,
		port=settings.DB_PORT,
		database=settings.DB_NAME,
		user=settings.DB_USER,
		password=settings.DB_PASSWORD,
		connect_timeout=5
	)

	return conn


def register_youtube_ingestion(metadata):
	logger.info("→ Iniciando ingreso de metadata del video '%s' a la base de datos...", metadata['title'])
	conn = get_connection()
	logger.debug("metadata: %s", metadata)
	try:
		duration = int(metadata.get('duration', 0))
		views = int(metadata.get('view_count', 0))
		published_at = datetime.strptime(metadata['upload_date'], '%Y-%m-%d')
		with conn.cursor() as cur:
			cur.execute("""
				CALL "youtube".register_youtube_ingestion(
					p_video_id := %s::text,
					p_video_url := %s::text,
					p_video_title := %s::text,
					p_video_duration := %s::bigint,
					p_video_view_count := %s::bigint,
					p_channel_id := %s::text,
					p_channel_name := %s::text,
					p_channel_url := %s::text,
					p_hash_video := %s::text,
					p_published_at := %s::timestamp
						)""", (
				str(metadata['video_id']),
				str(metadata['url']),
				str(metadata['title']),
				duration,     # Enviado como int -> Postgres lo recibe como BIGINT
				views,        # Enviado como int -> Postgres lo recibe como BIGINT
				str(metadata['channel_id']),
				str(metadata['channel_name']),
				str(metadata['channel_url']),
				str(metadata['video_hash']),
				published_at  # '2024-01-01'
			))
		conn.commit()
		logger.info("✅ Metadata del video '%s' ingresada correctamente.", metadata['title'])
		return True
	except Exception:
		logger.exception("❌ Error al ingresar metadata del video '%s'", metadata['title'])
		conn.rollback()
		return False
	finally:
		conn.close()


def db_get_videos_by_status(status):
	logger.debug("→ Consultando videos con estado '%s'...", status)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""
						SELECT *
						FROM
						"youtube".get_data_videos(
						p_status := %s::text
						)""", (status,))
			pending_videos = cur.fetchall()
		logger.info("✅ Se encontraron %d videos con estado '%s'.", len(pending_videos), status)
		return pending_videos
	except Exception:
		logger.exception("❌ Error al obtener videos con estado '%s'", status)
		return []
	finally:
		conn.close()


def download_youtube_ingestion(video_id):
	logger.debug("→ Iniciando registro de descarga del video ID '%s'", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".download_youtube_ingestion(
						p_video_id := %s::text
						)""", (
						video_id,
						))
		conn.commit()
		logger.info("✅ Descarga del video ID '%s' registrada correctamente.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al iniciar descarga del video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def validate_youtube_video(video_id):
	logger.debug("→ Iniciando validación de integridad para el video ID: %s", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL
					"youtube".validate_youtube_video(
					p_video_id := %s::text
					)""", (video_id,))
		conn.commit()
		logger.info("✅ Validación de integridad para el video ID '%s' registrada correctamente.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al iniciar validación de integridad para el video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def file_get_video_from_folder(video_id):
	# Validar que el archivo existe en la carpeta de datos, lo que confirmaría que se descargó correctamente
	try:
		file_path_json = settings.DATA_DIR / f"{video_id}.info.json"
		file_path_mp3 = settings.DATA_DIR / f"{video_id}.mp3"

		if not os.path.exists(file_path_json):
			logger.warning("⚠️ Archivo no encontrado: %s", file_path_json)
			return False
		if not os.path.exists(file_path_mp3):
			logger.warning("⚠️ Archivo no encontrado: %s", file_path_mp3)
			return False

		logger.debug("→ Archivo encontrado: %s", file_path_json)
		return True
	except Exception:
		logger.exception("Error al verificar archivo para: %s", video_id)
		return False


def file_get_video_metadata(video_id):
	# query para obtener metadata de la DB y confirmar que los datos del video descargado hagan match con el json 
	try:
		file_path = settings.DATA_DIR / f"{video_id}.info.json"
		if not os.path.exists(file_path):
			logger.warning("⚠️ Archivo no encontrado: %s", file_path)
			return None
			# Leemos el archivo JSON para obtener información adicional del video
			# utf-8 para evitar problemas con caracteres especiales en los títulos
		logger.debug("→ Leyendo metadata del video desde el archivo: %s", file_path)

		metaDataVideo = {}
		with open(file_path, 'r', encoding='utf-8') as f:
			meta_info = json.load(f)
			video_id_json = meta_info.get('id')
			video_title_json = meta_info.get('title')
			video_url_json = meta_info.get('webpage_url')
			video_duration_json = meta_info.get('duration')
			video_view_count_json = meta_info.get('view_count')
			channel_id_json = meta_info.get('channel_id')
			channel_name_json = meta_info.get('channel_name')
			metaDataVideo = {
				'id': video_id_json,
				'title': video_title_json,
				'webpage_url': video_url_json,
				'duration': video_duration_json,
				'view_count': video_view_count_json,
				'channel_id': channel_id_json,
				'channel_name': channel_name_json
			}
		logger.debug("Información adicional para %s:\n%s", video_id, metaDataVideo)
		return metaDataVideo
	except Exception:
		logger.exception("Error al leer metadata desde archivo para: %s", video_id)
		return None


def get_video_metadata(video_id):
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""
						SELECT *
						FROM
						"youtube".get_video_metadata(
						p_video_id := %s::text
						)""", (video_id,))
			video_metadata = cur.fetchone()
		logger.debug("✅ Metadata obtenida para '%s': %s", video_id, video_metadata)
		return video_metadata
	except Exception:
		logger.exception("❌ Error al obtener metadata para '%s'", video_id)
		return []
	finally:
		conn.close()


def get_video_content(video_id):
	"""
	Obtiene el contenido de un video desde la base de datos.
	
	Returns:
		dict con keys: video_id, transcription, summary
		[] si no se encuentra o hay un error
	"""
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""
						SELECT *
						FROM
						"youtube".get_video_content(
						p_video_id := %s::text
						)""", (video_id,))
			video_content = cur.fetchone()
		logger.debug("✅ Contenido obtenido para %s", video_id)
		return {'video_id': video_content[0], 'transcription': video_content[2], 'summary': video_content[1]}
	except Exception:
		logger.exception("❌ Error al obtener contenido para %s", video_id)
		return []
	finally:
		conn.close()


def process_youtube_ingestion(video_id, transcription):
	logger.debug("Iniciando proceso de transcripción en DB para el video ID: %s", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".process_youtube_ingestion(
						p_video_id := %s::text,
						p_transcripcion := %s::text
						)""", (
						video_id,
						str(transcription)
						))
		conn.commit()
		logger.info("✅ Proceso de transcripción del video ID '%s' completado.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al procesar transcripción del video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def summary_youtube_ingestion(video_id, summary):
	logger.debug("Iniciando proceso de resumen en DB para el video ID: %s", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".summary_youtube_ingestion(
						p_video_id := %s::text,
						p_summary := %s::text
						)""", (
						video_id,
						str(summary)
						))
		conn.commit()
		logger.info("✅ Proceso de resumen del video ID '%s' completado.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al procesar resumen del video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def error_youtube_ingestion(video_id, error_message):
	logger.debug("→ Registrando error para el video ID: %s", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".error_youtube_ingestion(
						p_video_id := %s::text,
						p_error_message := %s::text
						)""", (
						video_id,
						error_message
						))
		conn.commit()
		logger.warning("⚠️ Error registrado en DB para el video ID '%s': %s", video_id, error_message)
		return True
	except Exception:
		logger.exception("❌ Error al registrar error para el video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def category_youtube_ingestion(video_id, category, confidence):
	logger.debug("Iniciando proceso de categorización en DB para el video ID: %s", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".category_youtube_ingestion(
						p_video_id := %s::text,
						p_category := %s::text,
						p_confidence := %s::float
						)""", (
						video_id,
						str(category),
						float(confidence)
						))
		conn.commit()
		logger.info("✅ Proceso de categorización del video ID '%s' completado.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al procesar categorización del video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def manual_review_youtube_ingestion(video_id):
	logger.debug("→ Marcando video ID '%s' para revisión manual.", video_id)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".manual_review_category_youtube_ingestion(
						p_video_id := %s::text
						)""", (
						video_id,
						))
		conn.commit()
		logger.warning("⚠️ Video ID '%s' marcado para revisión manual.", video_id)
		return True
	except Exception:
		logger.exception("❌ Error al marcar video ID '%s' para revisión manual", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


def reset_youtube_ingestion(video_id, status):
	logger.debug("→ Reiniciando proceso de ingreso para el video ID: %s a '%s'", video_id, status)
	conn = get_connection()
	try:
		with conn.cursor() as cur:
			cur.execute("""CALL 
						"youtube".reset_youtube_ingestion(
						p_video_id := %s::text,
						p_status := %s::text
						)""", (
						video_id,
						status
						))
		conn.commit()
		logger.info("✅ Proceso de ingreso reiniciado para el video ID '%s' a '%s'.", video_id, status)
		return True
	except Exception:
		logger.exception("❌ Error al reiniciar proceso de ingreso para el video ID '%s'", video_id)
		conn.rollback()
		return False
	finally:
		conn.close()


# flow text:
# pending -> downloaded -> validate -> processed -> summary -> category -> vector -> learning -> completed 
# error


if __name__ == "__main__":
# 	# Ejemplo de uso
# 	sample_metadata = {
# 		'video_id': '2',
# 		'webpage_url': 'https://www.youtube.com/watch?v=abc1232',
# 		'title': 'halo 2',     
# 		'duration': 300,
# 		'view_count': 1000,
# 		'channel_id': 'channel1232',
# 		'channel_name': 'Canal de Ejemplo',
# 		'channel_url': 'https://www.youtube.com/channel/channel1232',
# 		'video_hash': 'hash1232',
# 		'upload_date': '2024-01-02'
# 	}
# 	sample_metadata_kakashi = {
# 	'video_id': 'EmE7CJuRXA4', 
# 	'webpage_url': 'https://www.youtube.com/watch?v=EmE7CJuRXA4', # URL limpia de YouTube
# 	'title': 'Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR',
# 	'duration': 802,
# 	'view_count': 2184096,
# 	'channel_id': 'UCK_dc2R_JcwP9lY419BNMOA',
# 	'channel_name': 'Nombre del Canal', # Puedes poner el real si lo tienes
# 	'channel_url': 'https://www.youtube.com/channel/UCK_dc2R_JcwP9lY419BNMOA',
# 	'video_hash': 'hash_generado_123', # Hash para control de duplicados
# 	'upload_date': '2024-03-27' # Ajustado al formato YYYY-MM-DD que pide tu datetime.strptime
# }
# 	register_youtube_ingestion(sample_metadata_kakashi)
	status = db_get_videos_by_status('pending')
	logger.info("Videos pendientes: %s", status)

	#logger.info("file_get_video_metadata: %s", file_get_video_metadata('Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR'))
	#download_youtube_ingestion(sample_metadata)
	#process_youtube_ingestion(sample_metadata, "Transcripción de ejemplo para el video.")
	#meta = get_video_metadata('halo 2')
	#logger.info("Metadata obtenida: %s", meta)
