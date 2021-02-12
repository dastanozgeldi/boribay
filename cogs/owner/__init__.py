from typing import Optional
from discord.ext import commands
from utils.Paginators import MyPages, SQLListPageSource
from jishaku.codeblocks import codeblock_converter
from utils.Cog import Cog


class Owner(Cog, command_attrs={'hidden': True}):
    '''Nothing really to see here. But, if you are that interested,
    those are commands that help me to manage the bot while it's online
    without restarting it. The favorite module of the Owner btw.'''
    icon = '👑'
    name = 'Owner'

    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group()
    async def dev(self, ctx):
        """The parent command."""
        await ctx.message.add_reaction('✅')

    @dev.command(aliases=['mrs'])  # move to rr/__init__.py
    async def messagereactionstats(self, ctx, message_link: str):
        """See what reactions are there in a message, shortly,
        message_reaction_stats."""
        ids = [int(i) for i in message_link.split('/')[5:]]
        msg = await ctx.guild.get_channel(ids[0]).fetch_message(ids[1])
        await ctx.send({f'{i}': i.count for i in msg.reactions})

    @dev.command()
    async def nick(self, ctx, *, nick: str):
        """Nickname changing command. Just a quick tool for the owner nothing more."""
        await ctx.me.edit(nick=nick)

    @dev.command()
    async def leave(self, ctx, guild_id: Optional[int]):
        """Leave command. Takes current guild if id was not given."""
        guild_id = guild_id or ctx.guild.id
        await self.bot.get_guild(guild_id).leave()

    @dev.command(aliases=['logout', 'close'])
    async def shutdown(self, ctx):
        """A shutdown command is just an alternative for CTRL-C in the terminal."""
        await self.bot.close()

    @dev.command()
    async def sql(self, ctx, *, query: codeblock_converter):
        """Does an SQL query."""
        query = query.content
        data = []
        for result in (await ctx.bot.pool.fetch(query) if query.lower().startswith('select') else await ctx.bot.pool.execute(query)):
            data.append(repr(result))
        await MyPages(SQLListPageSource(ctx, data)).start(ctx)

    @dev.command(aliases=['l'])
    async def load(self, ctx, *, module: str.lower):
        """Loads a module."""
        module = f'cogs.{module}' if module != 'jishaku' else module
        try:
            self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @dev.command(aliases=['u'])
    async def unload(self, ctx, *, module: str.lower):
        """Unloads a module."""
        module = f'cogs.{module}' if module != 'jishaku' else module
        try:
            self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @dev.command(aliases=['r'])
    async def reload(self, ctx, *, module: str.lower):
        """Reloads a module."""
        module = f'cogs.{module}' if module != 'jishaku' else module
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')


def setup(bot):
    bot.add_cog(Owner(bot))
