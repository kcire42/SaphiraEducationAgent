CREATE OR REPLACE PROCEDURE youtube.download_youtube_ingestion(IN p_video_id text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Inicializar Estado
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'downloaded', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$