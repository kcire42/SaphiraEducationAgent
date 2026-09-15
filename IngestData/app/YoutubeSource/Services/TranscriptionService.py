import os 
import whisper
from tqdm import tqdm
import json
from app.YoutubeSource.Utilities.Utilities import generate_hash
from app.config import settings


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
        
    print(f"✅ Cargando modelo Whisper '{model_name}' en: {MODEL_PATH}")
    
    # download_root evita que se descargue en la carpeta oculta del usuario (~/.cache)
    return whisper.load_model(model_name, download_root=MODEL_PATH)

def transcribe_audio(video_id, storage_path=None, model=None, model_size_fallback="small"):
    """
    Transcribe un video_id específico.
    """
    # 1. Priorizar el path y el modelo proporcionados
    path = storage_path or storage_audio_path
    
    if model is None:
        print(f"⚠️ Cargando modelo por defecto ({model_size_fallback})...")
        model = setup_model(model_size_fallback)

    audio_file = f"{video_id}.mp3"
    audio_full_path = os.path.join(path, audio_file)
    json_info_path = os.path.join(path, f"{video_id}.info.json")

    # 2. Validación de archivo (Más eficiente que listar todo el directorio)
    if not os.path.exists(audio_full_path):
        print(f"❌ El archivo {audio_file} no existe en {path}")
        return {'video_id': video_id, 'transcription': None}

    try:
        print(f"→ Transcribiendo con Whisper: {audio_file}")
        # fp16=False esencial para CPU
        result = model.transcribe(audio_full_path, fp16=False)
        
        # 3. Intento de recuperar ID real de la metadata
        final_video_id = video_id
        if os.path.exists(json_info_path):
            try:
                with open(json_info_path, 'r', encoding='utf-8') as f:
                    meta_info = json.load(f)
                    final_video_id = meta_info.get('id', video_id)
            except Exception as e:
                print(f"⚠️ No se pudo leer el JSON de metadata: {e}")

        return {
            'video_id': final_video_id,
            'transcription': result['text']
        }

    except Exception as e:
        print(f"❌ Error en la transcripción de {video_id}: {e}")
        return {'video_id': video_id, 'transcription': None}

# if __name__ == "__main__":
#     model = setup_model()
#     trans = transcribe_audio(model, storage_audio_path, 'Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR')
#     print(f"Transcripción {trans}")


