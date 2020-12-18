import discord
from discord.ext import commands
import traceback
import sys


class CommandErrorHandler(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error_embed = discord.Embed(title="⚠ | Error!", color=discord.Color.red())
        if hasattr(ctx.command, "on_error") and ctx.cog.qualified_name != 'Music':
            await ctx.send("Error occurred on doing this command.")

        cog = ctx.cog
        if cog and cog.qualified_name == 'Music':
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, )

        error = getattr(error, "original", error)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            error_embed.description = f'{ctx.command} has been disabled.'
            # await ctx.send(f'{ctx.command} has been disabled.')

        if isinstance(error, commands.errors.NSFWChannelRequired):
            error_embed.description = f'{error}'

        if isinstance(error, commands.errors.NotOwner):
            error_embed.description = f'Access denied to use command __{ctx.command}__'

        if isinstance(error, commands.CommandOnCooldown):
            error_embed.description = f'{ctx.author.display_name}, you are on cooldown. Try again in {round(error.retry_after, 2)}s.'

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                error_embed.description = f'{ctx.command} can not be used in Private Messages'
                # await ctx.author.send(f'{ctx.command} can not be used in Private Messages')
            except discord.HTTPException:
                pass

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        if isinstance(error, commands.BadArgument):
            error_embed.description = f"{error}"

        if isinstance(error, commands.MemberNotFound):
            error_embed.description = f"{error}"

        if isinstance(error, commands.MissingRequiredArgument):
            error_embed.description = f"This command is missing mandatory argument **{error.param.name}**. Type `{ctx.prefix}help {ctx.command}` to see where is the problem."
            # await ctx.send(f"This command is missing mandatory argument **{error.param.name}**. Type {ctx.prefix}help {ctx.command} to see where is the problem.")

        if isinstance(error, commands.CommandNotFound):
            error_embed.description = "I have no commands like that. Сheck the command for spelling errors, otherwise tell to the admins. To see commands list, type `.help`"
            # await ctx.send("I have no commands like that. Сheck the command for spelling errors, otherwise tell to the admins.")

        if isinstance(error, commands.MissingPermissions):
            error_embed.description = f"You have not permission: **{error.missing_perms[0]}** to use this command."
            # await ctx.send(f"You have not permission: __{error.missing_perms}__ to use this command.")

        if isinstance(error, commands.BotMissingPermissions):
            error_embed.description = f"I have not permission: **{error.missing_perms[0]}** to do that."
            # await ctx.send(f"I have not permission: __{error.missing_perms}__ to do that.")

        if isinstance(error, discord.Forbidden):
            error_embed.description = f"Missing permissions to do command **{ctx.prefix}{ctx.command}**\n```{error}```"

        if isinstance(error, IndexError):
            error_embed.description = f"This command has no elements in given number.\n```{error}```"

        if isinstance(error, commands.TooManyArguments):
            error_embed.description = f"Too many arguments for this command. Type {ctx.prefix}help {ctx.command} to learn how to use the command"
            # await ctx.send(f"Too many arguments for this command. Type {ctx.prefix}help {ctx.command} to learn how to use the command")
        await ctx.send(embed=error_embed)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
