import re
import toml
import discord
import asyncio
import aiohttp
import asyncpg
from time import perf_counter
from utils.CustomEmbed import Embed
from discord.ext import commands, ipc
from utils.CustomContext import Context
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient


async def get_prefix(bot: commands.Bot, message: discord.Message):
	if await bot.is_owner(message.author) and message.content.startswith('dev'):
		prefix = ''
	elif message.guild is None:
		prefix = '.'
	else:
		prefix = await bot.pool.fetchval('SELECT prefix FROM guild_config WHERE guild_id = $1', message.guild.id)
	return commands.when_mentioned_or(prefix)(bot, message)


class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(get_prefix, *args, **kwargs)
		self.embed = Embed
		self.config = toml.load('config.toml')
		self.owner_ids = {682950658671902730, 735489760491077742}
		self.exts = self.config['bot']['exts']
		self.owner_exts = ('Jishaku', 'Events', 'Owner', 'ErrorHandler')
		self.regex = {
			'RGB_REGEX': r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?',
			'EMOJI_REGEX': r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>',
			'URL_REGEX': r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
		}
		self.command_usage = 0
		self.db = AsyncIOMotorClient(f'mongodb+srv://{self.config["mongo"]["username"]}:{self.config["mongo"]["password"]}@{self.config["mongo"]["project"]}.xyuwh.mongodb.net/{self.config["mongo"]["database"]}?authSource=admin&w=majority&readPreference=primary&retryWrites=true')
		self.start_time = datetime.now()
		self.loop = asyncio.get_event_loop()
		self.pool = self.loop.run_until_complete(asyncpg.create_pool(
			user=self.config['database']['user'],
			password=self.config['database']['password'],
			host=self.config['database']['host'],
			database=self.config['database']['database']
		))
		self.ipc = ipc.Server(
			bot=self,
			host=self.config['ipc']['host'],
			port=self.config['ipc']['port'],
			secret_key=self.config['ipc']['secret_key']
		)
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.owner_url = 'http://discord.com/users/682950658671902730'
		self.invite_url = 'https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot'
		self.github_url = 'https://github.com/Dositan/boribay/'
		self.support_url = 'https://discord.gg/cZy6TvDg79'

	@property
	def dosek(self):
		return self.get_user(682950658671902730)

	@property
	async def db_latency(self):
		start = perf_counter()
		await self.pool.fetchval('SELECT 1;')
		end = perf_counter()
		return f'{(end - start) * 1000:.2f} ms'

	async def close(self):
		await super().close()
		await self.session.close()

	async def get_context(self, message, *, cls=Context):
		return await super().get_context(message, cls=cls)

	async def on_message(self, message):
		if not self.is_ready():
			return
		if re.fullmatch(f'<@(!)?{self.user.id}>', message.content):
			ctx = await self.get_context(message)
			cmd = self.get_command('prefix')
			await cmd(ctx)
		await self.process_commands(message)

	async def on_guild_join(self, guild: discord.Guild):
		await self.pool.execute(
			'INSERT INTO guild_config(guild_id, prefix, member_log, member_log_message, mod_log) VALUES($1, $2, $3, $4, $5, $6)',
			guild.id, '.', None, None, None, None
		)

	async def on_guild_remove(self, guild: discord.Guild):
		await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild.id)

	async def on_message_edit(self, before, after):
		if before.content != after.content:
			if after.author.id in self.owner_ids:
				return await self.process_commands(after)
		if before.embeds:
			return

	@property
	async def uptime(self) -> timedelta:
		return int((datetime.now() - self.start_time).total_seconds())

	async def reply(self, message_id, content=None, **kwargs):
		message = self._connection._get_message(message_id)
		await message.reply(content, **kwargs)
