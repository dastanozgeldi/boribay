import discord
from discord.ext import commands, menus


class BaseCog(commands.Cog):

	def __init__(self, bot, show_name):
		super().__init__()
		self.bot = bot
		self.show_name = show_name


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


class GroupHelp(menus.ListPageSource):
	'''Sends help for group-commands.'''

	def __init__(self, ctx, group, cmds, *, prefix):
		super().__init__(entries=cmds, per_page=5)
		self.ctx = ctx
		self.group = group
		self.prefix = prefix
		self.title = f'Help for category `{self.group.qualified_name}`'
		self.description = self.group.description

	async def format_page(self, menu, cmds):
		embed = discord.Embed(
			title=self.title,
			description=self.description,
			color=discord.Color.dark_theme()
		)
		for cmd in cmds:
			signature = f'{self.prefix}{cmd.qualified_name} {cmd.signature}'
			embed.add_field(
				name=signature,
				value=cmd.brief.format(prefix=self.ctx.prefix) or 'No help provided.',
				inline=False
			)

		maximum = self.get_max_pages()
		if maximum > 1:
			embed.set_author(
				name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} commands)')
		embed.set_footer(
			text=f'{self.prefix}help to see all commands list.')
		return embed


class Menu(menus.Menu):

	def __init__(self, pages, embed: bool = True, **kwargs):
		super().__init__(**kwargs)
		self.pages = pages
		self.embed = embed
		self.cur_page = 0

	async def change(self):
		new_page = self.pages[self.cur_page]
		if self.embed:
			await self.message.edit(embed=new_page)
		else:
			await self.message.edit(content=new_page)

	async def send_initial_message(self, ctx, channel):
		if self.embed:
			return await channel.send(embed=self.pages[self.cur_page])

	@menus.button('\N{LEFTWARDS BLACK ARROW}')
	async def previous_page(self, payload):
		if self.cur_page > 0:
			self.cur_page -= 1
			await self.change()

	@menus.button('\N{BLACK SQUARE FOR STOP}')
	async def stop_pages(self, payload):
		self.stop()

	@menus.button('\N{BLACK RIGHTWARDS ARROW}')
	async def next_page(self, payload):
		if self.cur_page < len(self.pages) - 1:
			self.cur_page += 1
			await self.change()


class MainHelp(menus.ListPageSource):
	'''Creates an embedded message including all commands (if not hidden).'''

	def __init__(self, ctx, categories: list):
		super().__init__(entries=categories, per_page=3)
		self.ctx = ctx

	async def format_page(self, menu, category):
		embed = discord.Embed(
			title='Help',
			description=f'```diff\n- <> ← required argument\n- [] ← optional argument\n+ {self.ctx.prefix}help [Category | group] to get help for a module.```',
			color=discord.Color.dark_theme()).set_footer(text=f'{self.ctx.prefix}help <command> to get more info about specific command.')
		for k, v in category:
			embed.add_field(name=k, value=v, inline=False)

		return embed


class MyHelpCommand(commands.HelpCommand):

	async def get_ending_note(self):
		return f'Type {self.clean_prefix}{self.invoked_with} [Category | command] to learn more about commands.'

	async def send_bot_help(self, mapping):
		cats = []
		for cog, cmds in mapping.items():
			if not hasattr(cog, "qualified_name"):
				continue
			name = "No Category" if cog is None else cog.qualified_name
			filtered = await self.filter_commands(cmds, sort=True)
			if filtered:
				all_cmds = " ─ ".join(f"`{c.name}`" for c in cmds)
				if cog:
					cats.append([name, f">>> {all_cmds}\n"])

		menu = MyPages(source=MainHelp(self.context, cats))
		await menu.start(self.context)

	async def send_cog_help(self, cog: BaseCog):
		ctx = self.context
		prefix = self.clean_prefix
		if not hasattr(cog, 'show_name'):
			pass
		entries = await self.filter_commands(cog.get_commands(), sort=True)
		menu = MyPages(
			GroupHelp(ctx, cog, entries, prefix=prefix),
			clear_reactions_after=True
		)
		await menu.start(ctx)

	async def send_command_help(self, command):
		embed = discord.Embed(
			title=self.get_command_signature(command),
			color=discord.Color.dark_theme()
		)
		aliases = ' | '.join(command.aliases)
		category = command.cog_name
		if command.aliases:
			embed.add_field(
				name='Aliases',
				value=aliases,
				inline=False
			)
		if category:
			embed.add_field(
				name='Category',
				value='No category...' if not category else category,
				inline=False
			)
		else:
			pass

		if command.description and not command.help:
			embed.description = command.description
		if command.help:
			embed.description = command.help
		else:
			embed.description = command.brief or 'No help found...'
		await self.get_destination().send(embed=embed)

	async def send_group_help(self, group: commands.Group):
		ctx = self.context
		prefix = self.clean_prefix
		subcommands = group.commands
		if len(subcommands) == 0:
			return await self.send_command_help(group)
		entries = await self.filter_commands(subcommands, sort=True)
		if len(entries) == 0:
			return await self.send_command_help(group)
		source = GroupHelp(ctx=ctx, group=group, cmds=entries, prefix=prefix)
		menu = MyPages(source)
		await menu.start(ctx)

	async def command_not_found(self, string):
		if len(string) >= 50:
			return f"Could not find the command `{string[:20]}...`."
		else:
			return f"Could not find the command `{string}`."

	def get_command_signature(self, command: commands.Command):
		return f'{self.clean_prefix}{command.qualified_name} {command.signature}'
