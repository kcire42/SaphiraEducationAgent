CREATE OR REPLACE FUNCTION youtube.get_video_status(p_video_id text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Devuelve el estado actual del video en el pipeline, o NULL si no está registrado
    RETURN (
        SELECT a1.status::text
        FROM "youtube".processing as a1
        WHERE a1.video_id = p_video_id
    );
END;
$function$
