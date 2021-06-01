import asyncio
import os
import re
from collections import namedtuple
from datetime import datetime
from typing import Union

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from .cache import Cache
from .configuration import ConfigLoader
from .context import Context
from .database import DatabaseManager
from .events import set_events
from .logger import create_logger

__all__ = ('Boribay',)
logger = create_logger('bot')
Output = namedtuple('Output', 'stdout stderr returncode')


def get_prefix(bot, msg: discord.Message) -> str:
    prefix = '.' if not msg.guild else bot.guild_cache[msg.guild.id]['prefix']
    return commands.when_mentioned_or(prefix)(bot, msg)


async def is_blacklisted(ctx: Context) -> bool:
    user = ctx.user_cache[ctx.author.id]
    return not user.get('blacklisted', False)


async def is_beta(ctx: Context) -> bool:
    if ctx.config.main.beta and ctx.author.id not in ctx.bot.owner_ids:
        raise commands.CheckFailure('❌ The bot is currently in the maintenance mode.')

    return True


class Boribay(commands.Bot):
    """The main bot class - Boribay.

    This class inherits from `discord.ext.commands.Bot`.
    """

    def __init__(self, **kwargs):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(
            get_prefix,
            intents=intents,
            max_messages=1000,
            case_insensitive=True,
            chunk_guilds_at_startup=False,
            activity=discord.Game(name='.help'),
            member_cache_flags=discord.flags.MemberCacheFlags.from_intents(intents),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False),
            **kwargs
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.config = ConfigLoader('./data/config.toml')
        self.command_usage = 0
        self.start_time = datetime.now()
        self.owner_ids = {682950658671902730}
        self.loop = asyncio.get_event_loop()

        # Session-related.
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.webhook = discord.Webhook.from_url(
            self.config.links.log_url,
            adapter=discord.AsyncWebhookAdapter(self.session)
        )

        self.setup()

    async def __ainit__(self) -> None:
        """The asynchronous init method to prepare database with cache stuff.

        The main bot pool, guild-user cache, all are being instantiated here.

        Returns:
            None: Means that the method returns nothing.
        """
        self.pool = await asyncpg.create_pool(**self.config.database)
        self.db = DatabaseManager(self)

        self.guild_cache = await Cache('SELECT * FROM guild_config', 'guild_id', self.pool)
        self.user_cache = await Cache('SELECT * FROM users', 'user_id', self.pool)

        # await self.check_guilds()

    @property
    def dosek(self) -> discord.User:
        return self.get_user(682950658671902730)

    @property
    def uptime(self) -> int:
        return int((datetime.now() - self.start_time).total_seconds())

    @staticmethod
    async def shell(command: str):
        """The shell method made to ease up terminal manipulation
        for some bot commands, such as `git pull`.

        Parameters
        ----------
        command : str
            The command to put inside terminal, e.g `git add .`

        Returns
        -------
        namedtuple
            The output terminal returned us.
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

    async def on_message(self, message: discord.Message):
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

    async def close(self):
        await super().close()
        await self.session.close()

    def setup(self) -> None:
        """The important setup method to get already done in one place.

        Environment variables, bot checks and the database.

        Returns:
            None: Means that the method returns nothing.
        """
        # Setting Jishaku environment variables to work with.
        os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
        os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
        os.environ['JISHAKU_HIDE'] = 'True'

        # Checks to limit certain things.
        self.add_check(is_beta)
        self.add_check(is_blacklisted)

        # Putting the async init method into loop.
        self.loop.create_task(self.__ainit__())

    def list_extensions(self):
        """
        List all extensions of the bot's extensions directory.
        """
        # We should also avoid folders, like __pycache__.
        return [ext for ext in os.listdir('./boribay/extensions') if not ext.startswith('_')]

    def run(self, extensions: Union[list, set]):
        """An overridden run method to make the launcher file smaller.

        Args:
            extensions (Union[list, set]): Extensions (cogs) to get loaded.
        """
        for ext in extensions:
            # loading all extensions before running the bot.
            self.load_extension(ext)
            logger.info(f'[MODULE] {ext} loaded.')

        set_events(self)  # Setting up the events.

        # Finally, running the bot instance.
        super().run(self.config.main.token)

    async def check_guilds(self) -> dict:
        """Check for new guilds before start.

        This is needed when the bot gone offline for a while
        and got added/removed to some servers.

        Since the bot was offline they aren't accordingly existing
        in the database/cache making servers' users unable to use the bot.

        Returns:
            dict: The refreshed guild cache.
        """
        guild_config = await self.pool.fetch('SELECT * FROM guild_config;')

        # preparing the guild id's to compare
        bot_guild_ids = {guild.id for guild in self.guilds}
        db_guild_ids = {row['guild_id'] for row in guild_config}

        if difference := list(bot_guild_ids - db_guild_ids):  # check for new guilds.
            self.logger.info(f'New {len(difference)} guilds are being inserted.')
            for guild_id in difference:
                await self.pool.execute('INSERT INTO guild_config(guild_id) VALUES($1);', guild_id)

        if difference := list(db_guild_ids - bot_guild_ids):  # check for old guilds.
            logger.info(f'Old {len(difference)} guilds are being deleted.')
            for guild_id in difference:
                await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1;', guild_id)

        await self.guild_cache.refresh()
