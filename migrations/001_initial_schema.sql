-- WhatsApp Bridge — Supabase initial schema
-- Auto-applied on first bridge startup via SUPABASE_DB_URL

-- Chats table
CREATE TABLE IF NOT EXISTS chats (
    jid TEXT PRIMARY KEY,
    name TEXT,
    last_message_time TIMESTAMPTZ,
    last_message_preview TEXT,
    is_group BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT NOT NULL,
    chat_jid TEXT NOT NULL REFERENCES chats(jid) ON DELETE CASCADE,
    sender_jid TEXT,
    sender_name TEXT,
    content TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    is_from_me BOOLEAN DEFAULT FALSE,
    media_type TEXT,
    media_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, chat_jid)
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    jid TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    avatar_url TEXT,
    last_message_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_messages_chat_jid ON messages(chat_jid);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_content ON messages USING GIN (to_tsvector('english', coalesce(content, '')));
CREATE INDEX IF NOT EXISTS idx_chats_last_message ON chats(last_message_time DESC);
CREATE INDEX IF NOT EXISTS idx_chats_is_group ON chats(is_group);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);

-- Auto-update updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'chats_updated_at') THEN
        CREATE TRIGGER chats_updated_at
            BEFORE UPDATE ON chats
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'contacts_updated_at') THEN
        CREATE TRIGGER contacts_updated_at
            BEFORE UPDATE ON contacts
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
END;
$$;

-- RPC functions for PostgREST upserts (called via /rest/v1/rpc/...)
-- These preserve GREATEST/COALESCE logic that plain PostgREST upserts can't do.

CREATE OR REPLACE FUNCTION upsert_chat(
    p_jid TEXT,
    p_name TEXT,
    p_last_message_time TIMESTAMPTZ,
    p_is_group BOOLEAN,
    p_last_message_preview TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO chats (jid, name, last_message_time, is_group, last_message_preview)
    VALUES (p_jid, p_name, p_last_message_time, p_is_group, p_last_message_preview)
    ON CONFLICT (jid) DO UPDATE SET
        name = COALESCE(NULLIF(p_name, ''), chats.name),
        last_message_time = GREATEST(chats.last_message_time, p_last_message_time),
        is_group = p_is_group,
        last_message_preview = COALESCE(NULLIF(p_last_message_preview, ''), chats.last_message_preview);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION upsert_message(
    p_id TEXT,
    p_chat_jid TEXT,
    p_sender_jid TEXT,
    p_sender_name TEXT,
    p_content TEXT,
    p_timestamp TIMESTAMPTZ,
    p_is_from_me BOOLEAN,
    p_media_type TEXT,
    p_media_url TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO messages (id, chat_jid, sender_jid, sender_name, content, timestamp, is_from_me, media_type, media_url)
    VALUES (p_id, p_chat_jid, p_sender_jid, p_sender_name, p_content, p_timestamp, p_is_from_me, p_media_type, p_media_url)
    ON CONFLICT (id, chat_jid) DO UPDATE SET
        content = COALESCE(NULLIF(p_content, ''), messages.content),
        media_type = COALESCE(NULLIF(p_media_type, ''), messages.media_type),
        media_url = COALESCE(NULLIF(p_media_url, ''), messages.media_url);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION upsert_contact(
    p_jid TEXT,
    p_name TEXT,
    p_phone TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO contacts (jid, name, phone)
    VALUES (p_jid, p_name, p_phone)
    ON CONFLICT (jid) DO UPDATE SET
        name = COALESCE(NULLIF(p_name, ''), contacts.name),
        phone = COALESCE(NULLIF(p_phone, ''), contacts.phone);
END;
$$ LANGUAGE plpgsql;
