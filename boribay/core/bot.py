import asyncio
import os
import re
from datetime import datetime
from typing import NoReturn, Union

import aiohttp
import asyncpg
import discord
from dbl import DBLClient
from discord.ext import commands

from .cache import Cache
from .configuration import ConfigLoader
from .context import Context
from .database import DatabaseManager
from .logger import create_logger

__all__ = ('Boribay',)
logger = create_logger('Bot')


def get_prefix(bot, msg: discord.Message) -> str:
    prefix = '.' if not msg.guild else bot.guild_cache[msg.guild.id]['prefix']
    return commands.when_mentioned_or(prefix)(bot, msg)


async def is_blacklisted(ctx: Context) -> bool:
    if not (user := ctx.user_cache[ctx.author.id]):
        raise commands.CheckFailure(f'❌ You are blacklisted. DM {ctx.bot.dosek} if you got any issues.')

    return not user.get('blacklisted', False)


async def is_beta(ctx: Context) -> bool:
    if ctx.config.main.beta and ctx.author.id not in ctx.bot.owner_ids:
        raise commands.CheckFailure('❌ The bot is currently in the maintenance mode.')

    return True


class Boribay(commands.Bot):
    """A custom Bot class subclassed from commands.Bot"""

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
        self.config = ConfigLoader('boribay/data/main/config.toml')
        self.command_usage = 0
        self.start_time = datetime.now()
        self.owner_ids = {682950658671902730}
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.dblpy = DBLClient(self, self.config.main.dbl_token)
        self.setup()

    @property
    def dosek(self) -> discord.User:
        return self.get_user(682950658671902730)

    @property
    def uptime(self) -> int:
        return int((datetime.now() - self.start_time).total_seconds())

    def embed(self, ctx: Context, **kwargs):
        """The way to manipulate with Embeds.

        This method adds features like:
            • Timestamp
            • Custom color.

        Args:
            ctx (Context): To get current guild configuration.

        Returns:
            discord.Embed: Embed that already has useful features.
        """
        embed_color = self.guild_cache[ctx.guild.id]['embed_color']

        kwargs.update(timestamp=datetime.utcnow(),
                      color=kwargs.pop('color', embed_color))

        return discord.Embed(**kwargs)

    async def on_message(self, message: discord.Message):
        if not self.is_ready():
            return

        # id below is the news channel from the support server.
        if message.channel.id == self.config.main.news_channel:
            with open('./boribay/data/main/detailed_news.md', 'w') as f:
                f.write(message.content)

        # checking if a message was the clean mention of the bot.
        if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
            ctx = await self.get_context(message)
            await self.get_command('prefix')(ctx)

        await self.process_commands(message)

    async def get_context(self, message: discord.Message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def close(self):
        await super().close()
        await self.dblpy.close()
        await self.session.close()

    async def __ainit__(self) -> NoReturn:
        self.pool = await asyncpg.create_pool(**self.config.database)
        self.db = DatabaseManager(self)

        self.bot_cache = dict(await self.pool.fetchrow('SELECT * FROM bot_stats'))
        self.guild_cache = await Cache('SELECT * FROM guild_config', 'guild_id', self.pool)
        self.user_cache = await Cache('SELECT * FROM users', 'user_id', self.pool)

    def setup(self) -> NoReturn:
        os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
        os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
        os.environ['JISHAKU_HIDE'] = 'True'

        self.add_check(is_beta)
        self.add_check(is_blacklisted)

        self.loop.create_task(self.__ainit__())

    def run(self, extensions: Union[list, set]):
        """A custom run method to make the launcher file smaller."""
        for ext in extensions:
            # loading all extensions before running the bot.
            self.load_extension(ext)
            logger.info(f'[MODULE] {ext} loaded.')

        super().run(self.config.main.token)
