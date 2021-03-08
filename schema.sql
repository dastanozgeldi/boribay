CREATE TABLE guild_config (
    guild_id bigint NOT NULL,
    prefix character varying(10) NOT NULL DEFAULT '.',
    welcome_channel bigint,
    embed_color integer DEFAULT 3553598,
    autorole bigint
)

CREATE TABLE todos (
    id serial primary key,
    user_id bigint not null,
    content text,
    added_at timestamp without time zone,
    jump_url text
)