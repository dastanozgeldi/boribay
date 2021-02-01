from utils.Cog import Cog
from discord.ext import tasks


class TopGG(Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        try:
            await self.bot.dblpy.post_guild_count()
        except Exception as e:
            self.bot.log.warning(f'Failed to post server count\n{type(e).__name__}: {e}')

    @Cog.listener()
    async def on_dbl_vote(self, data):
        await self.bot.get_channel(766571630268252180).send(data)


def setup(bot):
    bot.add_cog(TopGG(bot))
