from discord import Forbidden
from utils.Cog import Cog
from time import perf_counter
from discord.ext import commands


class Miscellaneous(Cog):
    '''Misc commands extension. Here owner inserts commands that aren't
    related to other categories, such as hello, ping etc.'''
    icon = '💫'
    name = 'Miscellaneous'

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    @commands.command()
    async def say(self, ctx, *, message: str):
        """Make the bot say what you want.
        Args: message: A message that will be sent."""
        try:
            await ctx.message.delete()
        except Forbidden:
            pass
        await ctx.send(message)

    @commands.command()
    async def prefix(self, ctx):
        """See bot's prefix."""
        prefix = '.' if not ctx.guild else ctx.bot.cache['prefix'][ctx.guild.id]
        await ctx.send(embed=ctx.bot.embed.default(ctx, description=f'The prefix is: `{prefix}` or {ctx.bot.user.mention}'))

    @commands.command(aliases=['links'])
    async def invite(self, ctx):
        """Some useful invites (support server and the bot itself)"""
        embed = ctx.bot.embed.default(
            ctx, description=f'Invite me [here]({ctx.bot.config["links"]["invite_url"]})\n'
            f'Support server [here]({ctx.bot.config["links"]["support_url"]})'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check latency of the bot and its system."""
        s = perf_counter()
        msg = await ctx.send('Pong!')
        e = perf_counter()
        elements = [
            ('<a:loading:787357834232332298> Websocket', f'{ctx.bot.latency * 1000:.2f}'),
            ('<a:typing:807306107508359228> Typing', f'{(e - s) * 1000:.2f}'),
            ('<:pg:795005204289421363> Database', f'{await ctx.bot.db_latency() * 1000:.2f}')
        ]
        embed = ctx.bot.embed.default(ctx, description='\n'.join([f'**{n}:** ```{v} ms```' for n, v in elements]))
        await msg.edit(embed=embed)

    @commands.command(aliases=['mrs'])
    async def messagereactionstats(self, ctx, message_link: str):
        """See what reactions are there in a message, shortly,
        message_reaction_stats."""
        ids = [int(i) for i in message_link.split('/')[5:]]
        msg = await ctx.guild.get_channel(ids[0]).fetch_message(ids[1])
        await ctx.send({f'{i}': i.count for i in msg.reactions})


def setup(bot):
    bot.add_cog(Miscellaneous())
