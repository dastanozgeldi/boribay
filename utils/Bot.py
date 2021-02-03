import re
import toml
import discord
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
		self.exts = self.config['bot']['exts']
		self.owner_exts = ('Jishaku', 'Events', 'Owner', 'ErrorHandler', 'GuildSettings', 'TopGG')
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
		self.owner_url = 'http://discord.com/users/682950658671902730'
		self.invite_url = 'https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot'
		self.github_url = 'https://github.com/Dositan/boribay/'
		self.support_url = 'https://discord.gg/cZy6TvDg79'
		self.topgg_url = 'https://top.gg/bot/735397931355471893#/'

	@property
	def dosek(self):
		return self.get_user(682950658671902730)

	@property
	async def uptime(self) -> timedelta:
		return int((datetime.now() - self.start_time).total_seconds())

	async def db_latency(self):
		start = perf_counter()
		await self.pool.fetchval('SELECT 1;')
		end = perf_counter()
		return end - start

	async def cache_guilds(self):
		await self.wait_until_ready()
		guild_config = await self.pool.fetch('SELECT guild_id, prefix, embed_color FROM guild_config')
		self.config['prefixes'] = {i['guild_id']: i['prefix'] for i in guild_config}
		self.config['embed_colors'] = {i['guild_id']: i['embed_color'] for i in guild_config}

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
			cmd = self.get_command('prefix')
			await cmd(ctx)
		await self.process_commands(message)

	async def on_guild_join(self, guild: discord.Guild):
		query = 'INSERT INTO guild_config(guild_id, prefix, member_log, member_log_message, mod_log) VALUES($1, $2, $3, $4, $5)'
		await self.pool.execute(query, guild.id, '.', None, None, None)

	async def on_guild_remove(self, guild: discord.Guild):
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
