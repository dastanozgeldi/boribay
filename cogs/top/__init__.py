from utils.Cog import Cog
from discord.ext import commands, tasks, flags
from collections import Counter
from utils.Checks import has_voted
from typing import Optional
from discord import Member


class TopGG(Cog):
    """Top.GG related commands-events extension.
    If you are a voter for Boribay, you can find
    features of this module quite useful."""
    icon = '<:topgg:809359742899978272>'
    name = 'TopGG'

    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

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
        self.bot.log.info('-> Posted a fresh guild count on Top.GG')

    @commands.group(name='top', invoke_without_command=True)
    async def top_gg(self, ctx):
        """A TopGG-related commands parent.
        Type `help top` to see its subcommands."""
        await ctx.send_help('top')

    @top_gg.command()
    @has_voted()
    async def didivote(self, ctx):
        """Check did you vote last 12 hours."""
        await ctx.send('You\'ve already voted, thanks!')

    @top_gg.command()
    async def howmuch(self, ctx, member: Optional[Member]):
        """Check how many times did you vote."""
        member = member or ctx.author
        data = Counter([f"{i['username']}#{i['discriminator']}" for i in await self.bot.dblpy.get_bot_upvotes()])
        await ctx.reply(f'You have voted {data[str(member)]} times.')

    @top_gg.command()
    async def vote(self, ctx):
        """Vote for the bot on Top.GG!"""
        await ctx.send(f'Alright the link is right here, thanks for the vote! {self.bot.config["links"]["topgg_url"]}')

    @flags.add_flag('--limit', type=int, default=5)
    @top_gg.command(cls=flags.FlagCommand, aliases=['lb'])
    async def leaderboard(self, ctx, **flags):
        """Leaderboard of top voters for Boribay. Defaults to 5 users,
        however you can specify the limitation of the leaderboard."""
        medals = ['🥇', '🥈', '🥉'] + ['🏅' for _ in range(flags['limit'] - 3)]
        d = Counter([f"{i['username']}#{i['discriminator']}" for i in await self.bot.dblpy.get_bot_upvotes()]).most_common(flags['limit'])
        embed = self.bot.embed.default(
            ctx, title='Top voters of this month.',
            description='\n'.join(f'{k} **{i[0]}** → {i[1]} votes' for i, k in zip(d, medals)),
            url=self.bot.config['links']['topgg_url']
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TopGG(bot))
