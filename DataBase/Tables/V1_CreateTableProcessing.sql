CREATE TABLE procesamiento(
     video_id text NOT NULL,
    status status NOT NULL,
    last_update timestamp with time zone NOT NULL ,
    PRIMARY KEY(video_id) 
);