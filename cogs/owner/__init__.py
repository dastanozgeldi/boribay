import re
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands, flags
from jishaku.codeblocks import codeblock_converter
from utils.Cog import Cog
from utils.Formats import TabularData


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

    @commands.group(invoke_without_command=True)
    async def su(self, ctx):
        """The super-user commands parent."""

    @su.command()
    async def nick(self, ctx, *, nick: str):
        """Nickname changing command. Just a quick tool for the owner nothing more."""
        await ctx.me.edit(nick=nick)

    @su.command()
    async def clear(self, ctx, limit: int = 5):
        await ctx.channel.purge(limit=limit, bulk=False, check=lambda r: r.author == ctx.me)
        await ctx.send(f'Deleted {limit} messages.')

    @su.command(aliases=['ss'])
    @commands.is_nsfw()
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search(ctx.bot.regex['URL_REGEX'], url):
            raise commands.BadArgument('Invalid URL specified. Note that you should include http(s).')
        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["screenshot_api"]}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='screenshot.png'))

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
        """Does some nice SQL queries."""
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

    @flags.add_flag('--mode', choices=['r', 'l', 'u'], default='r', help='A specific mode [reload, load, unload].')
    @flags.add_flag('ext', nargs="*")
    @su.command(cls=flags.FlagCommand)
    async def ext(self, ctx, **flags):
        """Extensions manager."""
        modes = {
            'r': ctx.bot.reload_extension,
            'l': ctx.bot.load_extension,
            'u': ctx.bot.unload_extension,
        }
        exts = ctx.bot.config['bot']['exts'] if flags['ext'][0] == '~' else flags['ext']
        for ext in exts:
            modes.get(flags['mode'])(ext)
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Owner())
