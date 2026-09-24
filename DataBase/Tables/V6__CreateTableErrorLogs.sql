CREATE TABLE youtube.error_logs(
    id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    video_id text,
    error_message text NOT NULL,
    last_update timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY(id),
    CONSTRAINT fk_video FOREIGN KEY(video_id) REFERENCES youtube.videos(video_id) ON DELETE CASCADE
);