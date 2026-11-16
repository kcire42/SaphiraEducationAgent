-- Elimina la versión anterior sin confidence para no dejar una sobrecarga
DROP PROCEDURE IF EXISTS youtube.category_youtube_ingestion(text, text);

CREATE OR REPLACE PROCEDURE youtube.category_youtube_ingestion(IN p_video_id text, IN p_category text, IN p_confidence float)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 

    -- 1. Actualizar categoría
    UPDATE "youtube".content
    SET category = p_category,
        category_confidence = p_confidence,
        last_update = NOW()
    WHERE video_id = p_video_id;

    -- 2. Inicializar Estado
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'category', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET status = EXCLUDED.status, last_update = NOW();
END;
$procedure$
