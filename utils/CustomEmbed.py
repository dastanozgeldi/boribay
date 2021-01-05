import discord
import datetime


class Embed(discord.Embed):
	def __init__(self, color=0x36393E, timestamp=None, **kwargs):
		super(Embed, self).__init__(
			color=color,
			timestamp=timestamp or datetime.datetime.utcnow(),
			**kwargs
		)

	@classmethod
	def default(cls, ctx, **kwargs):
		instance = cls(**kwargs)
		instance.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
		return instance

	@classmethod
	def error(cls, color=0xe74c3c, **kwargs):
		return cls(color=color, **kwargs)
