-- Financial Data PII Scrubber — PostgreSQL schema (PostgreSQL 18+)
-- Apply as the database owner:
--   psql -U scrubber -h localhost -d financial_scrubber -f sql/schema.sql
--
-- Design notes:
-- * Only scrubbed text is stored; raw statements are never persisted.
-- * Placeholder tokens are stored for auditability, but raw values are never stored
--   (no hashes either, to avoid brute-forcing low-entropy identifiers).
-- * JSONB is used for the structured analysis because its shape evolves.

BEGIN;

CREATE TABLE IF NOT EXISTS documents (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    status                TEXT NOT NULL DEFAULT 'completed'
                          CHECK (status IN ('processing', 'completed', 'failed')),
    combined_scrubbed_text TEXT NOT NULL,
    file_count            INTEGER NOT NULL DEFAULT 0,
    scrubbed_chars        INTEGER NOT NULL DEFAULT 0,
    placeholder_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS document_files (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    filename     TEXT NOT NULL,
    format       TEXT NOT NULL,
    char_count   INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'processed'
                 CHECK (status IN ('processed', 'skipped', 'failed')),
    error        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_files_document_id
    ON document_files (document_id);

CREATE TABLE IF NOT EXISTS pii_placeholders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_type  TEXT NOT NULL,
    placeholder  TEXT NOT NULL,
    occurrences  INTEGER NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, placeholder)
);

CREATE TABLE IF NOT EXISTS analyses (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    model          TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    structured     JSONB NOT NULL,
    raw_response   TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_document_id
    ON analyses (document_id);

CREATE TABLE IF NOT EXISTS conversations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_document_id
    ON conversations (document_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content          TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id
    ON chat_messages (conversation_id, created_at);

COMMIT;
