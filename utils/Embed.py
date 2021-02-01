import discord
import datetime


class Embed(discord.Embed):
	def __init__(self, timestamp=None, **kwargs):
		super(Embed, self).__init__(
			timestamp=timestamp or datetime.datetime.utcnow(),
			**kwargs
		)

	@classmethod
	def default(cls, ctx, **kwargs):
		instance = cls(**kwargs)
		try:
			instance.color = ctx.bot.config['embed_colors'][ctx.guild.id]
		except (AttributeError, KeyError):
			instance.color = 0x36393e
		return instance

	@classmethod
	def error(cls, color=0xff0000, **kwargs):
		return cls(color=color, **kwargs)
