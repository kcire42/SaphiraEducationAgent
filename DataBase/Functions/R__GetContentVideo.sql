CREATE OR REPLACE FUNCTION youtube.get_content_video(p_video_id text)
 RETURNS TABLE(video_id text, transcripcion text)
 LANGUAGE plpgsql
AS $function$ 
BEGIN
    RETURN query
    SELECT
    a1.video_id,
    a1.transcripcion
    FROM "youtube".contenido as a1
    where a1.video_id = p_video_id;
END;
$function$
