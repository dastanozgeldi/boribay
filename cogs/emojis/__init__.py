import re
from discord.ext import commands
from utils.Cog import Cog

# finder was stolen from R. Danny: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/fuzzy.py#L130-L149


def finder(text, collection, *, key=None):
    suggestions = []
    text = str(text)
    pat = '.*?'.join(map(re.escape, text))
    regex = re.compile(pat, flags=re.IGNORECASE)
    for item in collection:
        to_search = key(item) if key else item
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup):
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    return [z for _, _, z in sorted(suggestions, key=sort_key)]


class Emotes(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def emoji_handler(self, message):
        if message.author.bot:
            return

        matches = re.compile(r";(?P<name>[a-zA-Z0-9_]+)").findall(message.content)
        emojis = []

        for match in matches:
            e = finder(match, self.bot.emojis, key=lambda emoji: emoji.name)

            if e[0].is_usable():
                emojis.append(str(e[0]))

        await message.channel.send(' '.join(emojis))


def setup(bot):
    bot.add_cog(Emotes(bot))
