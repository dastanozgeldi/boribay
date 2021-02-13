CREATE TABLE guild_config (
    guild_id bigint NOT NULL,
    prefix character varying(10) NOT NULL DEFAULT '.',
    welcome_channel bigint,
    embed_color integer DEFAULT 3553598,
    autorole bigint
)

CREATE TABLE users (
    guild_id bigint,
    user_id bigint,
    cash bigint,
    xp bigint,
    lvl bigint
)
