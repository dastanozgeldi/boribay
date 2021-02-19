from difflib import get_close_matches
from discord.ext import commands, menus
from jishaku.features.python import PythonFeature
from utils.Cog import Cog
from utils.Paginators import MyPages, HelpPages


class GroupHelp(menus.ListPageSource):
    '''Sends help for group-commands.'''

    def __init__(self, ctx, group, cmds, prefix):
        super().__init__(entries=cmds, per_page=3)
        self.ctx = ctx
        self.group = group
        self.prefix = prefix
        self.description = '```fix\n<> ← required argument\n[] ← optional argument```'

    async def format_page(self, menu, cmds):
        g = self.group
        doc = g.__doc__ if isinstance(g, (Cog, PythonFeature)) else g.help
        embed = self.ctx.bot.embed.default(
            self.ctx,
            title=f'Help for category: {str(g)}',
            description=f'{doc}\n{self.description}'
        )
        for cmd in cmds:
            signature = f'{self.prefix}{cmd.qualified_name} {cmd.signature}'
            embed.add_field(name=signature, value=cmd.help.format(prefix=self.prefix), inline=False)
        if (maximum := self.get_max_pages()) > 1:
            embed.set_author(name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} commands)')
        embed.set_footer(text=f'{self.prefix}help <cmd> to get help for a specific command.')
        return embed


class MyHelpCommand(commands.HelpCommand):
    def get_ending_note(self):
        return f'Send {self.clean_prefix}{self.invoked_with} [Category] to get a category help.'

    async def send_bot_help(self, mapping):
        ctx = self.context
        links = ctx.bot.config['links']
        cats = []
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                if cog:
                    cats.append(str(cog))
        embed = ctx.bot.embed.default(
            ctx, description=f'[Invite]({links["invite_url"]}) | [Support]({links["support_url"]}) | [Source]({links["github_url"]}) | [Vote]({links["topgg_url"]})'
        ).set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url_as(size=64))
        embed.add_field(name='Modules:', value='\n'.join([m for m in cats]))
        news = open('news.md', 'r').readlines()
        embed.add_field(name=f'📰 News - {news[0]}', value=''.join(news[1:]))
        embed.set_footer(text=self.get_ending_note())
        await HelpPages(embed).start(ctx)

    async def send_cog_help(self, cog):
        ctx = self.context
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        await MyPages(
            GroupHelp(ctx, cog, entries, self.clean_prefix),
            timeout=30.0,
            clear_reactions_after=True
        ).start(ctx)

    async def send_command_help(self, command):
        embed = self.context.bot.embed.default(
            self.context,
            title=self.get_command_signature(command),
            description=command.help or 'No help found...'
        ).set_footer(text=self.get_ending_note())
        if aliases := command.aliases:
            embed.add_field(name='Aliases', value=' | '.join(aliases))
        if category := str(command.cog):
            embed.add_field(name='Category', value=category)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        if len(subcommands := group.commands) == 0 or len(cmds := await self.filter_commands(subcommands, sort=True)) == 0:
            return await self.send_command_help(group)
        await MyPages(GroupHelp(self.context, group, cmds, self.clean_prefix), timeout=30.0).start(self.context)

    async def command_not_found(self, string):
        msg = f'Could not find the command `{string}`.'
        if dym := '\n'.join(get_close_matches(string, [i.name for i in self.context.bot.commands])):
            msg += f' Did you mean...\n{dym}'
        return msg

    def get_command_signature(self, command):
        return f'{self.clean_prefix}{command.qualified_name} {command.signature}'


class Help(Cog):
    """Subclassed help command."""
    icon = '🆘'
    name = 'Help'

    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(command_attrs=dict(hidden=True, aliases=['h']))
        bot.help_command.cog = self

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
