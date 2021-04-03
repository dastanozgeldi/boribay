CREATE TABLE IF NOT EXISTS guild_config (
    guild_id BIGINT NOT NULL,
    prefix VARCHAR(10) NOT NULL DEFAULT '.',
    welcome_channel BIGINT,
    embed_color INTEGER DEFAULT 3553598,
    autorole BIGINT,
    automeme BIGINT,
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
    warns INTEGER
);