CREATE OR REPLACE FUNCTION youtube.get_data_videos(p_status text)
 RETURNS TABLE(video_id text, video_title text, video_url text, video_duration bigint, video_view_count bigint, channel_id text)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN query
    SELECT
        a1.video_id,
        a2.video_title,
        a2.video_url,
        a2.video_duration,
        a2.video_view_count,
        a2.channel_id
    FROM "youtube".procesamiento as a1
    INNER JOIN "youtube".videos as a2
    ON a1.video_id = a2.video_id
    -- ✅ Cambiamos esto: casteamos el parámetro al tipo de la columna
    -- Si no sabes el nombre del ENUM, puedes usar ::text en la columna
    WHERE a1.status::text = p_status; 
END;
$function$
