CREATE TABLE contenido(
     video_id text NOT NULL,
    summary text,
    transcripcion text NOT NULL,
    last_update timestamp with time zone NOT NULL,
    vector_summary vector,
    vector_transcripcion vector ,
    PRIMARY KEY(video_id) 
);