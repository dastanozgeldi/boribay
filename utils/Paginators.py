import discord
from discord.ext import menus


class MyPages(menus.MenuPages):
	'''My own paginator class.'''

	def __init__(self, source, **kwargs):
		super().__init__(source=source, check_embeds=True, **kwargs)

	async def finalize(self, timed_out):
		try:
			if timed_out:
				await self.message.clear_reactions()
			else:
				await self.message.delete()
		except discord.HTTPException:
			pass


class EmbedPageSource(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=1)

	async def format_page(self, menu, embed):
		maximum = self.get_max_pages()
		embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
		return embed
