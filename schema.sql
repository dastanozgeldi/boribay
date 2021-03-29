CREATE TABLE IF NOT EXISTS guild_config (
    guild_id bigint NOT NULL,
    prefix character varying(10) NOT NULL DEFAULT '.',
    welcome_channel bigint,
    embed_color integer DEFAULT 3553598,
    autorole bigint,
    automeme bigint
)

CREATE TABLE IF NOT EXISTS todos (
    id serial primary key,
    user_id bigint not null,
    content text,
    added_at timestamp without time zone,
    jump_url text
)

CREATE TABLE IF NOT EXISTS users (
    user_id bigint NOT NULL,
    wallet integer DEFAULT 0,
    bank integer DEFAULT 0,
    blacklisted boolean DEFAULT false
)