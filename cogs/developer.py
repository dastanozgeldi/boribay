import asyncio
import inspect
import os.path
from collections import namedtuple
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands, flags
from jishaku.codeblocks import codeblock_converter
from utils import Cog, TabularData

Output = namedtuple('Output', 'stdout stderr returncode')


class Owner(Cog, command_attrs={'hidden': True}):
    """Nothing really to see here. But, if you are that interested,
    those are commands that help me to manage the bot while it's online
    without restarting it. The favorite module of the Owner btw."""
    icon = '👑'
    name = 'Owner'

    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @staticmethod
    async def shell(command):
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return Output(stdout, stderr, str(process.returncode))

    @commands.command()
    async def nick(self, ctx, *, nick: str):
        """Nickname changing command. Just a quick tool for the owner nothing more."""
        await ctx.me.edit(nick=nick)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['ss'])
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["screenshot_api"]}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='screenshot.png'))

    @commands.group(invoke_without_command=True)
    async def maintenance(self, ctx):
        """Commands parent that control will bot respond other users.
        As you can see depends on the maintenance mode."""
        data = ctx.bot.cache['maintenance_mode']
        mode = 'enabled' if data else 'disabled'
        await ctx.send(f'Maintenance is {mode}.')

    @maintenance.command()
    async def enable(self, ctx):
        """Enabling command for maintenance mode."""
        await ctx.bot.pool.execute('UPDATE bot_stats SET maintenance_mode = true')
        await ctx.send('✅ Enabled maintenance mode.')
        ctx.bot.cache.update(maintenance_mode=True)

    @maintenance.command()
    async def disable(self, ctx):
        """Disabling command for maintenance mode."""
        await ctx.bot.pool.execute('UPDATE bot_stats SET maintenance_mode = false')
        await ctx.send('✅ Disabled maintenance mode.')
        ctx.bot.cache.update(maintenance_mode=False)

    @commands.command()
    async def blacklist(self, ctx, user: discord.Member, mode: bool = True):
        """Blacklists a user that makes user no longer able to use the bot."""
        query = f'UPDATE users SET blacklisted = {mode} WHERE user_id = $1'
        await ctx.bot.pool.execute(query, user.id)
        await ctx.message.add_reaction('✅')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    async def leave(self, ctx, guild_id: Optional[int]):
        """Leave command. Takes current guild if id was not given."""
        guild_id = guild_id or ctx.guild.id
        await ctx.bot.get_guild(guild_id).leave()
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['logout', 'close'])
    async def shutdown(self, ctx):
        """A shutdown command is just an alternative for CTRL-C in the terminal."""
        await ctx.message.add_reaction('👌')
        await ctx.bot.close()

    @commands.command()
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

        await ctx.send(f'```py\n{render}\n```')

    @commands.command(name='tableinfo')
    async def _table_info(self, ctx, table_name: str):
        """Represents some information about the given table."""
        q = '''SELECT column_name, data_type, column_default, is_nullable
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = $1'''
        results = await ctx.bot.pool.fetch(q, table_name)
        columns = list(results[0].keys())
        table = TabularData()
        table.set_columns(columns)
        table.add_rows(list(result.values()) for result in results)
        render = table.render()

        await ctx.send(f'```py\n{render}\n```')

    @commands.group(name='git', invoke_without_command=True)
    async def _git_commands(self, ctx):
        """A set of git command-line features to work with."""
        await ctx.send_help('git')

    @_git_commands.command(name='pull')
    async def _git_pull(self, ctx):
        """Pull changes from original source code on GitHub."""
        await self.shell('git pull')
        await ctx.send('✅ Pulled changes from GitHub.')

    @_git_commands.command(name='source', aliases=['src'])
    async def _git_source(self, ctx, *, command: Optional[str]):
        """Show source code for commands from the GitHub repo."""
        base = 'https://github.com/Dositan/Boribay'
        if not command:
            return await ctx.send(base)

        if not (cmd := ctx.bot.get_command(command.replace('.', ' '))):
            return await ctx.send(f'Could not find command `{cmd}`')

        source = cmd.callback.__code__
        filename = source.co_filename

        if command == 'help':
            source = type(ctx.bot.help_command)
            filename = inspect.getsourcefile(source)

        lines, firstlineno = inspect.getsourcelines(source)
        location = os.path.relpath(filename).replace('\\', '/')

        final_url = f'<{base}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

    @flags.add_flag(
        '--mode', choices=['r', 'l', 'u'], default='r',
        help='A specific mode [reload, load, unload].'
    )
    @flags.add_flag('ext', nargs="*")
    @commands.command(cls=flags.FlagCommand)
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
