CREATE OR REPLACE FUNCTION youtube.get_video_metadata(p_video_id text)
 RETURNS TABLE(video_id text, video_title text, video_url text, video_duration bigint, video_view_count bigint, channel_id text, channel_name text)
 LANGUAGE plpgsql
AS $function$
BEGIN 
    RETURN query
    SELECT
        a1.video_id,
        a1.video_title,
        a1.video_url,
        a1.video_duration,
        a1.video_view_count,
        a1.channel_id,
        a2.channel_name
    FROM "youtube".videos as a1
    INNER JOIN "youtube".channels as a2 ON a1.channel_id = a2.channel_id
    WHERE a1.video_id = p_video_id;
END;
$function$
