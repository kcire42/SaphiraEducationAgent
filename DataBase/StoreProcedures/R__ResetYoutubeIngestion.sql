CREATE OR REPLACE PROCEDURE youtube.reset_youtube_ingestion(IN p_video_id text, IN p_status text)
 LANGUAGE plpgsql
 AS $procedure$
BEGIN
    -- 1. Actualizar estado 
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, p_status, NOW())
    ON CONFLICT (video_id) DO UPDATE
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$
