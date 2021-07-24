import logging
from contextlib import suppress
from io import BytesIO

import boribay
import discord
from boribay.core import exceptions, utils
from discord.ext import commands
from rich import box, get_console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

__all__ = ('set_events',)

logger = logging.getLogger('bot')

start_screen = r'''
 ____             _  _
| __ )  ___  _ __(_)| |__   __ _ _   _
|  _ \ / _ \| '__| || '_ \ / _` | | | |
| |_) | (_) | |  | || |_) | (_| | |_| |
|____/ \___/|_|  |_||_.__/ \__,_ \__, |
                                 |___/
            by Dositan
'''


def set_events(bot):
    """Initializing bot events required to live."""

    # Bot-related events.
    @bot.event
    async def on_connect():
        logger.info('Connected to Discord successfully.')

    @bot.event
    async def on_ready():
        """The bot is ready, telling the developer."""
        guilds = len(bot.guilds)
        general_info = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        general_info.add_row('Boribay version', boribay.__version__)
        general_info.add_row('Library version', discord.__version__)

        counts = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        counts.add_row('Servers', str(guilds))
        if bot.intents.members:  # Avoiding 0 users
            users = len(set(bot.get_all_members()))
            counts.add_row('Cached Users', str(users))

        console = get_console()
        console.print(start_screen, style='blue', markup=False, highlight=False)
        if guilds:
            console.print(
                Columns(
                    [
                        Panel(general_info, title=str(bot.user.name)),
                        Panel(counts)
                    ],
                    equal=True,
                    align='center',
                )
            )
        else:
            console.print(Columns([Panel(general_info, title=str(bot.user.name))]))

        console.print(f'Loaded {len(bot.cogs)} cogs with {len(bot.commands)} commands')
        console.print(f'Client latency: {bot.latency * 1000:.2f} ms')

    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
        # making able to process commands on message edit only for owner.
        if before.content != after.content and after.author.id in bot.owner_ids:
            return await bot.process_commands(after)

        # on_message_edit gets tracked twice when a message gets edited, god knows why.
        if before.embeds:
            return

    # Guild logging.
    @bot.event
    async def on_guild_join(guild: discord.Guild) -> None:
        """Gets triggered whenever the bot joins a guild.

        Parameters
        ----------
        guild : discord.Guild
            The new guild.
        """
        embed = bot.embed(
            title=f'Joined a server: {guild}🎉',
            description=f'Member count: {guild.member_count}'
            f'Guild ID: {guild.id}'
            f'Now in {len(bot.guilds)} guilds.',
            color=0x2ecc71
        ).set_thumbnail(url=guild.icon_url)

        await bot.webhook.send(embed=embed)
        await bot.pool.execute(
            'INSERT INTO guild_config(guild_id) VALUES($1);',
            guild.id
        )
        await bot.guild_cache.refresh()

    @bot.event
    async def on_guild_remove(guild: discord.Guild) -> None:
        """Gets triggered whenever the bot loses a guild.

        Parameters
        ----------
        guild : discord.Guild
            The lost guild.
        """
        embed = bot.embed(
            title=f'Lost a server: {guild}💔',
            description=f'Member count: {guild.member_count}'
            f'Guild ID: {guild.id}'
            f'Now in {len(bot.guilds)} guilds.',
            color=0xff0000
        ).set_thumbnail(url=guild.icon_url)

        await bot.webhook.send(embed=embed)
        await bot.pool.execute(
            'DELETE FROM guild_config WHERE guild_id = $1;',
            guild.id
        )
        await bot.guild_cache.refresh()

    @bot.event
    async def on_command_completion(ctx) -> None:
        """Gets triggered everytime a bot command was successfully executed.

        Parameters
        ----------
        ctx : Context
            The custom context object.
        """
        bot.counter['command_usage'] += 1
        await bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    # Member-logging.
    @bot.event
    async def on_member_join(member: discord.Member) -> None:
        g: discord.Guild = member.guild
        # Member-logging feature.
        if wc := bot.guild_cache[g.id].get('welcome_channel', False):
            image = await utils.Manip.welcome(
                top_text=f'Member #{g.member_count}',
                bottom_text=f'{member} just spawned in the server.',
                member_avatar=BytesIO(await member.avatar_url.read())
            )
            channel = g.get_channel(wc)
            file = discord.File(image, f'{member}.png')
            await channel.send(file=file)

        # Autorole feature may get triggered according to the guild settings.
        if role_id := bot.guild_cache[g.id].get('autorole', False):
            await member.add_roles(g.get_role(role_id), reason='Autorole')

    # And finally, error handling.
    async def send(ctx, exc: str = None, *args, **kwargs) -> None:
        try:
            return await ctx.reply(exc, *args, **kwargs)

        except discord.Forbidden:
            with suppress(discord.Forbidden):
                return await ctx.author.send(exc, *args, **kwargs)

        except discord.NotFound:
            pass

    @bot.event
    async def on_command_error(ctx, error: str) -> None:
        error = getattr(error, 'original', error)
        embed = ctx.embed(title='⚠ Error!', color=0xff0000)

        if isinstance(error, commands.CommandNotFound):
            return

        original_author = getattr(ctx, 'original_author_id', ctx.author.id)
        setattr(ctx, 'original_author_id', original_author)

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
            # Those errors need to be reinvoked.
            return await ctx.reinvoke()

        elif isinstance(
            error,
            (
                # discord-py.
                commands.NotOwner,
                commands.BadArgument,
                commands.RoleNotFound,
                commands.CheckFailure,
                commands.ExtensionError,
                commands.CommandOnCooldown,
                commands.NSFWChannelRequired,
                commands.MaxConcurrencyReached,
                commands.PartialEmojiConversionFailure,
                exceptions.UserError
            )
        ):
            embed.description = str(error)
            return await send(ctx, embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send_help(ctx.command)

        else:
            logger.exception(type(error).__name__, exc_info=error)
