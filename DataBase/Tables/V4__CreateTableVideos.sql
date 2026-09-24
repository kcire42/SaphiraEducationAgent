CREATE TABLE videos(
     video_id text NOT NULL,
    video_url text NOT NULL,
    video_title text NOT NULL,
    video_duration bigint NOT NULL,
    video_view_count bigint NOT NULL,
    channel_id text NOT NULL,
    hash_video text NOT NULL,
    published_at timestamp with time zone NOT NULL,
    last_update timestamp with time zone NOT NULL ,
    PRIMARY KEY(video_id) 
);