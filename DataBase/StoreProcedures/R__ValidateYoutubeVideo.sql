CREATE OR REPLACE PROCEDURE youtube.validate_youtube_video(IN p_video_id text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Validar Integridad de Datos
    INSERT INTO "youtube".procesamiento (video_id, status, last_update)
    VALUES (p_video_id, 'validate', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();

END;
$procedure$
