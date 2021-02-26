import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from time import perf_counter

import aiohttp
import asyncpg
import toml
from dbl import DBLClient
from discord import AllowedMentions, Game, Intents, flags
from discord.ext import commands, ipc

from utils.Context import Context
from utils.Embed import Embed
from utils.Cache import Cache

intents = Intents.default()
intents.members = True
logging.basicConfig(filename='./data/logs/discord.log', filemode='w', level=logging.INFO)
handler = RotatingFileHandler('./data/logs/discord.log', maxBytes=5242880, backupCount=1)
os.environ['JISHAKU_HIDE'] = 'True'
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'


def get_prefix(bot, message):
    if not message.guild:
        prefix = '.'
    else:
        prefix = bot.cache[message.guild.id].get('prefix', '.')
    return commands.when_mentioned_or(prefix)(bot, message)


class Boribay(commands.Bot):
    """A custom Bot class subclassed from commands.Bot"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            get_prefix,
            intents=intents,
            max_messages=1000,
            case_insensitive=True,
            activity=Game(name='.help'),
            chunk_guilds_at_startup=False,
            member_cache_flags=flags.MemberCacheFlags.from_intents(intents),
            allowed_mentions=AllowedMentions(everyone=False, roles=False, replied_user=False),
            **kwargs
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.embed = Embed
        self.config = toml.load('config.toml')
        self.log = logging.getLogger(__name__)
        self.log.addHandler(handler)
        self.owner_ids = {682950658671902730, 382183425815216128}
        self.regex = {
            'RGB_REGEX': r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?',
            'EMOJI_REGEX': r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>',
            'URL_REGEX': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
        self.command_usage = 0
        self.start_time = datetime.now()
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.__ainit__())
        self.loop.create_task(self.check_changes())
        self.ipc = ipc.Server(
            bot=self,
            host=self.config['ipc']['host'],
            port=self.config['ipc']['port'],
            secret_key=self.config['ipc']['secret_key']
        )
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.dblpy = DBLClient(self, self.config['bot']['dbl_token'])

    async def __ainit__(self):
        await self.wait_until_ready()
        self.pool = await asyncpg.create_pool(**self.config['database'])
        self.cache = await Cache('SELECT * FROM guild_config', 'guild_id', self.pool)

    @property
    def dosek(self):
        return self.get_user(682950658671902730)

    @property
    def uptime(self) -> timedelta:
        return int((datetime.now() - self.start_time).total_seconds())

    async def check_changes(self):
        await self.wait_until_ready()
        guild_config = await self.pool.fetch('SELECT * FROM guild_config')
        bot_guild_ids = {guild.id for guild in self.guilds}
        db_guild_ids = {row['guild_id'] for row in guild_config}

        if difference := list(bot_guild_ids - db_guild_ids):
            # condition above checks if there were new guilds while the bot was sleeping.
            for guild_id in difference:
                # if there are, iteratively add them to the database.
                await self.pool.execute('INSERT INTO guild_config(guild_id) VALUES($1)', guild_id)

        if difference := list(db_guild_ids - bot_guild_ids):
            # the same condition but subtracting set of guild id's in db with current guild id's
            for guild_id in difference:
                # if there are, iteratively remove them from the database.
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

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        self.log.info(f'Logged in as -> {self.user.name}')
        self.log.info(f'Client ID -> {self.user.id}')
        self.log.info(f'Guild Count -> {len(self.guilds)}')

    async def on_ipc_ready(self):
        self.log.info('IPC Server ready.')

    async def on_message(self, message):
        if not self.is_ready():
            return
        if message.channel.id == 789791676632662017:
            with open('news.md', 'w') as f:
                msg = message.content.split('\n')
                f.write(msg[0] + '\n' + '\n'.join(msg[1:]))
        if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
            ctx = await self.get_context(message)
            await self.get_command('prefix')(ctx)
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            if after.author.id in self.owner_ids:
                return await self.process_commands(after)
        if before.embeds:
            return

    async def reply(self, message_id, content=None, **kwargs):
        message = self._connection._get_message(message_id)
        await message.reply(content, **kwargs)
