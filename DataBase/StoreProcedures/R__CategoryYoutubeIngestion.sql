CREATE OR REPLACE PROCEDURE youtube.category_youtube_ingestion(IN p_video_id text, IN p_category text)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Actualizar categoría
    UPDATE "youtube".content
    SET category = p_category,
        last_update = NOW()
    WHERE video_id = p_video_id;

    -- 2. Inicializar Estado
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'category', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$
