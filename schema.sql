CREATE TABLE public.guild_config
(
    guild_id bigint NOT NULL,
    prefix character varying(10) COLLATE pg_catalog."default" NOT NULL DEFAULT '.'::character varying,
    welcome_channel bigint,
    mod_log bigint,
    embed_color integer DEFAULT 3553598,
    image_url text COLLATE pg_catalog."default",
    CONSTRAINT prefixes_pkey PRIMARY KEY (guild_id)
)