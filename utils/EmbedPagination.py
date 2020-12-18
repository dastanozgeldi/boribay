import discord
from discord.ext import menus


class EmbedPageSource(menus.ListPageSource):
    async def format_page(self, menu, embed):
        return embed


class TodoPageSource(menus.ListPageSource):
	def __init__(self, ctx, embed):
		super().__init__(entries=embed, per_page=10)
		self.ctx = ctx

	async def format_page(self, menu, todos: list):
		embed = discord.Embed(
			color=discord.Color.dark_theme()
		).set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar_url)

		if len(todos) <= 1:
			embed.description = f'Currently you have no tasks.\nTo add a task type `{self.ctx.prefix}todo add <your task>`'
		else:
			todos = todos[1:]
			final = list(enumerate(todos, 1))
			to_desc = [f'{number}. {value}' for number, value in final]
			embed.description = '\n'.join(to_desc)
		return embed