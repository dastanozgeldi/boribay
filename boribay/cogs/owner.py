import asyncio
import copy
import inspect
import io
import os.path
import textwrap
from collections import namedtuple
from contextlib import redirect_stdout
from io import BytesIO
from typing import Optional

import discord
from boribay.core import Context
from boribay.utils import Cog, TabularData
from discord.ext import commands, flags
from jishaku.codeblocks import codeblock_converter

Output = namedtuple('Output', 'stdout stderr returncode')


class Owner(Cog):
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
        r = await ctx.bot.session.get(f'{ctx.config.api.screenshot}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='screenshot.png'))

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx):
        """Blacklists parent command."""
        await ctx.send_help('blacklist')

    @blacklist.command(name='add')
    async def _blacklist_add(self, ctx, users: commands.Greedy[commands.MemberConverter]):
        """Blacklists a user that makes them no longer able to use the bot."""
        query = '''
        UPDATE users SET
        warns = 3,
        blacklisted = true
        WHERE user_id = $1
        '''
        for user in users:
            await ctx.bot.pool.execute(query, user.id)

        await ctx.send(f'✅ Successfully put **{", ".join(str(x) for x in users)}** into blacklist.')
        await ctx.bot.user_cache.refresh()

    @blacklist.command(name='remove')
    async def _blacklist_remove(self, ctx, users: commands.Greedy[commands.MemberConverter]):
        """Removes a user from blacklist that brings them back to use the bot."""
        query = '''
        UPDATE users SET
        warns = 0,
        blacklisted = false
        WHERE user_id = $1
        '''
        for user in users:
            await ctx.bot.pool.execute(query, user.id)

        await ctx.send(f'✅ Successfully removed **{", ".join(str(x) for x in users)}** from blacklist.')
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

    def grab_code(self, code):
        if code.startswith('```') and code.endswith('```'):
            return '\n'.join(code.split('\n')[1: -1])

        return code.strip('` \n')

    @commands.command(name='run')
    async def _run_code(self, ctx, *, code):
        """Evaluates a given code."""
        code = self.grab_code(code)

        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'msg': ctx.message,
            'chan': ctx.channel,
            'guild': ctx.guild,
            'author': ctx.author,
            'discord': discord,
            'commands': commands
        }

        with io.StringIO() as stdout:
            exec(f'async def func():\n{textwrap.indent(code, "  ")}', env, env)
            with redirect_stdout(stdout):
                result = await env['func']()

            if value := stdout.getvalue():
                return await ctx.send(value)

            if not result:
                return await ctx.message.add_reaction('✅')

            if isinstance(result, discord.File):
                return await ctx.send(file=result)

            elif isinstance(result, discord.Embed):
                return await ctx.send(embed=result)

            elif isinstance(result, (str, int)):
                return await ctx.send(result)

            else:
                return await ctx.send(repr(result))

    @commands.command()
    async def sql(self, ctx, *, query: codeblock_converter):
        """Does some nice SQL queries."""
        query = query.content

        ql = query.lower()
        if ql.startswith('select') or ql.startswith('with'):
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

        else:
            await ctx.send(results)

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

    @flags.add_flag('-r', '--reload', help='Whether to reload all extensions after pulling.')
    @_git_commands.command(cls=flags.FlagCommand, name='pull')
    async def _git_pull(self, ctx, **flags):
        """Pull changes from original source code on GitHub."""
        await self.shell('git pull')

        if flags.pop('reload'):
            cmd = ctx.bot.get_command('ext')
            await cmd(ctx, mode='r', ext=['~'])  # means to reload everything.

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
    @flags.command()
    async def ext(self, ctx, **flags):
        """Extensions manager."""
        modes = {
            'r': ctx.bot.reload_extension,
            'l': ctx.bot.load_extension,
            'u': ctx.bot.unload_extension,
        }
        exts = ctx.config.main.exts if flags['ext'][0] == '~' else flags['ext']

        for ext in exts:
            modes.get(flags['mode'])(ext)

        await ctx.message.add_reaction('✅')

    @commands.command(name='as')
    async def _run_as(self, ctx: Context, member: commands.MemberConverter, *, command: str):
        """Run a command from someone's POV."""
        message = copy.copy(ctx.message)
        message._update({'channel': ctx.channel, 'content': ctx.prefix + command})
        message.author = member
        new_context = await ctx.bot.get_context(message)
        await ctx.bot.invoke(new_context)

    @commands.group(invoke_without_command=True)
    async def refresh(self, ctx):
        """Refreshes the bot cache."""
        await ctx.send_help('refresh')

    @refresh.command(name='config')
    async def _refresh_config(self, ctx: Context):
        """Refresh the bot config which is stored in the config.toml file.

        Args:
            ctx (Context): Automatically passed context argument."""
        ctx.config.reload()
        await ctx.send('✅ Reloaded the configuration file values.')

    @flags.add_flag('--of', choices=['guilds', 'users', 'stats'], default='users')
    @flags.add_flag('--all', action='store_true', help='Whether to refresh all cache categories.')
    @refresh.command(cls=flags.FlagCommand, name='cache')
    async def _refresh_cache(self, ctx: Context, **flags):
        """Refresh the bot cache through this command.

        Args:
            ctx (Context): Automatically passed context argument.

        Raises:
            commands.BadArgument: If an invalid mode was given."""
        modes = {
            'guilds': ctx.bot.guild_cache,
            'users': ctx.bot.user_cache,
            'stats': ctx.bot.cache,  # Caching category that stores only 1 row.
        }

        if flags.pop('all'):
            for mode in modes.values():
                await mode.refresh()
                return await ctx.send('✅ Every caching category was refreshed.')

        mode = flags.pop('of')
        await modes[mode].refresh()
        await ctx.send(f'✅ Refreshed `{mode}` cache.')


def setup(bot):
    bot.add_cog(Owner())
