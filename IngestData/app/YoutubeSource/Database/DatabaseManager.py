from datetime import datetime
from app.config import settings
import psycopg2
import os
import json






def get_connection():
    print(f"→ Estableciendo conexión a {settings.DB_HOST}, base: {settings.DB_NAME}")
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
    print(f"→ Iniciando ingreso de metadata del video '{metadata['title']}' a la base de datos...")
    conn = get_connection()
    print(f"metadata: {metadata}")
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
                        )""",(
                str(metadata['video_id']),
                str(metadata['url']),
                str(metadata['title']),
                duration,     # Enviado como int -> Postgres lo recibe como BIGINT
                views,        # Enviado como int -> Postgres lo recibe como BIGINT
                str(metadata['channel_id']),
                str(metadata['channel_name']),
                str(metadata['channel_url']),
                str(metadata['video_hash']),
                published_at # '2024-01-01'
            ))
        conn.commit()
        print(f"✅ Metadata del video '{metadata['title']}' ingresada correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al ingresar metadata del video '{metadata['title']}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def db_get_videos_by_status(status):
    print(f"→ Consultando videos pendientes de descarga...")
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
        print(f"✅ Se encontraron {len(pending_videos)} videos pendientes.")
        return pending_videos
    except Exception as e:
        print(f"❌ Error al obtener videos pendientes: {e}")
        return []
    finally:
        conn.close()
    

def download_youtube_ingestion(video_id):
    print(f"→ Iniciando descarga del video")  
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CALL 
                        "youtube".download_youtube_ingestion(
                        p_video_id := %s::text
                        )""",(
                        video_id,
                         ))
        conn.commit()
        print(f"✅ Descarga del video ID '{video_id}' iniciada correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al iniciar descarga del video ID '{video_id}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def validate_youtube_video(video_id):
    print(f"→ Iniciando validación de integridad para el video ID: {video_id}")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CALL
                    "youtube".validate_youtube_video(
                    p_video_id := %s::text
                    )""", (video_id,))
        conn.commit()
        print(f"✅ Validación de integridad para el video ID '{video_id}' iniciada correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error al iniciar validación de integridad para el video ID '{video_id}': {e}")
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
            print(f"⚠️ Archivo no encontrado: {file_path_json}")
            return False
        if not os.path.exists(file_path_mp3):
            print(f"⚠️ Archivo no encontrado: {file_path_mp3}")
            return False

        print(f"→ Archivo encontrado: {file_path_json}")
        return True
    except Exception as e:
        print(f"Error al verificar archivo para: {video_id}: {e}")
        return False

def file_get_video_metadata(video_id):
    # query para obtener metadata de la DB y confirmar que los datos del video descargado hagan match con el json 
    try:
        file_path = settings.DATA_DIR / f"{video_id}.info.json"
        if not os.path.exists(file_path):
            print(f"⚠️ Archivo no encontrado: {file_path}")
            return None
            # Leemos el archivo JSON para obtener información adicional del video
            # utf-8 para evitar problemas con caracteres especiales en los títulos
        print(f"→ Leyendo metadata del video desde el archivo: {file_path}")

        metaDataVideo = {}
        with open(file_path, 'r',encoding='utf-8') as f: 
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
        print(f"Información adicional para {video_id}:\n{metaDataVideo}")
        return metaDataVideo
    except Exception as e:
        print(f"Error al leer metadata para: {video_id}: {e}")
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
        print(f"✅ Metadata obtenida para '{video_id}': {video_metadata}")
        return video_metadata
    except Exception as e:
        print(f"❌ Error al obtener metadata para '{video_id}': {e}")
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
        print(f"✅ Contenido obtenido para {video_id}")
        return { 'video_id': video_content[0], 'transcription': video_content[2] , 'summary': video_content[1] }
    except Exception as e:
        print(f"❌ Error al obtener contenido para {video_id}: {e}")
        return []
    finally:
        conn.close()

def process_youtube_ingestion(video_id, transcription):
    print(f"Inciando proceso de transcripción de videos")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CALL 
                        "youtube".process_youtube_ingestion(
                        p_video_id := %s::text,
                        p_transcripcion := %s::text
                        )""",(
                        video_id, 
                        str(transcription)
                            ))
        conn.commit()
        print(f"✅ Proceso de transcripción de videos completado.")
        return True
    except Exception as e:
        print(f"❌ Error al procesar transcripción de videos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def summary_youtube_ingestion(video_id, summary):
    print(f"Inciando proceso de resumen de videos")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CALL 
                        "youtube".summary_youtube_ingestion(
                        p_video_id := %s::text,
                        p_summary := %s::text
                        )""",(
                        video_id, 
                        str(summary)
                            ))
        conn.commit()
        print(f"✅ Proceso de resumen de videos completado.")
        return True
    except Exception as e:
        print(f"❌ Error al procesar resumen de videos: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def error_youtube_ingestion(video_id, error_message):
    print(f"→ Registrando error para el video ID: {video_id}")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""CALL 
                        "youtube".error_youtube_ingestion(
                        p_video_id := %s::text,
                        p_error_message := %s::text
                        )""",(
                        video_id, 
                        error_message
                            ))
        conn.commit()
        print(f"✅ Error registrado para el video ID '{video_id}'.")
        return True
    except Exception as e:
        print(f"❌ Error al registrar error para el video ID '{video_id}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# flow text:
# pending -> downloaded -> validate -> processed -> summary -> vector -> learning -> completed 
# error


if __name__ == "__main__":
#     # Ejemplo de uso
#     sample_metadata = {
#         'video_id': '2',
#         'webpage_url': 'https://www.youtube.com/watch?v=abc1232',
#         'title': 'halo 2',     
#         'duration': 300,
#         'view_count': 1000,
#         'channel_id': 'channel1232',
#         'channel_name': 'Canal de Ejemplo',
#         'channel_url': 'https://www.youtube.com/channel/channel1232',
#         'video_hash': 'hash1232',
#         'upload_date': '2024-01-02'
#     }
#     sample_metadata_kakashi = {
#     'video_id': 'EmE7CJuRXA4', 
#     'webpage_url': 'https://www.youtube.com/watch?v=EmE7CJuRXA4', # URL limpia de YouTube
#     'title': 'Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR',
#     'duration': 802,
#     'view_count': 2184096,
#     'channel_id': 'UCK_dc2R_JcwP9lY419BNMOA',
#     'channel_name': 'Nombre del Canal', # Puedes poner el real si lo tienes
#     'channel_url': 'https://www.youtube.com/channel/UCK_dc2R_JcwP9lY419BNMOA',
#     'video_hash': 'hash_generado_123', # Hash para control de duplicados
#     'upload_date': '2024-03-27' # Ajustado al formato YYYY-MM-DD que pide tu datetime.strptime
# }
#     register_youtube_ingestion(sample_metadata_kakashi)
    status = db_get_videos_by_status('pending')
    print(f"Videos pendientes: {status}")
    
    #print(f"file_get_video_metadata: {file_get_video_metadata('Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR')}")
    #download_youtube_ingestion(sample_metadata)
    #process_youtube_ingestion(sample_metadata, "Transcripción de ejemplo para el video.")
    #meta = get_video_metadata('halo 2')
    #print(f"Metadata obtenida: {meta}")

