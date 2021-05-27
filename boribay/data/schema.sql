CREATE TABLE IF NOT EXISTS guild_config (
    guild_id BIGINT NOT NULL,
    prefix VARCHAR(10) NOT NULL DEFAULT '.',
    welcome_channel BIGINT,
    embed_color INTEGER DEFAULT 3553598,
    autorole BIGINT,
    logging_channel BIGINT
);

CREATE TABLE IF NOT EXISTS todos (
    id SERIAL PRIMARY KEY,
    user_id BIGINT not null,
    content TEXT,
    added_at TIMESTAMP WITHOUT TIME ZONE,
    jump_url TEXT
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT NOT NULL,
    wallet INTEGER DEFAULT 0,
    bank INTEGER DEFAULT 0,
    blacklisted BOOLEAN DEFAULT false,
    bio TEXT,
    locale VARCHAR(20) DEFAULT 'en_US'::character varying NOT NULL
);

CREATE TABLE IF NOT EXISTS ideas (
    id SERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    approved BOOLEAN DEFAULT false,
    added TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);
