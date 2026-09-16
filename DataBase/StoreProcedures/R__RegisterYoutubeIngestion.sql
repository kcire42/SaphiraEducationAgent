CREATE OR REPLACE PROCEDURE youtube.register_youtube_ingestion(IN p_video_id text, IN p_video_url text, IN p_video_title text, IN p_video_duration bigint, IN p_video_view_count bigint, IN p_channel_id text, IN p_channel_name text, IN p_channel_url text, IN p_hash_video text, IN p_published_at timestamp without time zone)
 LANGUAGE plpgsql
AS $procedure$
BEGIN 
    -- 1. Manejar el Canal
    INSERT INTO "youtube".channels (channel_id, channel_name, channel_url)
    VALUES (p_channel_id, p_channel_name, p_channel_url)
    ON CONFLICT (channel_id) DO NOTHING;

    -- 2. Manejar el Video
    INSERT INTO "youtube".videos (video_id, video_url, video_title, video_duration, video_view_count, channel_id, hash_video, published_at, last_update)
    VALUES (p_video_id, p_video_url, p_video_title, p_video_duration, p_video_view_count, p_channel_id, p_hash_video, p_published_at, NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET video_view_count = EXCLUDED.video_view_count, 
        hash_video = EXCLUDED.hash_video,
        last_update = NOW();

    -- 3. Inicializar Estado
    INSERT INTO "youtube".procesamiento (video_id, status, last_update)
    VALUES (p_video_id, 'pending', NOW())
    ON CONFLICT (video_id) DO UPDATE 
    SET last_update = NOW();
END;
$procedure$
