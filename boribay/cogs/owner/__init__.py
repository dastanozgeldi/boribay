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
from boribay.core import Cog, Context
from boribay.utils import TabularData
from discord.ext import commands, flags
from jishaku.codeblocks import codeblock_converter

Output = namedtuple('Output', 'stdout stderr returncode')


class Owner(Cog):
    """Nothing really to see here. But, if you are that interested,
    those are commands that help me to manage the bot while it's online
    without restarting it. The favorite module of the Owner btw."""
    icon = '👑'

    async def cog_check(self, ctx: Context):
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
        """Nickname changing quick tool.

        Example:
            **{p}nick [,] Boribay**

        Args:
            nick (str): A new nickname to set.
        """
        await ctx.me.edit(nick=nick)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['ss'])
    async def screenshot(self, ctx, url: str):
        """Take a screenshot of the URL you give to the bot.

        Example:
            **{p}screenshot https://discord.com/**

        Args:
            url (str): A URL you want to get a screenshot from.
        """
        r = await ctx.bot.session.get(f'{ctx.config.api.screenshot}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='screenshot.png'))

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: Context):
        """Blacklists parent command."""
        await ctx.send_help('blacklist')

    @blacklist.command(name='add')
    async def _blacklist_add(self, ctx: Context, users: commands.Greedy[discord.Member]):
        """Blacklist a user.

        This makes him/her no longer able to use the bot.

        Example:
            **{p}blacklist add @Dosek**

        Args:
            users (commands.Greedy[discord.Member]): Blacklist several users.
        """
        query = 'UPDATE users SET blacklisted = true WHERE user_id = $1'

        for user in users:
            await ctx.bot.pool.execute(query, user.id)

        await ctx.send(f'✅ Successfully put **{", ".join(str(x) for x in users)}** into blacklist.')
        await ctx.bot.user_cache.refresh()

    @blacklist.command(name='remove')
    async def _blacklist_remove(self, ctx: Context, users: commands.Greedy[discord.Member]):
        """Remove a user from blacklist.

        This brings him/her back the permissions to use the bot.

        Example:
            **{p}blacklist remove @Dosek**

        Args:
            users (commands.Greedy[discord.Member]): Unblacklist several users.
        """
        query = 'UPDATE users SET blacklisted = false WHERE user_id = $1'

        for user in users:
            await ctx.bot.pool.execute(query, user.id)

        await ctx.send(f'✅ Successfully removed **{", ".join(str(x) for x in users)}** from blacklist.')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    async def leave(self, ctx: Context, guild: Optional[discord.Guild]):
        """Make the bot leave a specific guild.

        This takes the current guild if ID was not given.

        Example:
            **{p}leave 789654321**

        Args:
            guild (Optional[discord.Guild]): A guild to leave.
        """
        guild = guild or ctx.guild

        try:
            await guild.leave()
            return await ctx.message.add_reaction('✅')

        except discord.HTTPException:
            return await ctx.send(f'❌ Could not leave the guild **{guild}**')

    @commands.command(aliases=['logout', 'close'])
    async def shutdown(self, ctx: Context):
        """A shutdown command.

        This makes the bot close all its instances in order to log out from discord.
        """
        await ctx.message.add_reaction('👌')
        await ctx.bot.close()

    def grab_code(self, code: str):
        """Commonly, we use ```py to help ourselves seeing the code properly.

        This function is to grab the actual code and ignore this formatting.

        Args:
            code (str): A code to grab and filter.
        """
        if code.startswith('```') and code.endswith('```'):
            return '\n'.join(code.split('\n')[1: -1])

        return code.strip('` \n')

    @commands.command(name='run')
    async def _run_code(self, ctx: Context, *, code: str):
        """Evaluate the given code.

        Has some useful globals to work with.

        Example:
            **{p}run return 'Hello World'**

        Args:
            code (str): The code that will be evaluated.
        """
        code = self.grab_code(code)

        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'discord': discord,
            'guild': ctx.guild,
            'commands': commands,
            'author': ctx.author,
            'message': ctx.message,
            'channel': ctx.channel
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
    async def sql(self, ctx: Context, *, query: codeblock_converter):
        """Do some SQL queries.

        Example:
            **{p}sql SELECT * FROM guild_config WHERE guild_id = 1234567**

        Args:
            query (codeblock_converter): A query to run in SQL.
        """
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
    async def _table_info(self, ctx: Context, table_name: str):
        """Get some information about the given table.

        Example:
            **{p}tableinfo users**

        Args:
            table_name (str): A table name to get info from.
        """
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
    async def _git_commands(self, ctx: Context):
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
        """Get source code for commands from the GitHub repo.

        Example:
            **{p}git source settings**

        Args:
            command (Optional[str]): A command to get the source of.
        """
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
        """Extensions manager.

        Load, unload, reload the specified extensions.

        Example:
            **{p}ext ~** - reloads all extensions.
            **{p}ext boribay.cogs.fun** - reloads the "Fun" cog.
        """
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
    async def _run_as(self, ctx: Context, member: discord.Member, *, command: str):
        """Execute commands as someone else.

        Example:
            **{p}as @Yerassyl ping** - runs the ping command as Yerassyl.

        Args:
            member (discord.Member): A member to get the context from.
            command (str): A command to execute.
        """
        message = copy.copy(ctx.message)
        message._update({'channel': ctx.channel, 'content': ctx.prefix + command})
        message.author = member

        new_context = await ctx.bot.get_context(message)
        await ctx.bot.invoke(new_context)

    @commands.group(invoke_without_command=True)
    async def refresh(self, ctx: Context):
        """Refreshes the bot cache."""
        await ctx.send_help('refresh')

    @refresh.command(name='config')
    async def _refresh_config(self, ctx: Context):
        """Refresh the bot config which is stored in the config.toml file.

        Args:
            ctx (Context): Automatically passed context argument.
        """
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
            commands.BadArgument: If an invalid mode was given.
        """
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
