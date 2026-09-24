CREATE TABLE error_logs(
     error_message text,
    last_update timestamp with time zone,
    video_id text,
    id bigint GENERATED ALWAYS AS IDENTITY NOT NULL ,
    PRIMARY KEY(id) 
);