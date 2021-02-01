from typing import Optional

from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils.Cog import Cog
from utils.Formats import TabularData


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
    async def leave(self, ctx, guild_id: Optional[int]):
        """Leave command. Takes current guild if id was not given."""
        guild_id = guild_id or ctx.guild.id
        await self.bot.get_guild(guild_id).leave()

    @dev.command(aliases=['logout', 'close'])
    async def shutdown(self, ctx):
        await ctx.message.add_reaction('👌')
        await self.bot.close()

    @dev.command()
    async def sql(self, ctx, *, query: codeblock_converter):
        """Does an SQL query.
        Thanks again Danny for the output formatter!"""
        query = query.content
        async with ctx.timer:
            results = await self.bot.pool.fetch(query) if query.lower().startswith('select') else await self.bot.pool.execute(query)
            table = TabularData()
            table.set_columns(list(results[0].keys()))
            table.add_rows(list(r.values()) for r in results)
            await ctx.send(f'```py\n{table.render()}\n```')

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
