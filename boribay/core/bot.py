from __future__ import annotations

import asyncio
import logging
import re
from collections import Counter, namedtuple
from datetime import datetime

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from .config import Config
from .database import Cache, DatabaseManager
from .events import set_events
from .utils import Context, is_beta, is_blacklisted

__all__ = ('Boribay',)

logger = logging.getLogger('bot')
Output = namedtuple('Output', 'stdout stderr returncode')


class Boribay(commands.Bot):
    """The main bot class - Boribay.

    This class inherits from `discord.ext.commands.Bot`.
    """

    def __init__(self, *, cli_flags, **kwargs):
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.cli = cli_flags
        self.counter = Counter()
        self.config = Config('./data/config/config.toml')

        self._launch_time = datetime.now()

        def get_prefix(bot: Boribay, msg: discord.Message) -> str:
            prefix = '.' if not msg.guild else bot.guild_cache[msg.guild.id]['prefix']
            return commands.when_mentioned_or(prefix)(bot, msg)

        intents = discord.Intents.default()
        intents.members = True
        super().__init__(
            command_prefix=get_prefix,
            description='A Discord Bot created to make people smile.',
            intents=intents,
            max_messages=1000,
            case_insensitive=True,
            owner_ids={682950658671902730},
            chunk_guilds_at_startup=False,
            activity=discord.Game(name='.help'),
            member_cache_flags=discord.flags.MemberCacheFlags.from_intents(intents),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=False
            ),
            **kwargs
        )

    @property
    def owner(self) -> discord.User:
        return self.get_user(682950658671902730)

    @property
    async def invite_url(self) -> str:
        app_info = await self.application_info()
        return discord.utils.oauth_url(app_info.id)

    @property
    def uptime(self) -> int:
        return int((datetime.now() - self._launch_time).total_seconds())

    @staticmethod
    async def shell(command: str):
        """The shell method made to ease up terminal manipulation
        for some bot commands, such as `git pull`.

        Parameters
        ----------
        command : str
            The command to put inside terminal, e.g `git add .`
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return Output(stdout, stderr, str(process.returncode))

    def embed(self, ctx: Context, **kwargs) -> discord.Embed:
        """The way to manipulate with Embeds.

        This method adds features like:
            • Timestamp
            • Custom color.

        Args:
            ctx (Context): To get current guild configuration.

        Returns:
            discord.Embed: Embed that already has useful features.
        """
        embed_color = 0x36393e if ctx.guild is None else self.guild_cache[ctx.guild.id]['embed_color']
        kwargs.update(timestamp=datetime.utcnow(), color=kwargs.pop('color', embed_color))
        return discord.Embed(**kwargs)

    async def on_message(self, message: discord.Message) -> None:
        if not self.is_ready():
            return

        # checking if a message was the clean mention of the bot.
        if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
            ctx = await self.get_context(message)
            await self.get_command('prefix')(ctx)

        await self.process_commands(message)

    async def get_context(
        self, message: discord.Message, *, cls=Context
    ) -> Context:
        """The same get_context but with the custom context class.

        Args:
            message (discord.Message): A message object to get the context from.
            cls (optional): The classmethod variable. Defaults to Context.

        Returns:
            Context: The context brought from the message.
        """
        return await super().get_context(message, cls=cls)

    async def close(self) -> None:
        await super().close()
        await self.session.close()

    async def setup(self):
        # Session-related.
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.webhook = discord.Webhook.from_url(
            self.config.links.log_url,
            adapter=discord.AsyncWebhookAdapter(self.session)
        )

        # Data-related.
        self.pool = await asyncpg.create_pool(**self.config.database)
        self.db = DatabaseManager(self)
        self.guild_cache = await Cache(
            'SELECT * FROM guild_config',
            'guild_id',
            self.pool
        )
        self.user_cache = await Cache(
            'SELECT * FROM users',
            'user_id',
            self.pool
        )

        # Checks to limit certain things.
        self.add_check(is_beta)
        self.add_check(is_blacklisted)

        # Initializer functions.
        set_events(self)

        # Check for flags.
        if self.cli.developer or self.config.main.beta:
            logger.info('Developer mode enabled.')
            self.load_extension('boribay.core.developer')

        if self.cli.no_cogs:
            logger.info('Booting up with no extensions loaded.')

        else:
            extensions = self.config.main.exts
            if (to_exclude := self.cli.exclude):
                extensions = set(extensions) - set(to_exclude)

            for ext in extensions:
                # loading all extensions before running the bot.
                self.load_extension(ext)

            logger.info('Loaded extensions: ' + ', '.join(self.cogs.keys()))

    async def start(self, *args, **kwargs) -> None:
        """An overridden run method to make the launcher file smaller."""
        # Getting the token.
        token = self.config.main.token
        if self.cli.token:
            logger.info(
                'Logging in without using the native token. Consider setting '
                'a token in the configuration file, i.e data/config.toml'
            )
            token = self.cli.token

        # Finally, booting up the bot instance.
        await self.setup()
        await super().start(token, *args, **kwargs)
