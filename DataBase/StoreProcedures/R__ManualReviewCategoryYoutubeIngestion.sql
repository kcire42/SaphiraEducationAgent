-- Elimina la copia que se creó por error en el esquema public
DROP PROCEDURE IF EXISTS public.manual_review_category_youtube_ingestion(text);

CREATE OR REPLACE PROCEDURE youtube.manual_review_category_youtube_ingestion(
    IN p_video_id text
)
    LANGUAGE plpgsql
    AS $procedure$
BEGIN
    -- 1. Actualizar estado a 'manual_review'
    INSERT INTO "youtube".processing (video_id, status, last_update)
    VALUES (p_video_id, 'manual_review', NOW())
    ON CONFLICT (video_id) DO UPDATE
    SET status = EXCLUDED.status, last_update = NOW();  
END;
$procedure$