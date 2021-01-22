import discord
import prettify_exceptions
from typing import Optional
from utils import Exceptions
from utils.CustomCog import Cog
from discord.ext import commands


class ErrorHandler(Cog, command_attrs={'hidden': True}):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, exc: str = None, *args, **kwargs) -> Optional[discord.Message]:
        try:
            return await ctx.reply(exc, *args, **kwargs)
        except discord.Forbidden:
            try:
                return await ctx.author.send(exc, *args, **kwargs)
            except discord.Forbidden:
                pass
        except discord.NotFound:
            pass
        return None

    async def send_error(self, ctx, exc):
        channel = self.bot.get_channel(781874343868629073)
        embed = self.bot.embed.error(description=f'```py\nError:\n{exc}\n```')
        embed.set_author(name=f'{ctx.author}', icon_url=ctx.author.avatar_url)
        if ctx.guild:
            command = 'None' if isinstance(ctx.command, type(None)) else ctx.command.qualified_name
            embed.set_thumbnail(url=ctx.guild.icon_url_as(size=256))
            embed.add_field(
                name='Information',
                value=f'Channel: {ctx.channel.mention}\n'
                f'Guild: {ctx.guild}\n'
                f'Command: {command}\n'
                f'Message: {ctx.message.content}'
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignored = (commands.CommandNotFound)
        error = getattr(error, 'original', error)
        if isinstance(error, ignored):
            return
        setattr(ctx, 'original_author_id', getattr(ctx, 'original_author_id', ctx.author.id))
        invoke_errors = (commands.MissingRole, commands.MissingAnyRole, commands.CommandOnCooldown, commands.MissingPermissions, commands.DisabledCommand)

        if isinstance(error, invoke_errors) and ctx.original_author_id in self.bot.owner_ids:
            return await ctx.reinvoke()

        elif isinstance(error, IndexError):
            return await self.send(ctx, embed=self.bot.embed.error(description=str(error)))

        elif isinstance(error, KeyError):
            return await self.send(ctx, embed=self.bot.embed.error(decription=str(error)))

        elif isinstance(error, Exceptions.TooManyOptions):
            return await self.send(ctx, embed=self.bot.embed.error(description='There were too many options to create a poll.'))

        elif isinstance(error, Exceptions.NotEnoughOptions):
            return await self.send(ctx, embed=self.bot.embed.error(description='There were not enough options to create a poll.'))

        elif isinstance(error, commands.NSFWChannelRequired):
            return await self.send(ctx, embed=self.bot.embed.error(description=str(error)))

        elif isinstance(error, commands.MaxConcurrencyReached):
            return await self.send(ctx, embed=self.bot.embed.error(description=str(error)))

        elif isinstance(error, commands.PartialEmojiConversionFailure):
            if ctx.command.name == 'emoji':
                return
            return await self.send(ctx, embed=self.bot.embed.error(description=f'{error}'), delete_after=5.0)

        elif isinstance(error, commands.CommandOnCooldown):
            return await self.send(ctx, embed=self.bot.embed.error(description=f'This command is on cooldown. **`{int(error.retry_after)}` seconds**'), delete_after=10.0)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        elif isinstance(error, commands.MissingPermissions):
            return await self.send(ctx, embed=self.bot.embed.error(description=f'You are missing permission: `{error.missing_perms[0]}`'))

        elif isinstance(error, commands.BadArgument):
            return await self.send(ctx, embed=self.bot.embed.error(description=f'{error}'))

        elif isinstance(error, commands.BotMissingPermissions):
            return await self.send(ctx, embed=self.bot.embed.error(description=f'I am missing permission: `{error.missing_perms[0]}`'))

        elif isinstance(error, commands.NotOwner):
            return await self.send(ctx, embed=self.bot.embed.error(description='You must be the owner of the bot to run this.'))

        elif isinstance(error, commands.RoleNotFound):
            return await self.send(ctx, embed=self.bot.embed.error(description=f'{error}'))

        prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
        exc = ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))

        if len(exc) > 500:
            await ctx.send('Unexpected error occured. Gotta send the traceback to my owner.')
            await self.send_error(ctx, error)
        else:
            await self.send(ctx, embed=self.bot.embed.error(description=f'Details: ```py\n{exc}\n```'))
            await self.send_error(ctx, exc)

        raise error


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
