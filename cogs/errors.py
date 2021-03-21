from contextlib import suppress

import prettify_exceptions
from discord import Forbidden, NotFound
from discord.ext import commands, flags
from utils import Cog, exceptions


class ErrorHandler(Cog, command_attrs={'hidden': True}):

    async def send(self, ctx, exc: str = None, *args, **kwargs):
        try:
            return await ctx.reply(exc, *args, **kwargs)

        except Forbidden:
            with suppress(Forbidden):
                return await ctx.author.send(exc, *args, **kwargs)

        except NotFound:
            pass

        return None

    async def send_error(self, ctx, exc):
        channel = ctx.bot.get_channel(ctx.bot.config['bot']['errors_channel'])
        embed = ctx.bot.embed.error(description=f'```py\nError:\n{exc}\n```')
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

        if ctx.guild:
            command = 'None' if isinstance(ctx.command, type(None)) else str(ctx.command)
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
    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        embed = ctx.bot.embed.error(title='⚠ Error!')

        if isinstance(error, commands.CommandNotFound):
            return

        setattr(ctx, 'original_author_id', getattr(ctx, 'original_author_id', ctx.author.id))
        invokes = (
            commands.MissingRole,
            commands.MissingAnyRole,
            commands.CommandOnCooldown,
            commands.MissingPermissions,
            commands.DisabledCommand
        )

        defaults = (
            KeyError,
            AssertionError,
            exceptions.TooManyOptions,
            exceptions.NotEnoughOptions,
            commands.NotOwner,
            commands.BadArgument,
            commands.RoleNotFound,
            commands.CheckFailure,
            commands.ExtensionError,
            commands.NSFWChannelRequired,
            commands.MaxConcurrencyReached,
            flags._parser.ArgumentParsingError,
            commands.PartialEmojiConversionFailure
        )

        if isinstance(error, invokes) and ctx.original_author_id in ctx.bot.owner_ids:
            return await ctx.reinvoke()

        elif isinstance(error, defaults):
            embed.description = str(error)
            return await self.send(ctx, embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f'This command is on cooldown. Retry after **{int(error.retry_after)} seconds**'
            return await self.send(ctx, embed=embed)

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

        raise error


def setup(bot):
    bot.add_cog(ErrorHandler())
