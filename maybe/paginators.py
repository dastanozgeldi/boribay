from discord.ext import menus


class SQLListPageSource(menus.ListPageSource):
	def __init__(self, ctx, data, *, per_page=5):
		super().__init__(data, per_page=per_page)
		self.ctx = ctx

	async def format_page(self, menu, page):
		embed = self.ctx.bot.embed.default(
			self.ctx, description='```py\n' + '\n'.join(page) + '\n```'
		)
		embed.set_author(name=f'Page {menu.current_page + 1} / {self.get_max_pages()}')
		return embed
