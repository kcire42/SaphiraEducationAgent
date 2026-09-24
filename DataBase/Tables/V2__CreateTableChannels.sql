CREATE TABLE youtube.channels(
    channel_id text NOT NULL,
    channel_name text NOT NULL,
    channel_url text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY(channel_id) 
);