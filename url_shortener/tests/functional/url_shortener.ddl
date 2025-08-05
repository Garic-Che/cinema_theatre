CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.url_mapping (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_link TEXT NOT NULL,
    expiry_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO content.url_mapping (id, raw_link, expiry_date)
VALUES
('f47ac10b-58cc-4372-a567-0e02b2c3d479', 'http://auth-service:8000/test1', '01-01-2124'),
('9a42b832-1f47-4c95-841e-2ea6db01ef89', 'http://auth-service:8000/test2', '01-01-2000')
