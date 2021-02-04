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

    async def basic_cleanup(self, ctx, search):
        count = 0
        async for msg in ctx.history(limit=search, before=ctx.message):
            if msg.author == ctx.me:
                await msg.delete()
                count += 1
        return {str(self.bot.user): count}

    @commands.group()
    async def dev(self, ctx):
        """The parent command."""
        await ctx.message.add_reaction('✅')

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

    @dev.command()
    async def cleanup(self, ctx, search=1):
        """Cleans up the bot's messages from the channel."""
        spammers = await self.basic_cleanup(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{author}**: {count}' for author, count in spammers)

        await ctx.send('\n'.join(messages))


def setup(bot):
    bot.add_cog(Owner(bot))
