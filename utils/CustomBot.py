import asyncio
import os
import re
from datetime import datetime, timedelta
from time import perf_counter

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from utils.CustomContext import CustomContext

load_dotenv()


cluster = AsyncIOMotorClient(f"mongodb+srv://{os.getenv('db_username')}:{os.getenv('db_password')}@{os.getenv('db_project')}.xyuwh.mongodb.net/{os.getenv('db')}?retryWrites=true&w=majority")


async def get_prefix(bot: commands.Bot, message: discord.Message):
	if message.guild:
		prefixes = await cluster.Boribay.prefixes.find_one({"_id": message.guild.id})
		prefix = prefixes['prefix']
	else:
		prefix = '.'
	return commands.when_mentioned_or(prefix)(bot, message)


class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(get_prefix, *args, **kwargs)
		# Database related variables
		self.db = cluster
		self.prefixes = self.db.Boribay.prefixes
		self.collection = self.db.Boribay.colldb
		self.todos = self.db.Boribay.todos
		# Additional variables
		self.start_time = datetime.now()
		self.loop = asyncio.get_event_loop()
		self.session = aiohttp.ClientSession(loop=self.loop)
		self.owner_url = 'http://discord.com/users/682950658671902730'
		self.support_url = 'https://discord.gg/cZy6TvDg79'
		self.invite_url = 'https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot'
		self.github_url = 'https://github.com/Dositan/boribay/'

	@property
	def dosek(self):
		return self.get_user(682950658671902730)

	async def db_latency(self):
		start = perf_counter()
		await self.db.Boribay.command('ping')
		end = perf_counter()
		return f'{round((end - start) * 1000)} ms'

	async def close(self):
		await super().close()
		await self.session.close()

	async def get_context(self, message, *, cls=CustomContext):
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
		post = {
			"_id": guild.id,
			"prefix": "."
		}
		if await self.prefixes.count_documents({"_id": guild.id}) == 0:
			await self.prefixes.insert_one(post)

	async def on_guild_remove(self, guild: discord.Guild):
		await self.prefixes.delete_one({'_id': guild.id})

	'''
	async def on_message_edit(self, before, after):
		if await self.is_owner(before.author):
			await self.process_commands(after)
	'''

	async def get_uptime(self) -> timedelta:
		# return timedelta(seconds=int((datetime.now() - self.start_time).total_seconds()))
		return int((datetime.now() - self.start_time).total_seconds())

	async def reply(self, message_id, content=None, **kwargs):
		message = self._connection._get_message(message_id)
		await message.reply(content, **kwargs)

	async def add_delete_reaction(self, ctx: CustomContext, channel_id, message_id):
		channel = self.get_channel(channel_id)

		if channel is None:
			return

		message = await channel.fetch_message(message_id)

		if message is None:
			return

		await message.add_reaction('\N{WASTEBASKET}')

		def _check(_reaction, _user):
			return _user != self.user and str(_reaction.emoji) == '\N{WASTEBASKET}' and _user == ctx.author

		try:
			reaction, user = await self.wait_for(
				'reaction_add',
				timeout=10.0,
				check=_check
			)
		except asyncio.TimeoutError:
			pass

		else:
			try:
				await message.delete()
			except (discord.Forbidden, discord.HTTPException):
				pass
