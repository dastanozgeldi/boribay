import discord
import asyncio
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


class SQLListPageSource(menus.ListPageSource):
	def __init__(self, data, *, per_page=5):
		super().__init__(data, per_page=per_page)

	async def format_page(self, menu, page):
		embed = discord.Embed(description='```sql\n' + "\n".join(page) + '\n```')
		return embed


class EmbedPageSource(menus.ListPageSource):
	def __init__(self, data):
		super().__init__(data, per_page=1)

	async def format_page(self, menu, embed):
		maximum = self.get_max_pages()
		embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
		return embed


class NoReactionsPassed(discord.ext.commands.CommandInvokeError):
	pass


class Poll:
	def __init__(self, entries, title=None, footer=None, color=0x36393E, timeout=30.0, return_index=False):
		self.entries = entries
		self.title = title or "Untitled"
		self.footer = footer
		self.color = color
		self.timeout = timeout
		self.return_index = return_index

	async def pagination(self, ctx, loc=None, user=None):
		if len(self.entries) < 2:
			raise ValueError("Not enough data to create a poll.")
		elif len(self.entries) > 10:
			raise ValueError("Maximum limit 10 has reached.")
		e = ctx.bot.embed(title=self.title, description="", color=self.color)
		self.emojis = []
		for i, c in enumerate(self.entries):
			if i < 9:
				self.emojis.append(f"{i + 1}\u20E3")
			else:
				self.emojis.append("\U0001F51F")
			e.description = f"{e.description}{self.emojis[i]} {c}\n"

		if self.footer:
			e.set_footer(text=self.footer)

		self.controller = e
		return await self.reactions(ctx, user, loc)

	async def reactions(self, ctx, user, loc):
		if not loc:
			mes = await ctx.send(embed=self.controller)
		else:
			mes = await loc.send(embed=self.controller)

		for emoji in self.emojis:
			await mes.add_reaction(emoji)

		user = loc if loc else user

		def check(r, u):
			if str(r) not in self.emojis or u.id == ctx.bot.user.id or r.message.id != mes.id:
				return False
			if not user:
				if u.id != ctx.author.id:
					return False
			else:
				if u.id != user.id:
					return False
			return True

		try:
			r, u = await ctx.bot.wait_for("reaction_add", check=check, timeout=self.timeout)
		except asyncio.TimeoutError:
			await self.stop(mes)
			raise NoReactionsPassed("You didn't choose anything.")

		control = self.entries[self.emojis.index(str(r))]
		await self.stop(mes)
		if not self.return_index:
			return control
		else:
			return self.emojis.index(str(r))

	async def stop(self, msg):
		try:
			await msg.delete()
		except discord.HTTPException:
			pass
