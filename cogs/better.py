# import logging
import discord
from discord.ext import commands
from utils.CustomCog import Cog

from utils.CustomBot import Bot
from utils.CustomEmbed import Embed
import prettify_exceptions
import typing


class ErrorHandler(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        # self.logger = utils.create_logger(
        #    self.__class__.__name__, logging.INFO)

    async def send_to_ctx_or_author(self, ctx, text: str = None, *args, **kwargs) -> typing.Optional[discord.Message]:
        try:
            return await ctx.reply(text, *args, **kwargs)
        except discord.Forbidden:
            try:
                return await ctx.author.send(text, *args, **kwargs)
            except discord.Forbidden:
                pass
        except discord.NotFound:
            pass
        return None

    async def send_error(self, ctx, error):
        error_log_channel = self.bot.get_channel(766571630268252180)
        embed = Embed.error(title="Something went wrong...", description=f"```py\nAn Error Occurred:\n{error}\n```")
        embed.set_author(
            name=f"{ctx.author} | {ctx.author.id}", icon_url=ctx.author.avatar_url
        )
        if ctx.guild:
            cmd = (
                "None"
                if isinstance(ctx.command, type(None))
                else ctx.command.qualified_name
            )
            embed.set_thumbnail(url=ctx.guild.icon_url_as(size=512))
            embed.add_field(
                name="Key Information:",
                value=f"Channel: {ctx.channel} {ctx.channel.id}\n"
                f"Guild: {ctx.guild} {ctx.guild.id}\n"
                f"Command: {cmd}\n"
                f"Message Content: {ctx.message.content}",
            )

        await error_log_channel.send(embed=embed)

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound)

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        setattr(ctx, "original_author_id", getattr(ctx, "original_author_id", ctx.author.id))
        owner_reinvoke_errors = (
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole,
            commands.CommandOnCooldown,
            commands.DisabledCommand,
        )

        if ctx.original_author_id in self.bot.owner_ids and isinstance(error, owner_reinvoke_errors):
            return await ctx.reinvoke()

        elif isinstance(error, commands.PartialEmojiConversionFailure):
            if ctx.command.name == "emoji":
                return

            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"{error}"), delete_after=5.0)

        elif isinstance(error, commands.CommandOnCooldown):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"This command is on cooldown. **`{int(error.retry_after)}` seconds**"), delete_after=5.0)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        elif isinstance(error, commands.MissingPermissions):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"You're missing the required permission: `{error.missing_perms[0]}`"))

        elif isinstance(error, commands.BadArgument):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"{error}"))

        elif isinstance(error, commands.BotMissingPermissions):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"I'm missing the required permission: `{error.missing_perms[0]}`"))

        elif isinstance(error, commands.NotOwner):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description="You must be the owner of the bot to run this."))

        elif isinstance(error, commands.RoleNotFound):
            return await self.send_to_ctx_or_author(ctx, embed=Embed.error(description=f"{error}"))

        prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
        tb = (
            ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))
        )

        if len(tb) > 1000:
            await ctx.send("The error message is too big so I sent it just to the developer.")
            await self.send_error(ctx, error)
        else:
            await self.send_to_ctx_or_author(ctx, embed=Embed.error(
                title="An error has occurred...",
                description=(
                    "Here's some details on it: ```py\n"
                    f"{tb}```"
                )
            ))
            await self.send_error(ctx, tb)

        raise error


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
