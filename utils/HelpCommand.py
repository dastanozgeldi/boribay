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
		doc = self.group.__doc__ if isinstance(self.group, commands.Cog) else self.group.help
		embed = Embed(title=self.title, description=f'{doc}\n{self.description}')
		for cmd in cmds:
			signature = f'{self.prefix}{cmd.qualified_name} {cmd.signature}'
			desc = cmd.help
			embed.add_field(name=signature, value=desc.format(prefix=self.ctx.prefix), inline=False)
		maximum = self.get_max_pages()
		if maximum > 1:
			embed.set_author(name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} commands)')
		embed.set_footer(text=f'{self.prefix}help to see all commands list.')
		return embed


class MainHelp(menus.ListPageSource):
	'''Creates an embedded message including all commands (if not hidden).'''

	def __init__(self, ctx, categories: list):
		super().__init__(entries=categories, per_page=3)
		self.ctx = ctx
		self.count = len(categories)

	async def format_page(self, menu, category):
		embed = Embed(
			description=f'{self.ctx.prefix}help [Category | group] to get module help\n'
			f'[Invite]({self.ctx.bot.invite_url}) | [Support]({self.ctx.bot.support_url}) | [Source]({self.ctx.bot.github_url})',
		).set_footer(text=f'{self.ctx.prefix}help <command> to get command help.')
		embed.set_author(
			name=f'Page {menu.current_page + 1} of {self.get_max_pages()} ({self.count} categories)',
			icon_url=self.ctx.author.avatar_url_as(size=64)
		)
		for name, value in category:
			embed.add_field(name=name, value=value, inline=False)
		return embed


class MyHelpCommand(commands.HelpCommand):

	async def get_ending_note(self):
		return f'Type {self.clean_prefix}{self.invoked_with} [Category] to get help for a category.'

	async def send_bot_help(self, mapping):
		cats = []
		for cog, cmds in mapping.items():
			if not hasattr(cog, 'name'):
				continue
			filtered = await self.filter_commands(cmds, sort=True)
			if filtered:
				all_cmds = ", ".join(f"`{c.name}`" for c in cmds)
				if cog:
					cats.append([cog.name, f"> {all_cmds}\n"])

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
		embed.set_footer(text=await self.get_ending_note())
		aliases = ' | '.join(command.aliases)
		category = command.cog_name
		if command.aliases:
			embed.add_field(name='Aliases', value=aliases, inline=True)
		if category:
			embed.add_field(name='Category', value=category, inline=True)
		else:
			pass

		embed.description = command.help or 'No help found...'
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
		commands_list = [i.name for i in self.context.bot.commands]
		dym = '\n'.join(get_close_matches(string, commands_list))
		if not dym:
			msg = f'Could not find the command `{string}`.'
		else:
			msg = f'Could not find the command {string}. Did you mean...\n{dym}'
		return msg

	def get_command_signature(self, command: commands.Command):
		return f'{self.clean_prefix}{command.qualified_name} {command.signature}'
