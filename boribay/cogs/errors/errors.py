from contextlib import suppress

import prettify_exceptions
from boribay.core import Boribay, Cog, Context, create_logger
from boribay.utils import exceptions
from discord import Forbidden, NotFound
from discord.ext import commands, flags


class ErrorHandler(Cog):
    """The error-handling extension."""

    def __init__(self, bot: Boribay):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

    async def send(self, ctx: Context, exc: str = None, *args, **kwargs):
        try:
            return await ctx.reply(exc, *args, **kwargs)

        except Forbidden:
            with suppress(Forbidden):
                return await ctx.author.send(exc, *args, **kwargs)

        except NotFound:
            pass

        return None

    async def send_error(self, ctx: Context, exc: str):
        me = self.bot
        channel = me.get_channel(me.config.main.errors_channel)
        embed = me.embed(ctx, description=f'```py\nError:\n{exc}\n```', color=0xff0000)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

        if ctx.guild:
            command = 'None' if not ctx.command else str(ctx.command)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(
                name='Information',
                value=f'Channel: {ctx.channel.mention}\n'
                f'Guild: {ctx.guild}\n'
                f'Command: {command}\n'
                f'Message: {ctx.message.content}'
            )

        await channel.send(embed=embed)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: str):
        error = getattr(error, 'original', error)
        embed = ctx.embed(title='⚠ Error!', color=0xff0000)

        if isinstance(error, commands.CommandNotFound):
            return

        setattr(ctx, 'original_author_id', getattr(ctx, 'original_author_id', ctx.author.id))
        INVOKES = (
            commands.MissingRole,
            commands.MissingAnyRole,
            commands.DisabledCommand,
            commands.CommandOnCooldown,
            commands.MissingPermissions
        )

        CUSTOM = (
            exceptions.DefaultError,
            exceptions.NotEnough,
            exceptions.PastMinimum,
            exceptions.NotAnInteger,
            exceptions.TooManyOptions,
            exceptions.NotEnoughOptions
        )

        DEFAULTS = (
            commands.NotOwner,
            commands.BadArgument,
            commands.RoleNotFound,
            commands.CheckFailure,
            commands.ExtensionError,
            commands.CommandOnCooldown,
            commands.NSFWChannelRequired,
            commands.MaxConcurrencyReached,
            flags._parser.ArgumentParsingError,
            commands.PartialEmojiConversionFailure,
            *CUSTOM
        )

        if isinstance(error, INVOKES) and ctx.original_author_id in ctx.bot.owner_ids:
            return await ctx.reinvoke()

        elif isinstance(error, DEFAULTS):
            embed.description = str(error)
            return await self.send(ctx, embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        try:
            prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
            exc = ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))

        except AttributeError:
            return

        if len(exc) > 1000:
            await ctx.send('An error occured. Sending the traceback to the logging channel...')
            await self.send_error(ctx, error)

        else:
            embed = ctx.embed(description=f'Details: ```py\n{exc}\n```', color=0xff0000)
            await self.send(ctx, embed=embed)
            await self.send_error(ctx, exc)

        # self.logger.error(error)
        # It's always better to get the original traceback instead of simple logging
        # that does not provide any details.
        raise error
