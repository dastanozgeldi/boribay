from discord import Member, TextChannel
from discord.ext import commands
from utils.Cog import Cog
from utils.Converters import ColorConverter
from utils.Manipulation import welcome_card


class Settings(Cog):
	"""A settings extension. This is basically how the bot will look like
	in your server. Type **help settings** to see what the parent command does."""

	def __init__(self, bot):
		self.bot = bot
		self.name = '⚙ Guild Settings'
		self.ticks = (
			'<:greenTick:596576670815879169>',
			'<:redTick:596576672149667840>'
		)

	async def cog_check(self, ctx):
		return await commands.has_guild_permissions(administrator=True).predicate(ctx)

	@commands.group(invoke_without_command=True)
	async def settings(self, ctx):
		"""The settings parent command.
		Shows settings statistic of the current server:
		Custom color and custom prefix."""
		fillers = [
			('Custom Prefix', self.ticks[0] if self.bot.config['prefixes'][ctx.guild.id] != '.' else self.ticks[1]),
			('Custom Color', self.ticks[0] if self.bot.config['embed_colors'][ctx.guild.id] != 3553598 else self.ticks[1])
		]
		await ctx.send(embed=self.bot.embed.default(ctx, description='\n'.join(f'**{name}**: {value}' for name, value in fillers)))
		# 	TODO use very wide Table for guilds which includes:
		# 	Role on_member_join
		# 	Welcoming and Leaving messages, maybe Images!

	@settings.command()
	async def welcome(self, ctx, channel: TextChannel, member: Member):
		"""Sets a welcoming message or image to the database of this server,
		if any given."""
		await channel.send(file=await welcome_card(member))

	# Well the code above works with no problem, unexpectedly right?
	# TODO I must learn PostgreSQL a lot to hit results I want, brb

	@settings.command()
	async def prefix(self, ctx, prefix: str):
		"""Set Prefix command
		Args: prefix (str): a new prefix that you want to set."""
		self.bot.config['prefixes'][ctx.guild.id] = prefix
		await self.bot.pool.execute('UPDATE guild_config SET prefix = $1 WHERE guild_id = $2', prefix, ctx.guild.id)
		await ctx.send('Prefix has been changed to: `%s`' % prefix)

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
