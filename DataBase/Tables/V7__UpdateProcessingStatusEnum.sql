ALTER TYPE youtube.processing_status RENAME TO processing_status_old;

CREATE TYPE youtube.processing_status AS ENUM (
    'pending',
    'downloaded',
    'validate',
    'processed',
    'summary',
    'vector',
    'learning',
    'completed',
    'error'
);

ALTER TABLE youtube.processing
    ALTER COLUMN status DROP DEFAULT;

ALTER TABLE youtube.processing
    ALTER COLUMN status TYPE youtube.processing_status
    USING lower(status::text)::youtube.processing_status;

ALTER TABLE youtube.processing
    ALTER COLUMN status SET DEFAULT 'pending';

DROP TYPE youtube.processing_status_old;
