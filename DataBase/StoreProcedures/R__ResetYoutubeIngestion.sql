CREATE OR REPLACE PROCEDURE youtube.reset_youtube_ingestion(IN p_video_id text, IN p_status text)
 LANGUAGE plpgsql
 AS $procedure$
DECLARE
    v_current_status youtube.processing_status;
    v_target_status  youtube.processing_status;
BEGIN
    -- 1. Validar que el estado destino exista en el enum
    BEGIN
        v_target_status := p_status::youtube.processing_status;
    EXCEPTION WHEN invalid_text_representation THEN
        RAISE EXCEPTION 'Estado destino inválido: "%"', p_status;
    END;

    -- 2. Obtener el estado actual y bloquear la fila mientras se valida
    SELECT status INTO v_current_status
    FROM "youtube".processing
    WHERE video_id = p_video_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El video % no existe en youtube.processing', p_video_id;
    END IF;

    -- 3. Solo se permite regresar a un estado anterior. El enum es ordenado y 'error'
    --    es el último valor, así que desde 'error' se puede regresar a cualquier estado.
    IF v_target_status >= v_current_status THEN
        RAISE EXCEPTION 'No se puede pasar el video % de "%" a "%": el estado destino debe ser anterior al actual',
            p_video_id, v_current_status, v_target_status;
    END IF;

    -- 4. Actualizar estado
    UPDATE "youtube".processing
    SET status = v_target_status,
        last_update = NOW()
    WHERE video_id = p_video_id;
END;
$procedure$
