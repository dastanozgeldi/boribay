import json
from contextlib import suppress
from io import BytesIO
from typing import TYPE_CHECKING

import discord
import prettify_exceptions
from boribay.utils import Manip, exceptions
from discord.ext import commands, flags

from .constants import PATH
from .logger import create_logger

if TYPE_CHECKING:
    from .bot import Boribay

__all__ = ('set_events',)

log = create_logger('events')
with open(f'{PATH}/rr.json', 'r') as f:
    local_reaction_roles = json.load(f)


def set_events(bot: 'Boribay'):
    """
    Initializing bot events required to live.
    """

    # Bot-related events.
    @bot.event
    async def on_ready():
        log.info(f'Logged in as -> {bot.user} | ID: {bot.user.id}')

    @bot.event
    async def on_message_edit(before, after):
        # making able to process commands on message edit only for owner.
        if before.content != after.content:
            if after.author.id in bot.owner_ids:
                return await bot.process_commands(after)

        # on_message_edit gets tracked twice when a message gets edited, god knows why.
        if before.embeds:
            return

    # Guild logging.
    async def _log_guild(guild: discord.Guild, **kwargs):
        """A general guild-logging method since both events are pretty similar.

        Args:
            guild (discord.Guild): The guild object produced by the event.
        """
        embed = bot.embed(
            title=kwargs.pop('text').format(guild),
            description=f'Member count: {guild.member_count}'
            f'Guild ID: {guild.id}\nNow in {len(bot.guilds)} guilds.',
            color=kwargs.pop('color')
        ).set_thumbnail(url=guild.icon_url)

        await bot.webhook.send(embed=embed)
        await bot.pool.execute(kwargs.pop('query'), guild.id)
        await bot.guild_cache.refresh()

    @bot.event
    async def on_guild_join(guild: discord.Guild):
        await _log_guild(guild, text='Joined a server: {}🎉', color=0x2ecc71,
                         query='INSERT INTO guild_config(guild_id) VALUES($1);')

    @bot.event
    async def on_guild_remove(guild: discord.Guild):
        await _log_guild(guild, text='Lost a server: {}💔', color=0xff0000,
                         query='DELETE FROM guild_config WHERE guild_id = $1;')

    @bot.event
    async def on_command_completion(ctx):
        author = ctx.author.id
        bot.command_usage += 1
        await bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

        if not await bot.pool.fetch('SELECT * FROM users WHERE user_id = $1', author):
            query = 'INSERT INTO users(user_id) VALUES($1)'
            await bot.pool.execute(query, author)
            await bot.user_cache.refresh()

    # Member-logging.
    @bot.event
    async def on_member_join(member: discord.Member):
        g = member.guild

        if wc := bot.guild_cache[g.id].get('welcome_channel', False):
            await g.get_channel(wc).send(file=discord.File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := bot.guild_cache[g.id].get('autorole', False):
            await member.add_roles(g.get_role(role_id), reason='Autorole')

    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if (m_id := str(payload.message_id)) in local_reaction_roles.keys():
            guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)
            for emoji, name in local_reaction_roles[m_id].items():
                if payload.emoji.name == emoji:
                    role = discord.utils.get(guild.roles, name=name)

            await payload.member.add_roles(role)

    @bot.event
    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        if (m_id := str(payload.message_id)) in local_reaction_roles.keys():
            guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)
            for emoji, name in local_reaction_roles[m_id].items():
                if payload.emoji.name == emoji:
                    role = discord.utils.get(guild.roles, name=name)

            with suppress(AttributeError):
                member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
                await member.remove_roles(role)

    # And finally, error handling.
    async def send(ctx, exc: str = None, *args, **kwargs):
        try:
            return await ctx.reply(exc, *args, **kwargs)

        except discord.Forbidden:
            with suppress(discord.Forbidden):
                return await ctx.author.send(exc, *args, **kwargs)

        except discord.NotFound:
            pass

        return None

    async def send_error(ctx, exc: str):
        me = ctx.bot
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

    @bot.event
    async def on_command_error(ctx, error: str):
        error = getattr(error, 'original', error)
        embed = ctx.embed(title='⚠ Error!', color=0xff0000)

        if isinstance(error, commands.CommandNotFound):
            return

        setattr(ctx, 'original_author_id', getattr(ctx, 'original_author_id', ctx.author.id))

        CUSTOM = (
            exceptions.DefaultError,
            exceptions.NotEnough,
            exceptions.PastMinimum,
            exceptions.NotAnInteger,
            exceptions.TooManyOptions,
            exceptions.NotEnoughOptions
        )

        if isinstance(
            error,
            (
                commands.MissingRole,
                commands.MissingAnyRole,
                commands.DisabledCommand,
                commands.CommandOnCooldown,
                commands.MissingPermissions
            )
        ) and ctx.original_author_id in ctx.bot.owner_ids:
            return await ctx.reinvoke()

        elif isinstance(
            error,
            (
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
        ):
            embed.description = str(error)
            return await send(ctx, embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        try:
            prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
            exc = ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))

        except AttributeError:
            return

        if len(exc) > 1000:
            await ctx.send('An error occured. Sending the traceback to the logging channel...')
            await send_error(ctx, error)

        else:
            embed = ctx.embed(description=f'Details: ```py\n{exc}\n```', color=0xff0000)
            await send(ctx, embed=embed)
            await send_error(ctx, exc)

        # log.error(error)
        # It's always better to get the original traceback instead of simple logging
        # that does not provide any details.
        raise error
