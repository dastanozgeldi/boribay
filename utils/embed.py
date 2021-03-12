from datetime import datetime as dt

from discord import Embed as E


class Embed(E):
	def __init__(self, timestamp=None, **kwargs):
		super(Embed, self).__init__(
			timestamp=timestamp or dt.utcnow(),
			**kwargs
		)

	@classmethod
	def default(cls, ctx, **kwargs):
		g = ctx.guild
		instance = cls(**kwargs)
		instance.color = 0x36393e if not g else ctx.bot.cache[g.id]['embed_color']

		return instance

	@classmethod
	def error(cls, color=0xff0000, **kwargs):
		return cls(color=color, **kwargs)
