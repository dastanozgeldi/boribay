from utils.Cog import Cog
from discord.ext import tasks, commands
from collections import Counter


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

    @Cog.listener()
    async def on_guild_post(self):
        await self.bot.log.info('-> Posted a fresh guild count on Top.GG')

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx):
        d = dict(Counter([f"{i['username']}#{i['discriminator']}" for i in await self.bot.dblpy.get_bot_upvotes()]))
        d = sorted(d.items(), key=lambda x: x[1], reverse=True)
        embed = self.bot.embed.default(
            ctx,
            title=f'Top{" 10" if len(d) >= 10 else ""} voters of this month.',
            description='\n'.join([f'**{k}** — {v} votes' for k, v in d]),
            url=self.bot.config['links']['topgg_url']
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TopGG(bot))
