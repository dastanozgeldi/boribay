# Should belong to /utils/

import json

languages = ['en', 'ru']
with open('data/translations.json', 'rb') as f:
    translations = json.loads(f.read().decode())


def _(ctx, message):
    g = ctx.guild
    lang = 'en' if not g else ctx.bot.guild_cache[g.id]['language']

    if lang == 'en':
        return message

    try:
        translation = translations[message][lang]
    except (KeyError, UnboundLocalError):
        pass

    return translation
