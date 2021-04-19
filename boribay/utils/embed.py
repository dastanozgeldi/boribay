from datetime import datetime as dt

from discord import Embed as E


class Embed(E):
	def __init__(self, timestamp=None, **kwargs):
		super(Embed, self).__init__(timestamp=timestamp or dt.utcnow(), **kwargs)

	@classmethod
	def default(cls, ctx, **kwargs):
		g = ctx.guild
		color = 0x36393f if not g else ctx.bot.guild_cache[g.id]['embed_color']
		return cls(color=color, **kwargs)

	@classmethod
	def error(cls, color=0xff0000, **kwargs):
		return cls(color=color, **kwargs)
