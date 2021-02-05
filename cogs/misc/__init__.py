from time import perf_counter
from utils.Cog import Cog
from discord.ext import commands


class Miscellaneous(Cog):
    '''Misc commands extension. Here owner inserts commands that aren't
    related to other categories, such as hello, ping etc.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '💫 Miscellaneous'

    @commands.command()
    async def vote(self, ctx):
        """Vote for the bot on Top.GG!"""
        await ctx.send('Alright the link is right here, thanks for the vote! %s' % ctx.bot.config['links']['topgg_url'])

    @commands.command()
    async def prefix(self, ctx):
        """See bot's prefix."""
        prefix = '.' if not ctx.guild else self.bot.config['prefixes'][ctx.guild.id]
        await ctx.send(embed=self.bot.embed.default(ctx, description=f'The prefix is: `{prefix}` or {self.bot.user.mention}'))

    @commands.command(aliases=['links'])
    async def invite(self, ctx):
        """Some useful invites (support server and the bot itself)"""
        embed = self.bot.embed.default(
            ctx, description=f'Invite me [here]({ctx.bot.config["links"]["invite_url"]})\n'
            f'Support server [here]({ctx.bot.config["links"]["support_url"]})'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check latency of the bot and its system."""
        s = perf_counter()
        msg = await ctx.send('Pinging...')
        e = perf_counter()
        elements = [
            ('<a:loading:787357834232332298> Websocket', f'{self.bot.latency * 1000:.2f}'),
            ('<a:typing:787357087843745792> Typing', f'{(e - s) * 1000:.2f}'),
            ('<:pg:795005204289421363> Database', f'{await self.bot.db_latency():.2f}')
        ]
        embed = self.bot.embed.default(ctx, description='\n'.join([f'**{n}:** ```{v} ms```' for n, v in elements]))
        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
