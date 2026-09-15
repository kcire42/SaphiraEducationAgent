from app.YoutubeSource.Services.YoutubeService import get_videos_from_youtube_channel, download_audio
from app.YoutubeSource.Services.TranscriptionService import transcribe_audio
from app.YoutubeSource.Database.DatabaseManager import *
from app.YoutubeSource.IntegrityData.IntegrityData import validate_video_metadata
from app.YoutubeSource.Services.SummaryServices import get_summary_from_llm
import asyncio
import logging


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.debug("🚀 Iniciando el proceso de ingestión de videos de YouTube...")
    youtube_channel = 'https://www.youtube.com/@Platzi'
    # 1. INGESTIÓN: Obtener y registrar videos nuevos
    videos_channel = get_videos_from_youtube_channel(youtube_channel, current_start=1, batch_size=3)
    if not videos_channel:
        logger.debug("❌ No se encontraron videos en el canal. Verifica la URL o el estado del canal.")
    else:
        for video in videos_channel:
            if register_youtube_ingestion(video):
                logger.debug(f"✅ Registrado: {video['title']}")
            else:
                error_youtube_ingestion(video['video_id'], "Error al registrar video en DB.")
                logger.debug(f"❌ Error al registrar: {video['title']}")
    logger.debug(f"✅ Videos obtenidos del canal: {len(videos_channel)} with details: {videos_channel}")
    logger.debug("✅ Proceso de ingestión de videos de YouTube completado.")
    # 2. DESCARGA: Procesar videos con status 'pending'
    pending_videos = db_get_videos_by_status('pending')
    if len(pending_videos) == 0:
        logger.debug("✅ No hay videos pendientes de descarga.")
    else:
        logger.debug(f"✅ Videos pendientes de procesamiento: {len(pending_videos)}, details: {pending_videos}")
        for video in pending_videos:
        # Desempaquetado claro (asumiendo el orden de tu SELECT actual)
            video_id, title, video_url, *_ = video 
            
            logger.debug(f"→ Descargando: {title}")
            result = download_audio(video_url, video_id)
            
            if result.get('status') == 'downloaded':
                # Actualizar estado en DB y validar
                if download_youtube_ingestion(video_id):
                    logger.debug(f"✅ Audio guardado y estado actualizado.")
                    
                    # Validación de integridad
                    if validate_video_metadata(video_id): # Sugerencia: validar por video_id si es posible
                        if validate_youtube_video(video_id): # Cambia a video_id si tu función lo soporta
                            logger.debug(f"✅ Validación exitosa.")
                        else:
                            error_youtube_ingestion(video_id, "Error en validación de video en DB.")
                            logger.debug(f"❌ Falló validación de video en db.")
                    else:
                        error_youtube_ingestion(video_id, "Error en validación de integridad.")
                        logger.debug(f"❌ Falló validación de integridad.")
            else:
                logger.debug(f"⚠️ El video: {title} (ID: {video_id}) no se descargó correctamente, por lo que se omite la validación.")
    
    # 3. TRANSCRIPCIÓN: Procesar videos con status 'validate'
    validate_videos = db_get_videos_by_status('validate')

    if len(validate_videos) == 0:
        logger.debug("✅ No hay videos pendientes de transcripción.")
    else:
        logger.debug(f"✅ Videos pendientes de transcripción: {len(validate_videos)}, details: {validate_videos}")
    
        for video in validate_videos:
            video_id,*_ = video
            
            logger.debug(f"→ Transcribiendo: {video_id}")
            video_transcription = transcribe_audio(video_id)
            
            # Usamos .get() para evitar KeyErrors
            texto = video_transcription.get('transcription')
            
            if texto:
                if process_youtube_ingestion(video_id, texto):
                    logger.debug(f"✅ Transcripción procesada y finalizada.")
                else:
                    error_youtube_ingestion(video_id, "Error al guardar transcripción en DB.")
                    logger.debug(f"❌ Error al guardar transcripción en DB.")
            else:
                error_youtube_ingestion(video_id, "Error: La transcripción volvió vacía.")
                logger.debug(f"❌ Error: La transcripción volvió vacía.")

   


    # 4. Crear resumen del texto 

    processed_videos = db_get_videos_by_status('processed')

    if len(processed_videos) == 0:
        logger.debug("✅ No hay videos pendientes de resumen.")
    else:

        logger.debug(f"✅ Videos listos para resumen: {len(processed_videos)}, details: {processed_videos}")
        for video in processed_videos:
            video_id,*_ = video
            logger.debug(f"→ Resumiendo: {video_id}")
            video_content = get_video_content(video_id) 
            logger.debug(f"✅ Contenido del video {video_content.get('transcription')[:30]}...")
            if video_content.get('transcription'):
                summary = asyncio.run(get_summary_from_llm(video_content.get('transcription')))
                if summary:
                    logger.debug(f"✅ Resumen del video {summary}...")
                    summary_status = summary_youtube_ingestion(video_id, summary)
                    if summary_status:
                        logger.debug(f"✅ Resumen guardado y estado actualizado.")
                    else:
                        error_youtube_ingestion(video_id, "Error al guardar resumen en DB.")
                        logger.error(f"❌ Error al guardar resumen en DB.")
                else:
                    error_youtube_ingestion(video_id, "Error al obtener resumen del LLM Service.")
                    logger.error(f"❌ Error al obtener resumen del LLM Service.")
            else:
                error_youtube_ingestion(video_id, "Error: No se encontró transcripción para resumir.")
                logger.error(f"❌ Error: No se encontró transcripción para resumir.")


    logger.debug("🏁 Proceso completado.")


            
        
        
        
