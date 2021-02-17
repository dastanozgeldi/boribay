from typing import Optional
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils.Cog import Cog


class Owner(Cog, command_attrs={'hidden': True}):
    '''Nothing really to see here. But, if you are that interested,
    those are commands that help me to manage the bot while it's online
    without restarting it. The favorite module of the Owner btw.'''
    icon = '👑'
    name = 'Owner'

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.group()
    async def su(self, ctx):
        """The parent command."""
        await ctx.message.add_reaction('✅')

    @su.command()
    async def nick(self, ctx, *, nick: str):
        """Nickname changing command. Just a quick tool for the owner nothing more."""
        await ctx.me.edit(nick=nick)

    @su.command()
    async def leave(self, ctx, guild_id: Optional[int]):
        """Leave command. Takes current guild if id was not given."""
        guild_id = guild_id or ctx.guild.id
        await ctx.bot.get_guild(guild_id).leave()

    @su.command(aliases=['logout', 'close'])
    async def shutdown(self, ctx):
        """A shutdown command is just an alternative for CTRL-C in the terminal."""
        await ctx.bot.close()

    @su.command()
    async def sql(self, ctx, *, query: codeblock_converter):
        from utils.Formats import TabularData
        query = query.content
        if query.lower().startswith('select'):
            strategy = ctx.bot.pool.fetch
        else:
            strategy = ctx.bot.pool.execute
        results = await strategy(query)
        if isinstance(results, list):
            columns = list(results[0].keys())
            table = TabularData()
            table.set_columns(columns)
            table.add_rows(list(result.values()) for result in results)
            render = table.render()
            msg = f'```py\n{render}\n```'
        else:
            msg = results
        await ctx.send(msg)

    @su.command(aliases=['l'])
    async def load(self, ctx, *, module: str.lower):
        """Loads a module."""
        ctx.bot.load_extension(f'cogs.{module}' if module != 'jishaku' else module)

    @su.command(aliases=['u'])
    async def unload(self, ctx, *, module: str.lower):
        """Unloads a module."""
        ctx.bot.unload_extension(f'cogs.{module}' if module != 'jishaku' else module)

    @su.command(aliases=['r'])
    async def reload(self, ctx, *, module: str.lower):
        """Reloads a module."""
        ctx.bot.reload_extension(f'cogs.{module}' if module != 'jishaku' else module)


def setup(bot):
    bot.add_cog(Owner())
