import asyncio
import re
from datetime import datetime, timedelta
from time import perf_counter

import aiohttp
import asyncpg
import discord
import toml
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from utils.CustomContext import Context
from utils.CustomEmbed import Embed


async def get_prefix(bot: commands.Bot, message: discord.Message):
	if message.guild:
		prefix = await bot.pool.fetchval('SELECT prefix FROM guild_config WHERE guild_id = $1', message.guild.id)
	else:
		prefix = '.'
	return commands.when_mentioned_or(prefix)(bot, message)


class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(get_prefix, *args, **kwargs)
		self.config = toml.load('config.toml')
		self.owner_ids = {682950658671902730, 735489760491077742}
		self.command_usage = 0
		# Database related variables
		self.db = AsyncIOMotorClient(f'mongodb+srv://{self.config["mongo"]["username"]}:{self.config["mongo"]["password"]}@{self.config["mongo"]["project"]}.xyuwh.mongodb.net/{self.config["mongo"]["database"]}?authSource=admin&w=majority&readPreference=primary&retryWrites=true')
		self.collection = self.db.Boribay.colldb
		self.todos = self.db.Boribay.todos
		# Additional variables
		self.embed = Embed
		self.start_time = datetime.now()
		self.loop = asyncio.get_event_loop()
		self.pool = self.loop.run_until_complete(asyncpg.create_pool(
			user=self.config['database']['user'],
			password=self.config['database']['password'],
			host=self.config['database']['host'],
			database=self.config['database']['database']
		))
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.owner_url = 'http://discord.com/users/682950658671902730'
		self.support_url = 'https://discord.gg/cZy6TvDg79'
		self.invite_url = 'https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot'
		self.github_url = 'https://github.com/Dositan/boribay/'

	async def db_latency(self):
		start = perf_counter()
		await self.pool.fetchval('SELECT 1;')
		end = perf_counter()
		return f'{round((end - start) * 1000, 2)} ms'

	async def close(self):
		await super().close()
		await self.session.close()

	async def get_context(self, message, *, cls=Context):
		return await super().get_context(message, cls=cls)

	async def on_message(self, message):
		if not self.is_ready():
			return

		MENTION_REGEX = f'<@(!)?{self.user.id}>'

		if re.fullmatch(MENTION_REGEX, message.content):
			ctx = await self.get_context(message)
			cmd = self.get_command('prefix')

			await cmd(ctx)

		await self.process_commands(message)

	async def on_guild_join(self, guild: discord.Guild):
		await self.pool.execute('INSERT INTO guild_config(guild_id, prefix, log_channel) VALUES($1, $2, $3)', guild.id, '.', None)

	async def on_guild_remove(self, guild: discord.Guild):
		await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild.id)

	async def on_message_edit(self, before, after):
		if before.content != after.content:
			if after.author.id in self.owner_ids:
				return await self.process_commands(after)
		if before.embeds:
			return

	async def get_uptime(self) -> timedelta:
		return int((datetime.now() - self.start_time).total_seconds())

	async def reply(self, message_id, content=None, **kwargs):
		message = self._connection._get_message(message_id)
		await message.reply(content, **kwargs)

	@property
	def dosek(self):
		return self.get_user(682950658671902730)
