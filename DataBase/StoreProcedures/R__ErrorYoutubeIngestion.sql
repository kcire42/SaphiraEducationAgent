CREATE OR REPLACE PROCEDURE youtube.error_youtube_ingestion(IN p_video_id text, IN p_error_message text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN
    -- 1. Actualizar error en tabla 
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'error', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();

    -- 2. Insertar mensaje de error en tabla de errores
    INSERT INTO "youtube".error_logs (video_id, error_message, last_update)
    VALUES (p_video_id, p_error_message, NOW());
END;
$procedure$
