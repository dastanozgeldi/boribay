import copy
import inspect
import os.path
from io import BytesIO, StringIO
from textwrap import indent
from typing import Optional

import discord
from boribay.core import utils
from discord.ext import commands, flags

from jishaku.codeblocks import codeblock_converter
from utils.Contextlib import redirect_stdout

from .formats import TabularData
from .utils import IdeaPageSource

__all__ = ('Developer',)


class Developer(utils.Cog):
    """The owner extension.

    Commands that help owner to manage the bot itself.

    No restarting needed using these commands.
    """

    icon = '👑'

    async def cog_check(self, ctx: utils.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    @commands.command()
    async def nick(self, ctx, *, nick: str) -> None:
        """Nickname changing quick tool.

        Example:
            **{p}nick [,] Boribay**

        Args:
            nick (str): A new nickname to set.
        """
        await ctx.me.edit(nick=nick)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=('ss',))
    async def screenshot(self, ctx, url: str) -> None:
        """Take a screenshot of the URL you give to the bot.

        Example:
            **{p}screenshot https://discord.com/**

        Args:
            url (str): A URL you want to get a screenshot from.
        """
        r = await ctx.bot.session.get('https://image.thum.io/get/width/1920/crop/675/maxAge/1/noanimate/' + url)
        file = discord.File(fp=BytesIO(await r.read()), filename='screenshot.png')
        await ctx.send(file=file)

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: utils.Context) -> None:
        """Blacklists parent command."""
        await ctx.send_help('blacklist')

    @blacklist.command(name='add')
    async def _blacklist_add(
        self, ctx: utils.Context, users: commands.Greedy[discord.Member]
    ) -> None:
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
        await ctx.user_cache.refresh()

    @blacklist.command(name='remove')
    async def _blacklist_remove(
        self, ctx: utils.Context, users: commands.Greedy[discord.Member]
    ) -> None:
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
        await ctx.user_cache.refresh()

    @commands.command()
    async def leave(self, ctx: utils.Context, guild: Optional[discord.Guild]) -> None:
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
            return await ctx.send(
                f'❌ Could not leave the guild: {guild} | {guild.id}'
            )

    @flags.add_flag(
        '-s',
        '--silently',
        action='store_true',
        help='Whether to logout silently.'
    )
    @flags.command()
    async def shutdown(self, ctx: utils.Context, **flags) -> None:
        """A shutdown command.

        This makes the bot close all its instances in order to log out from discord.
        """
        # The developer may not want the bot to send the last message before
        # shutting down, if they set this to False, the bot will close
        # its instances silently.
        if not flags.pop('silently'):
            await ctx.send('Shutting down... 👌')

        await ctx.bot.close()

    @staticmethod
    def grab_code(code: str) -> str:
        """Commonly, we use ```py to help ourselves seeing the code properly.

        This function is to grab the actual code and ignore this formatting.

        Args:
            code (str): A code to grab and filter.
        """
        if code.startswith('```') and code.endswith('```'):
            return '\n'.join(code.split('\n')[1: -1])

        return code.strip('` \n')

    @commands.command(name='run')
    async def _run_code(self, ctx: utils.Context, *, code: str) -> None:
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

        with StringIO() as stdout:
            exec(f'async def func():\n{indent(code, "  ")}', env, env)
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
    async def sql(self, ctx: utils.Context, *, query: codeblock_converter) -> None:
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
    async def _table_info(self, ctx: utils.Context, table_name: str) -> None:
        """Get some information about the given table.

        Example:
            **{p}tableinfo users**

        Args:
            table_name (str): A table name to get info from.
        """
        q = '''
        SELECT column_name, data_type, column_default, is_nullable
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = $1
        '''
        results = await ctx.bot.pool.fetch(q, table_name)
        columns = list(results[0].keys())
        table = TabularData()
        table.set_columns(columns)
        table.add_rows(list(result.values()) for result in results)
        render = table.render()

        await ctx.send(f'```py\n{render}\n```')

    @commands.group(name='git', invoke_without_command=True)
    async def _git_commands(self, ctx: utils.Context) -> None:
        """A set of git command-line features to work with."""
        await ctx.send_help('git')

    @flags.add_flag(
        '-r',
        '--reload',
        help='Whether to reload all extensions after pulling.'
    )
    @_git_commands.command(cls=flags.FlagCommand, name='pull')
    async def _git_pull(self, ctx, **flags) -> None:
        """Pull changes from original source code on GitHub."""
        await ctx.bot.shell('git pull')

        if flags.pop('reload'):
            cmd = ctx.bot.get_command('ext')
            await cmd(ctx, mode='r', ext=['~'])  # to reload everything.

        await ctx.send('✅ Pulled changes from GitHub.')

    @_git_commands.command(name='source', aliases=('src',))
    async def _git_source(self, ctx, *, command: Optional[str]) -> None:
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
        '--mode',
        choices=('r', 'l', 'u'),
        default='r',
        help='A specific mode [reload, load, unload].'
    )
    @flags.add_flag('ext', nargs="*")
    @flags.command()
    async def ext(self, ctx, **flags) -> None:
        """Extensions manager.

        Load, unload, reload the specified extensions.

        Example:
            **{p}ext ~** - reloads all extensions.
            **{p}ext boribay.extensions.fun** - reloads the "Fun" cog.
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
    async def _run_as(
        self, ctx: utils.Context, member: discord.Member, *, command: str
    ) -> None:
        """Execute commands as someone else.

        Example:
            **{p}as @Yerassyl ping** - runs the ping command as Yerassyl.

        Args:
            member (discord.Member): A member to get the utils.Context from.
            command (str): A command to execute.
        """
        message = copy.copy(ctx.message)
        message._update({'channel': ctx.channel, 'content': ctx.prefix + command})
        message.author = member

        new_utils.Context = await ctx.bot.get_utils.Context(message)
        await ctx.bot.invoke(new_utils.Context)

    @commands.group(invoke_without_command=True)
    async def refresh(self, ctx: utils.Context) -> None:
        """The refresh commands group."""
        await ctx.send_help('refresh')

    @refresh.command(name='config')
    async def _refresh_config(self, ctx: utils.Context) -> None:
        """Refresh the bot config which is stored in the config.toml file.

        Args:
            ctx (utils.Context): Automatically passed utils.Context argument.
        """
        ctx.config.reload()
        await ctx.send('✅ Reloaded the configuration file values.')

    @flags.add_flag(
        '--of',
        choices=('guilds', 'users', 'stats'),
        default='users'
    )
    @flags.add_flag(
        '--all',
        action='store_true',
        help='Whether to refresh all cache categories.'
    )
    @refresh.command(cls=flags.FlagCommand, name='cache')
    async def _refresh_cache(self, ctx: utils.Context, **flags) -> None:
        """Refresh the bot cache through this command.

        Args:
            ctx (utils.Context): Automatically passed utils.Context argument.

        Raises:
            commands.BadArgument: If an invalid mode was given.
        """
        modes = {'guilds': ctx.guild_cache, 'users': ctx.user_cache}
        if flags.pop('all'):
            for mode in modes.values():
                await mode.refresh()

            return await ctx.send('✅ Every caching category was refreshed.')

        mode = flags.pop('of')
        await modes[mode].refresh()
        await ctx.send(f'✅ Refreshed `{mode}` cache.')

    @commands.group(invoke_without_command=True)
    async def idea(self, ctx: utils.Context) -> None:
        await ctx.send_help('idea')

    async def _get_information(
        self, ctx: utils.Context, element_id: int, *, return_author: bool = False
    ) -> discord.Embed:
        try:
            data = dict(await ctx.bot.pool.fetchrow(
                'SELECT * FROM ideas WHERE id = $1', element_id
            ))
        except TypeError:
            await ctx.send(f'Suggestion with id ({element_id}) does not exist.')
            return

        author = await ctx.getch('user', data.pop('author_id'))
        embed = ctx.embed(
            title=f'Suggestion #{data.pop("id")}',
            description=data.pop('content')
        ).add_field(
            name='Additional Information',
            value='\n'.join(f'**{k.title()}**: {v}' for k, v in data.items())
        )

        if return_author:
            owner = ctx.bot.dosek
            embed.set_author(name=str(owner), icon_url=owner.avatar_url)
            return author, embed

        return embed

    @idea.command()
    @commands.is_owner()
    async def approve(self, ctx: utils.Context, suggestion_id: int) -> None:
        """Approve the suggestion by its ID.

        Example:
            **{p}idea approve 2**

        Args:
            suggestion_id (int): The ID of the suggestion.
            Multiple ID's may be specified.
        """
        query = 'UPDATE ideas SET approved = true WHERE id = $1;'
        await ctx.bot.pool.execute(query, suggestion_id)
        await ctx.message.add_reaction('✅')

        data = await self._get_information(ctx, suggestion_id, return_author=True)
        await data[0].send('🎉 Your suggestion got approved!', embed=data[1])

    @idea.command()
    @commands.is_owner()
    async def reject(self, ctx: utils.Context, suggestion_id: int) -> None:
        """Reject the suggestion by its ID.

        Example:
            **{p}idea reject 3**

        Args:
            suggestion_id (int): The ID of the suggestion.
            Multiple IDs may be specified.
        """
        data = await self._get_information(ctx, suggestion_id, return_author=True)
        await data[0].send('❌ Your suggestion got rejected.', embed=data[1])

        query = 'DELETE FROM ideas WHERE id = $1;'
        await ctx.bot.pool.execute(query, suggestion_id)
        await ctx.message.add_reaction('✅')

    @flags.add_flag(
        '--approved',
        action='store_true',
        help='Whether to list only approved suggestions.'
    )
    @flags.add_flag(
        '--limit',
        type=int,
        help='Set the limit of suggestions to get displayed.'
    )
    @idea.command(cls=flags.FlagCommand)
    @commands.is_owner()
    async def pending(self, ctx: utils.Context, **flags) -> None:
        """Check out all pending suggestions.

        Example:
            **{p}idea pending** - shows all unapproved suggestions.
            **{p}idea pending --approved** - shows only approved ideas.
            **{p}idea pending --limit 10** - shows last 10 added suggestions.
        """
        additional = 'true' if flags.pop('approved') else 'false'
        answers = {
            'true': 'There are no any approved ideas yet.',
            'false': 'Currently, there are no suggestions waiting to be approved.'
        }

        query = f'SELECT id, content, author_id FROM ideas WHERE approved is {additional};'
        if not (data := await ctx.bot.pool.fetch(query)):
            await ctx.send(answers[additional])
            return

        menu = utils.Paginate(source=IdeaPageSource(ctx, data))
        await menu.start(ctx)

    @idea.command()
    @commands.is_owner()
    async def info(self, ctx: utils.Context, suggestion_id: int) -> None:
        """Get some detailed information about the suggestion.

        Example:
            **{p}idea info 3** - sends the info about 3rd suggestion.

        Args:
            suggestion_id (int): The ID of the suggestion.
        """
        embed = await self._get_information(ctx, suggestion_id)
        await ctx.send(embed=embed)
