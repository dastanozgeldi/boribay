from discord import TextChannel
from discord.ext import commands
from utils.Cog import Cog
from utils.Converters import ColorConverter


class Settings(Cog):
	"""A settings extension. This is basically how the bot will look like
	in your server. Type **help settings** to see what the parent command does."""

	def __init__(self, bot):
		self.bot = bot
		self.name = '⚙ Guild Settings'

	async def cog_check(self, ctx):
		return await commands.has_guild_permissions(administrator=True).predicate(ctx)

	def on_or_off(self, ctx, key, check):
		if self.bot.config[key][ctx.guild.id] != check:
			return '<:greenTick:596576670815879169>'
		return '<:redTick:596576672149667840>'

	@commands.group(invoke_without_command=True)
	async def settings(self, ctx):
		"""The settings parent command.
		Shows settings statistic of the current server:
		Custom color and custom prefix."""
		fillers = [
			('Custom Prefix', self.on_or_off(ctx, 'prefixes', '.')),
			('Custom Color', self.on_or_off(ctx, 'embed_colors', 3553598)),
			('Welcome Channel', self.on_or_off(ctx, 'welcome_channel', None))
		]
		await ctx.send(embed=self.bot.embed.default(ctx, description='\n'.join(f'**{name}**: {value}' for name, value in fillers)))
		# 	TODO use very wide Table for guilds which includes:
		# 	Role on_member_join

	@settings.command(aliases=['wc'])
	async def welcomechannel(self, ctx, channel: TextChannel):
		"""Set Welcome channel command.
		Args: channel: Channel where the bot should log messages to.
		message: Message content that the bot should send."""
		query = 'UPDATE guild_config SET welcome_channel = $1 WHERE guild_id = $2'
		await self.bot.pool.execute(query, channel.id, ctx.guild.id)
		await ctx.send(f'Set {channel.mention} as a welcoming channel.')

	@settings.command()
	async def prefix(self, ctx, prefix: str):
		"""Set Prefix command
		Args: prefix (str): a new prefix that you want to set."""
		self.bot.config['prefixes'][ctx.guild.id] = prefix
		await self.bot.pool.execute('UPDATE guild_config SET prefix = $1 WHERE guild_id = $2', prefix, ctx.guild.id)
		await ctx.send(f'Prefix has been changed to: `{prefix}`')

	@settings.command(aliases=['colour'])
	async def color(self, ctx, color: ColorConverter):
		"""Sets the custom color for the bot. Then all embeds color will be one
		that you specified. To bring the default color back,
		use `settings color #36393e`"""
		color = int(str(color).replace('#', ''), 16)
		self.bot.config['embed_colors'][ctx.guild.id] = color
		await self.bot.pool.execute('UPDATE guild_config SET embed_color = $1 WHERE guild_id = $2', color, ctx.guild.id)
		await ctx.message.add_reaction('✅')


def setup(bot):
	bot.add_cog(Settings(bot))
