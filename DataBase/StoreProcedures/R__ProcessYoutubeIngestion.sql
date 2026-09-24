CREATE OR REPLACE PROCEDURE youtube.process_youtube_ingestion(IN p_video_id text, IN p_transcripcion text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Actualizar transcripción
    INSERT INTO "youtube".content (video_id, transcripcion, last_update  )
    VALUES (p_video_id, p_transcripcion, NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET transcripcion = EXCLUDED.transcripcion, last_update = NOW();

    -- 2. Inicializar Estado
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'processed', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$
