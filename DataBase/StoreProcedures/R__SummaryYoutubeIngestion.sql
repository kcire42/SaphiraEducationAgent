CREATE OR REPLACE PROCEDURE youtube.summary_youtube_ingestion(IN p_video_id text, IN p_summary text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Actualizar resumen
    UPDATE "youtube".contenido
    SET summary = p_summary,
        last_update = NOW()
    WHERE video_id = p_video_id;

    -- 2. Inicializar Estado
    INSERT INTO "youtube".procesamiento (video_id, status, last_update)
    VALUES (p_video_id, 'summary', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$
