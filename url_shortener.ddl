CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.url_mapping (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_link TEXT NOT NULL,
    expiry_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);