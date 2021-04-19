import asyncio
import logging
import re
from datetime import datetime
from time import perf_counter

import aiohttp
import asyncpg
import discord
from async_cse import Search
from boribay.utils import Cache, Embed
from dbl import DBLClient
from discord.ext import commands, ipc

from .config_loader import ConfigLoader
from .context import Context

__all__ = ('Boribay',)

LOGGERS = [('discord', logging.INFO), ('boribay', logging.INFO)]


# https://github.com/nickofolas/neo/blob/master/neo/core/__init__.py
# Thanks for this awesome way of logging!
class ColoredFormatter(logging.Formatter):
    prefix = '\x1b[38;5;'
    codes = {
        'INFO': f'{prefix}2m',
        'WARN': f'{prefix}100m',
        'DEBUG': f'{prefix}26m',
        'ERROR': f'{prefix}1m',
        'WARNING': f'{prefix}220m',
        '_RESET': '\x1b[0m',
    }

    def format(self, record: logging.LogRecord):
        if record.levelname in self.codes:
            record.msg = self.codes[record.levelname] + str(record.msg) + self.codes['_RESET']
            record.levelname = self.codes[record.levelname] + record.levelname + self.codes['_RESET']

        return super().format(record)


for name, level in LOGGERS:
    log_ = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(fmt='[%(asctime)s %(levelname)s: %(name)s] %(message)s')
    formatter.datefmt = '\x1b[38;2;132;206;255m' + '%d:%m:%Y %H:%M:%S' + formatter.codes['_RESET']
    handler.setFormatter(formatter)

    log_.setLevel(level)
    log_.addHandler(handler)


def get_prefix(bot, msg: discord.Message):
    prefix = '.' if not msg.guild else bot.guild_cache[msg.guild.id]['prefix']
    return commands.when_mentioned_or(prefix)(bot, msg)


class Boribay(commands.Bot):
    """A custom Bot class subclassed from commands.Bot"""
    intents = discord.Intents.default()
    intents.members = True

    def __init__(self, **kwargs):
        super().__init__(
            get_prefix,
            max_messages=1000,
            case_insensitive=True,
            chunk_guilds_at_startup=False,
            intents=self.intents,
            activity=discord.Game(name='.help'),
            member_cache_flags=discord.flags.MemberCacheFlags.from_intents(self.intents),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False),
            **kwargs
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.embed = Embed
        self.log = logging.getLogger(__name__)
        self.config = ConfigLoader('boribay/core/config.toml')
        self.command_usage = 0
        self.start_time = datetime.now()
        self.owner_ids = {682950658671902730}
        self.regex = {
            'RGB_REGEX': r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?',
            'EMOJI_REGEX': r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>',
            'URL_REGEX': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }

        # Loop-related
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.__ainit__())
        self.loop.create_task(self.check_changes())

        # Clients
        self.ipc = ipc.Server(self, **self.config.ipc)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.dblpy = DBLClient(self, self.config.main.dbl_token)
        self.cse = Search(self.config.api.google_key)

        # Checks
        self.add_check(self.is_on_beta)
        self.add_check(self.is_blacklisted)

    async def __ainit__(self):
        self.pool = await asyncpg.create_pool(**self.config.database)
        self.cache = dict(await self.pool.fetchrow('SELECT * FROM bot_stats'))
        self.guild_cache = await Cache('SELECT * FROM guild_config', 'guild_id', self.pool)
        self.user_cache = await Cache('SELECT * FROM users', 'user_id', self.pool)

    async def is_blacklisted(self, ctx: Context):
        if not (user := self.user_cache[ctx.author.id]):
            raise commands.CheckFailure(f'❌ You are blacklisted. DM {self.dosek} if you got any issues.')

        return not user.get('blacklisted', False)

    async def is_on_beta(self, ctx: Context):
        if self.config.main.beta and ctx.author.id not in self.owner_ids:
            raise commands.CheckFailure('❌ The bot is currently in the maintenance mode.')

        return True

    def run(self, extensions: set):
        """A custom run method to make the launcher file smaller."""
        for ext in extensions:
            # loading all extensions before running the bot.
            self.load_extension(ext)
            self.log.info(f'-> [MODULE] {ext} loaded.')

        super().run(self.config.main.token)

    @property
    def dosek(self):
        return self.get_user(682950658671902730)

    @property
    def uptime(self):
        return int((datetime.now() - self.start_time).total_seconds())

    async def on_message(self, message: discord.Message):
        if not self.is_ready():
            return

        # id below is the news channel from the support server.
        if message.channel.id == self.config.main.news_channel:
            with open('./boribay/core/news.md', 'w') as f:
                msg = message.content.split('\n')
                f.write(msg[0] + '\n' + '\n'.join(msg[1:]))

        # checking if a message was the clean mention of the bot.
        if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
            ctx = await self.get_context(message)
            await self.get_command('prefix')(ctx)

        await self.process_commands(message)

    async def check_changes(self):
        await self.wait_until_ready()

        guild_config = await self.pool.fetch('SELECT * FROM guild_config')

        # preparing the guild id's to compare
        bot_guild_ids = {guild.id for guild in self.guilds}
        db_guild_ids = {row['guild_id'] for row in guild_config}

        if difference := list(bot_guild_ids - db_guild_ids):  # check for new guilds.
            for guild_id in difference:
                await self.pool.execute('INSERT INTO guild_config(guild_id) VALUES($1)', guild_id)

        if difference := list(db_guild_ids - bot_guild_ids):  # check for old guilds.
            for guild_id in difference:
                await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild_id)

    async def db_latency(self):
        start = perf_counter()
        await self.pool.fetchval('SELECT 1;')
        end = perf_counter()

        return end - start

    async def close(self):
        await super().close()
        await self.cse.close()
        await self.dblpy.close()
        await self.session.close()

    async def get_context(self, message: discord.Message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def getch_user(self, user_id: int):
        try:
            return self.get_user(user_id) or await self.fetch_user(user_id)

        except discord.NotFound:
            return None
