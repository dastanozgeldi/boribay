from difflib import get_close_matches
from typing import List, Union

import discord
from discord.ext import commands, menus

from boribay.core import utils
from boribay.core.bot import Boribay

__all__ = ("HelpCommand", "Help")


class HelpMenu(menus.Menu):
    """The main help menu of the bot."""

    def __init__(self, **kwargs):
        self.embed: discord.Embed = kwargs.pop("embed")
        super().__init__(timeout=60.0, clear_reactions_after=True, **kwargs)

    async def send_initial_message(
        self, ctx: utils.Context, channel: discord.abc.Messageable
    ) -> discord.Message:
        """Sends the initial message for the help-menu.

        Parameters
        ------------
        ctx: :class:`utils.Context`
            The invocation context to use.
        channel: :class:`discord.abc.Messageable`
            The messageable to send the message to.

        Returns
        --------
        :class:`discord.Message`
            The message that has been sent initially.
        """
        return await channel.send(embed=self.embed)

    @menus.button("<:backward:814725888892731443>")
    async def go_back(self, payload):
        """Go back to the main page."""
        await self.message.edit(embed=self.embed)

    @menus.button("<:info:814725889031667722>")
    async def on_info(self, payload):
        """Shows this information page."""
        embed = self.ctx.embed(title="Reactions Information")
        embed.add_field(
            name="What are these reactions for?",
            # Will look like "✅: blablabla".
            value="\n".join(
                f"{e}: {b.action.__doc__}" for e, b in self.buttons.items()
            ),
        )
        await self.message.edit(embed=embed)

    @menus.button("<:question:814725892215144458>")
    async def on_question(self, payload):
        """Shows how to use the bot."""
        embed = self.ctx.embed(title="Welcome to the FAQ page.")

        fields = [
            ("How to use commands?", "Follow the given signature for the command."),
            ("What is <argument>?", "This means the argument is **required**."),
            ("What about [argument]?", "This means the argument is **optional**."),
            ("[argument...]?", "This means there can be multiple arguments."),
            (
                "What the hell is [--flag FLAG]?",
                "This means the optional flag\nExample: **todo show --dm**",
            ),
        ]
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        await self.message.edit(embed=embed)

    @menus.button("<:crossmark:814742130190712842>")
    async def destroy_menu(self, payload):
        """Deletes this message."""
        # This differs a little bit from `self.stop`, while stopping clears up
        # all reactions, this method exactly deletes the menu.
        await self.message.delete()


class GroupHelp(menus.ListPageSource):
    """Sends help for group-commands."""

    def __init__(
        self,
        ctx: utils.Context,
        group: Union[commands.Cog, commands.Group],
        cmds: List[commands.Command],
        prefix: str,
    ):
        super().__init__(entries=cmds, per_page=3)
        self.ctx = ctx
        self.group = group
        self.prefix = prefix
        self.description = "```fix\n<> ← required argument\n[] ← optional argument```"

    async def format_page(self, menu: menus.Menu, cmds) -> discord.Embed:
        g = self.group

        if isinstance(g, commands.Cog):
            doc = g.__doc__
        else:
            doc = (g.help or "Help not provided.").split("\n")[0]

        embed = self.ctx.embed(
            title=f"Help for category: {g}", description=doc + self.description
        )

        for cmd in cmds:
            cmd_help = cmd.help or "Help not found."
            embed.add_field(
                name=f"{self.prefix}{cmd} {cmd.signature}",
                value=cmd_help.split("\n")[0] + "..",
                inline=False,
            )

        if (maximum := self.get_max_pages()) > 1:
            embed.set_author(
                name=f"Page {menu.current_page + 1} of {maximum} ({len(self.entries)} commands)"
            )

        embed.set_footer(
            text=f"{self.prefix}help <cmd> to get detailed help for a command."
        )
        return embed


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                "hidden": True,
                "aliases": ["h"],
                "help": "Shows help about modules, command groups or commands.",
            }
        )

    def get_ending_note(self):
        ctx = self.context
        return f"Send {ctx.clean_prefix}{self.invoked_with} [Category] to get a category help."

    async def send_bot_help(self, mapping):
        ctx = self.context
        cats = []
        for cog, cmds in mapping.items():
            if cog:
                if await self.filter_commands(cmds, sort=True):
                    cats.append(str(cog))

        embed = ctx.embed().set_author(
            name=str(ctx.author), icon_url=ctx.author.avatar
        )
        embed.add_field(name="Plugins:", value="\n".join(cats))
        await HelpMenu(embed=embed).start(ctx)

    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        entries = await self.filter_commands(cog.get_commands(), sort=True)

        await utils.Paginate(
            GroupHelp(ctx, cog, entries, ctx.clean_prefix),
            timeout=30.0,
            clear_reactions_after=True,
        ).start(ctx)

    async def send_command_help(self, command: commands.Command):
        ctx = self.context
        description = command.help or "Help not found."

        embed = ctx.embed(
            title=self.get_command_signature(command),
            description=description.format(p=ctx.clean_prefix),
        ).set_footer(text=self.get_ending_note())

        if category := str(command.cog):
            embed.add_field(name="Category", value=category)

        if aliases := command.aliases:
            embed.add_field(name="Aliases", value=" | ".join(aliases))

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        ctx = self.context
        subcommands = group.commands
        cmds = await self.filter_commands(subcommands, sort=True)
        if 0 in (len(subcommands), len(cmds)):
            return await self.send_command_help(group)

        await utils.Paginate(
            GroupHelp(ctx, group, cmds, ctx.clean_prefix), timeout=30.0
        ).start(ctx)

    async def command_not_found(self, string: str):
        ctx = self.context
        message = f"Could not find the command `{string}`. "
        commands_list = [str(cmd) for cmd in ctx.bot.walk_commands()]

        if dym := "\n".join(get_close_matches(string, commands_list)):
            message += f"Did you mean...\n{dym}"

        return message

    def get_command_signature(self, command: commands.Command):
        ctx = self.context
        return f"{ctx.clean_prefix}{command} {command.signature}"


class Help(utils.Cog):
    """The help command extension."""

    def __init__(self, bot: Boribay):
        self.icon = "🆘"
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command
