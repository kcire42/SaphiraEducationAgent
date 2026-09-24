CREATE TABLE youtube.videos(
    video_id text NOT NULL,
    channel_id text NOT NULL, -- Ahora está referenciado
    video_url text NOT NULL,
    video_title text NOT NULL,
    video_duration bigint NOT NULL,
    video_view_count bigint NOT NULL,
    hash_video text NOT NULL,
    published_at timestamp with time zone NOT NULL,
    last_update timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY(video_id),
    CONSTRAINT fk_channel FOREIGN KEY(channel_id) REFERENCES youtube.channels(channel_id) ON DELETE CASCADE
);