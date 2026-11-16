import os
import logging
import whisper
from tqdm import tqdm
import json
from app.YoutubeSource.Utilities.Utilities import generate_hash
from app.config import settings

logger = logging.getLogger(__name__)

# Carpeta actual del script
storage_audio_path = settings.DATA_DIR
MODEL_PATH = settings.MODELS_DIR


def setup_model(model_name=None):
	"""
	Carga el modelo de Whisper. 
	Si no se especifica nombre, usa el de settings.
	"""
	if model_name is None:
		model_name = settings.MODEL_WHISPER

	logger.info("✅ Cargando modelo Whisper '%s' en: %s", model_name, MODEL_PATH)

	# download_root evita que se descargue en la carpeta oculta del usuario (~/.cache)
	return whisper.load_model(model_name, download_root=MODEL_PATH)


def transcribe_audio(video_id, storage_path=None, model=None, model_size_fallback="small"):
	"""
	Transcribe un video_id específico.
	"""
	# 1. Priorizar el path y el modelo proporcionados
	path = storage_path or storage_audio_path

	if model is None:
		logger.warning("⚠️ Cargando modelo por defecto (%s)...", model_size_fallback)
		model = setup_model(model_size_fallback)

	audio_file = f"{video_id}.mp3"
	audio_full_path = os.path.join(path, audio_file)
	json_info_path = os.path.join(path, f"{video_id}.info.json")

	# 2. Validación de archivo (Más eficiente que listar todo el directorio)
	if not os.path.exists(audio_full_path):
		logger.error("❌ El archivo %s no existe en %s", audio_file, path)
		return {'video_id': video_id, 'transcription': None}

	try:
		logger.info("→ Transcribiendo con Whisper: %s", audio_file)
		# fp16=False esencial para CPU
		result = model.transcribe(audio_full_path, fp16=False)

		# 3. Intento de recuperar ID real de la metadata
		final_video_id = video_id
		if os.path.exists(json_info_path):
			try:
				with open(json_info_path, 'r', encoding='utf-8') as f:
					meta_info = json.load(f)
					final_video_id = meta_info.get('id', video_id)
			except Exception:
				logger.warning("⚠️ No se pudo leer el JSON de metadata para %s", video_id, exc_info=True)

		return {
			'video_id': final_video_id,
			'transcription': result['text']
		}

	except Exception:
		logger.exception("❌ Error en la transcripción de %s", video_id)
		return {'video_id': video_id, 'transcription': None}

# if __name__ == "__main__":
# 	model = setup_model()
# 	trans = transcribe_audio(model, storage_audio_path, 'Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR')
# 	logger.info("Transcripción %s", trans)
