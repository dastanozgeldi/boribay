from difflib import get_close_matches
from discord.ext import commands, menus
from utils.Cog import Cog
from utils.Paginators import MyPages


class HelpPages(menus.Menu):
    def __init__(self, embed, **kwargs):
        super().__init__(timeout=69.0, clear_reactions_after=True, **kwargs)
        self.embed = embed

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)

    @menus.button('<:left:814725888653918229>')
    async def go_back(self, payload):
        """Go back to the main page."""
        await self.message.edit(embed=self.embed)

    @menus.button('<:info:814725889031667722>')
    async def on_info(self, payload):
        """Shows this information page."""
        embed = self.bot.embed.default(self.ctx, title='Reactions Information')
        messages = [f'{emoji}: {button.action.__doc__}' for emoji, button in self.buttons.items()]
        embed.add_field(name='What are these reactions for?', value='\n'.join(messages))
        await self.message.edit(embed=embed)

    @menus.button('<:question:814725892215144458>')
    async def on_question(self, payload):
        """Shows how to use the bot."""
        embed = self.bot.embed.default(self.ctx, title='Welcome to the FAQ page.')
        fields = [
            ('How to use commands?', 'Follow the given signature for the command.'),
            ('What is <argument>?', 'This means the argument is **required**.'),
            ('What about [argument]?', 'This means the argument is **optional**.'),
            ('[argument...]?', 'This means there can be multiple arguments.'),
            ('What the hell is [--flag FLAG]?', f'This means the optional argument\nExample: **{self.ctx.prefix}todo show --dm True**')
        ]
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        await self.message.edit(embed=embed)

    @menus.button('<:crossmark:814742130190712842>')
    async def stop(self, payload):
        """Deletes this message."""
        await self.message.delete()


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
        doc = g.__doc__ if isinstance(g, Cog) else g.help
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
    def __init__(self):
        super().__init__(command_attrs={
            'hidden': True,
            'aliases': ['h'],
            'cooldown': commands.Cooldown(1, 5.0, commands.BucketType.user),
            'help': 'Shows help about modules, command groups or commands.'
        })

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

    def get_flags(self, command):
        return [f'**--{a.dest}** {a.help}' for a in command.callback._def_parser._actions if lambda x: '_OPTIONAL' not in a.dest]

    async def send_command_help(self, command):
        embed = self.context.bot.embed.default(
            self.context,
            title=self.get_command_signature(command),
            description=command.help or 'No help found...'
        ).set_footer(text=self.get_ending_note())
        if category := str(command.cog):
            embed.add_field(name='Category', value=category)
        if aliases := command.aliases:
            embed.add_field(name='Aliases', value=' | '.join(aliases))
        if hasattr(command.callback, '_def_parser'):
            embed.add_field(name='Flags', value='\n'.join(self.get_flags(command)), inline=False)
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
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
