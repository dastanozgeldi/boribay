import re
import toml
import asyncio
import aiohttp
import asyncpg
from time import perf_counter
from utils.Embed import Embed
from discord.ext import commands
from utils.Context import Context
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dbl import DBLClient


async def get_prefix(bot, message):
	if not message.guild:
		prefix = '.'
	else:
		prefix = bot.config['prefixes'][message.guild.id]
	return commands.when_mentioned_or(prefix)(bot, message)


class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(get_prefix, *args, **kwargs)
		self.embed = Embed
		self.config = toml.load('config.toml')
		self.owner_ids = {682950658671902730, 382183425815216128}
		self.regex = {
			'RGB_REGEX': r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?',
			'EMOJI_REGEX': r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>',
			'URL_REGEX': r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
		}
		self.command_usage = 0
		self.db = AsyncIOMotorClient(f'mongodb+srv://{self.config["mongo"]["username"]}:{self.config["mongo"]["password"]}@{self.config["mongo"]["project"]}.xyuwh.mongodb.net/{self.config["mongo"]["database"]}?authSource=admin&w=majority&readPreference=primary&retryWrites=true')
		self.start_time = datetime.now()
		self.loop = asyncio.get_event_loop()
		self.loop.create_task(self.cache_guilds())
		self.pool = self.loop.run_until_complete(asyncpg.create_pool(
			user=self.config['database']['user'],
			password=self.config['database']['password'],
			host=self.config['database']['host'],
			database=self.config['database']['database']
		))
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.dblpy = DBLClient(self, self.config['bot']['dbl_token'])

	@property
	def dosek(self):
		return self.get_user(682950658671902730)

	@property
	def uptime(self) -> timedelta:
		return int((datetime.now() - self.start_time).total_seconds())

	async def db_latency(self):
		start = perf_counter()
		await self.pool.fetchval('SELECT 1;')
		end = perf_counter()
		return end - start

	async def cache_guilds(self):
		await self.wait_until_ready()
		_1 = {i.id for i in self.guilds}
		_2 = {i['guild_id'] for i in await self.pool.fetch('select guild_id from guild_config')}
		if difference := list(_1 - _2):
			for _id in difference:
				await self.pool.execute('INSERT INTO guild_config(guild_id) VALUES($1)', _id)
		guild_config = await self.pool.fetch('SELECT * FROM guild_config')
		self.config['prefixes'] = {i['guild_id']: i['prefix'] for i in guild_config}
		self.config['embed_colors'] = {i['guild_id']: i['embed_color'] for i in guild_config}
		self.config['welcome_channel'] = {i['guild_id']: i['welcome_channel'] for i in guild_config}

	async def close(self):
		await super().close()
		await self.dblpy.close()
		await self.session.close()

	async def get_context(self, message, *, cls=Context):
		return await super().get_context(message, cls=cls)

	async def on_message(self, message):
		if not self.is_ready():
			return
		if message.channel.id == 789791676632662017:
			open('news.md', 'w').write(message.content)
		if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
			ctx = await self.get_context(message)
			await self.get_command('prefix')(ctx)
		await self.process_commands(message)

	async def on_guild_join(self, guild):
		query = 'INSERT INTO guild_config(guild_id) VALUES($1)'
		await self.pool.execute(query, guild.id)

	async def on_guild_remove(self, guild):
		await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild.id)

	async def on_message_edit(self, before, after):
		if before.content != after.content:
			if after.author.id in self.owner_ids:
				return await self.process_commands(after)
		if before.embeds:
			return

	async def reply(self, message_id, content=None, **kwargs):
		message = self._connection._get_message(message_id)
		await message.reply(content, **kwargs)
