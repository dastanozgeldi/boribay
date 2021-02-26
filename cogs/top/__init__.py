from collections import Counter

from discord.ext import commands, flags
from utils.Checks import has_voted
from utils.Cog import Cog


class TopGG(Cog):
    """Top.GG related commands-events extension.
    If you are a voter for Boribay, you can find
    features of this module quite useful."""
    icon = '<:topgg:809359742899978272>'
    name = 'TopGG'

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    @commands.command()
    @has_voted()
    async def didivote(self, ctx):
        """Check did you vote last 12 hours."""
        await ctx.send('You\'ve already voted, thanks!')

    @commands.command()
    async def vote(self, ctx):
        """Vote for the bot on Top.GG!"""
        await ctx.send(f'Alright the link is right here, thanks for the vote! {ctx.bot.config["links"]["topgg_url"]}')

    @flags.add_flag('--limit', type=int, default=5, help='Set the limit of users you want to see.')
    @flags.command(aliases=['lb'])
    async def leaderboard(self, ctx, **flags):
        """Leaderboard of top voters for Boribay. Defaults to 5 users,
        however you can specify the limitation of the leaderboard."""
        medals = ['🥇', '🥈', '🥉'] + ['✨' for num in range(flags['limit'] - 3)]
        d = Counter([i['username'] for i in await ctx.bot.dblpy.get_bot_upvotes()]).most_common(flags['limit'])
        embed = ctx.bot.embed.default(
            ctx, title='Top voters of this month.',
            description='\n'.join(f'{k} **{i[0]}** → {i[1]} votes' for i, k in zip(d, medals)),
            url=ctx.bot.config['links']['topgg_url']
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TopGG())
