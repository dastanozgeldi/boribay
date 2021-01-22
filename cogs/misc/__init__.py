from time import perf_counter
from utils.CustomCog import Cog
from discord.ext import commands


class Miscellaneous(Cog):
    '''Misc commands extension. Here owner inserts commands that aren't
    related to other categories, such as hello, ping etc.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '💫 Miscellaneous'

    @commands.command(aliases=['hi', 'hey'])
    async def hello(self, ctx):
        """Introduction"""
        await ctx.send(f'Hello there! I am **{self.bot.user}**, created by **{self.bot.dosek}**')

    @commands.command()
    async def prefix(self, ctx):
        """See bot's prefix."""
        if not ctx.guild:
            prefix = '.'
        else:
            prefix = await self.bot.pool.fetchval('SELECT prefix FROM guild_config WHERE guild_id = $1', ctx.guild.id)
        await ctx.send(embed=self.bot.embed(
            description=f'The prefix is: `{prefix}` or {self.bot.user.mention}'
        ))

    @commands.command(aliases=['links'])
    async def invite(self, ctx):
        """Some useful invites (support server and the bot itself)"""
        embed = self.bot.embed(
            description=f'To invite me to your server click [here]({self.bot.invite_url})\n'
            f'Invite to the support server is [here]({self.bot.support_url})'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check latency of the bot and its system."""
        s = perf_counter()
        msg = await ctx.send('Pinging...')
        e = perf_counter()
        embed = self.bot.embed()
        embed.add_field(name='<a:loading:787357834232332298> Websocket:', value=f'{self.bot.latency * 1000:.2f}ms')
        embed.add_field(name='<a:typing:787357087843745792> Typing:', value=f'{(e - s) * 1000:.2f}ms')
        embed.add_field(name='<:pg:795005204289421363> Database:', value=await self.bot.db_latency)
        await msg.edit(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
