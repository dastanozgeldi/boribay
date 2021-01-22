from typing import Optional

from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils.CustomCog import Cog
from utils.Paginators import MyPages, SQLListPageSource


class Owner(Cog, command_attrs={'hidden': True}):
    '''Nothing really to see here. But, if you are that interested,
    those are commands that help me to manage the bot while it's online
    without restarting it. The favorite module of the Owner btw.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '👑 Owner'

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(invoke_without_command=True)
    async def dev(self, ctx):
        """The parent command."""
        pass

    @dev.command()
    async def selfclear(self, ctx, amount: Optional[int] = 1):
        pass

    @dev.command()
    async def leave(self, ctx, guild_id: Optional[int]):
        """Leave command. Takes current guild if id was not given."""
        guild_id = guild_id or ctx.guild.id
        await self.bot.get_guild(guild_id).leave()

    @dev.command(aliases=['die'])
    async def shutdown(self, ctx):
        await ctx.message.add_reaction('👌')
        await self.bot.close()

    @dev.command()
    async def sql(self, ctx, *, query: codeblock_converter):
        """Does an SQL query."""
        query = query.content
        data = []
        for result in (await self.bot.pool.fetch(query) if query.lower().startswith('select') else await self.bot.pool.execute(query)):
            data.append(repr(result))
        await MyPages(SQLListPageSource(data)).start(ctx)

    @dev.command(aliases=['l'])
    async def load(self, ctx, *, module: str):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @dev.command(aliases=['u'])
    async def unload(self, ctx, *, module: str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @dev.command(aliases=['r'])
    async def reload(self, ctx, *, module: str):
        """Reloads a module."""
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('🔄')


def setup(bot):
    bot.add_cog(Owner(bot))
