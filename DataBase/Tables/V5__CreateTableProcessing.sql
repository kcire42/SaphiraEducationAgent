CREATE TYPE youtube.processing_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE youtube.processing(
    video_id text NOT NULL,
    status youtube.processing_status DEFAULT 'PENDING' NOT NULL,
    last_update timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY(video_id),
    CONSTRAINT fk_video FOREIGN KEY(video_id) REFERENCES youtube.videos(video_id) ON DELETE CASCADE
);