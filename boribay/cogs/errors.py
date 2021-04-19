from contextlib import suppress

import prettify_exceptions
from boribay.core import Boribay, Context
from boribay.utils import Cog, exceptions
from discord import Forbidden, NotFound
from discord.ext import commands, flags


class ErrorHandler(Cog):
    """The error-handling extension."""

    def __init__(self, bot: Boribay):
        self.bot = bot

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
        me: Boribay = ctx.bot
        channel = me.get_channel(me.config.main.errors_channel)
        embed = me.embed.error(description=f'```py\nError:\n{exc}\n```')
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
    async def on_command_error(self, ctx: Context, error):
        error = getattr(error, 'original', error)
        embed = ctx.bot.embed.error(title='⚠ Error!')

        if isinstance(error, commands.CommandNotFound):
            return

        setattr(ctx, 'original_author_id', getattr(ctx, 'original_author_id', ctx.author.id))
        invokes = (
            commands.MissingRole,
            commands.MissingAnyRole,
            commands.DisabledCommand,
            commands.CommandOnCooldown,
            commands.MissingPermissions
        )

        defaults = (
            exceptions.TooManyOptions,
            exceptions.NotEnoughOptions,
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
        )

        if isinstance(error, invokes) and ctx.original_author_id in ctx.bot.owner_ids:
            return await ctx.reinvoke()

        elif isinstance(error, defaults):
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
            await self.send(ctx, embed=ctx.bot.embed.error(description=f'Details: ```py\n{exc}\n```'))
            await self.send_error(ctx, exc)

        self.bot.log.error(error)


def setup(bot: Boribay):
    bot.add_cog(ErrorHandler(bot))
