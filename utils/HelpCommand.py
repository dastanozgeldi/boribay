from difflib import get_close_matches
from discord.ext import commands, menus
from utils.CustomCog import Cog
from utils.Paginators import MyPages
from utils.CustomEmbed import Embed


class GroupHelp(menus.ListPageSource):
	'''Sends help for group-commands.'''

	def __init__(self, ctx, group, cmds, *, prefix):
		super().__init__(entries=cmds, per_page=3)
		self.ctx = ctx
		self.group = group
		self.prefix = prefix
		self.title = f'Help for category `{self.group.qualified_name}`'
		self.description = '```fix\n<> ← required argument\n[] ← optional argument```'

	async def format_page(self, menu, cmds):
		embed = Embed(
			title=self.title,
			description=self.description
		)
		for cmd in cmds:
			signature = f'{self.prefix}{cmd.qualified_name} {cmd.signature}'
			desc = cmd.help or cmd.brief
			embed.add_field(
				name=signature,
				value=desc.format(prefix=self.ctx.prefix),
				inline=False
			)

		maximum = self.get_max_pages()
		if maximum > 1:
			embed.set_author(
				name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} commands)')

		embed.set_footer(text=f'{self.prefix}help to see all commands list.')
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
		self.count = len(categories)

	async def format_page(self, menu, category):
		embed = Embed(
			description=f'''{self.ctx.prefix}help [category | group] to get module help
			[Invite]({self.ctx.bot.invite_url}) | [Support]({self.ctx.bot.support_url}) | [Source]({self.ctx.bot.github_url})''',
		).set_footer(text=f'{self.ctx.prefix}help <command> to get command help.')
		embed.set_author(
			name=f'Page {menu.current_page + 1} of {self.get_max_pages()} ({self.count} categories)',
			icon_url=self.ctx.author.avatar_url_as(size=128)
		)
		for k, v in category:
			embed.add_field(name=k, value=v, inline=False)
		return embed


class MyHelpCommand(commands.HelpCommand):

	async def get_ending_note(self):
		return f'Type {self.clean_prefix}{self.invoked_with} [Category | command] to learn more about commands.'

	async def send_bot_help(self, mapping):
		cats = []
		for cog, cmds in mapping.items():
			if not hasattr(cog, "name"):
				continue
			name = cog.name or "No Category"
			filtered = await self.filter_commands(cmds, sort=True)
			if filtered:
				all_cmds = ", ".join(f"`{c.name}`" for c in cmds)
				if cog:
					cats.append([name, f"> {all_cmds}\n"])

		menu = MyPages(source=MainHelp(self.context, cats), timeout=30.0)
		await menu.start(self.context)

	async def send_cog_help(self, cog: Cog):
		ctx = self.context
		prefix = self.clean_prefix
		if not hasattr(cog, 'name'):
			pass
		entries = await self.filter_commands(cog.get_commands(), sort=True)
		menu = MyPages(
			GroupHelp(ctx, cog, entries, prefix=prefix),
			clear_reactions_after=True,
			timeout=30.0
		)
		await menu.start(ctx)

	async def send_command_help(self, command):
		embed = Embed(title=self.get_command_signature(command))
		aliases = ' | '.join(command.aliases)
		category = command.cog_name
		if command.aliases:
			embed.add_field(name='Aliases', value=aliases, inline=True)
		if category:
			embed.add_field(name='Category', value=category or 'No category...', inline=True)
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
		menu = MyPages(source, timeout=30.0)
		await menu.start(ctx)

	async def command_not_found(self, string):
		bot = self.context.bot
		commands_list = [i.name for i in bot.commands]
		dym = '\n'.join(get_close_matches(string, commands_list))
		if dym:
			return f'Could not find the command `{string}`. Did you mean...\n{dym}'
		else:
			return f'Could not find the command `{string}`'

	def get_command_signature(self, command: commands.Command):
		return f'{self.clean_prefix}{command.qualified_name} {command.signature}'
