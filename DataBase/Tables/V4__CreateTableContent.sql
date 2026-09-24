CREATE TABLE youtube.content(
    video_id text NOT NULL,
    summary text,
    transcripcion text NOT NULL,
    vector_summary vector(1536), 
    vector_transcripcion vector(1536),
    last_update timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY(video_id),
    CONSTRAINT fk_video FOREIGN KEY(video_id) REFERENCES youtube.videos(video_id) ON DELETE CASCADE
);