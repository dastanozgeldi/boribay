from difflib import get_close_matches
from discord.ext import commands, menus
from utils.Cog import Cog
from utils.Paginators import MyPages


class GroupHelp(menus.ListPageSource):
	'''Sends help for group-commands.'''

	def __init__(self, ctx, group, cmds, *, prefix):
		super().__init__(entries=cmds, per_page=3)
		self.ctx = ctx
		self.group = group
		self.prefix = prefix
		self.title = f'Help for category: {self.group.name}'
		self.description = '```fix\n<> ← required argument\n[] ← optional argument```'

	async def format_page(self, menu, cmds):
		doc = self.group.__doc__ if isinstance(self.group, Cog) else self.group.help
		embed = self.ctx.bot.embed.default(self.ctx, title=self.title, description=f'{doc}\n{self.description}')
		for cmd in cmds:
			signature = f'{self.prefix}{cmd.qualified_name} {cmd.signature}'
			embed.add_field(name=signature, value=cmd.help.format(prefix=self.prefix), inline=False)
		if maximum := self.get_max_pages() > 1:
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
		embed = self.ctx.bot.embed.default(
			self.ctx,
			description=f'{self.ctx.prefix}help [Category | group] to get module help\n'
			f'[Invite]({self.ctx.bot.invite_url}) | [Support]({self.ctx.bot.support_url}) | [Source]({self.ctx.bot.github_url})'
		)
		embed.set_footer(text=f'{self.ctx.prefix}help <command> to get command help.')
		embed.set_author(
			name=f'Page {menu.current_page + 1} of {self.get_max_pages()} ({self.count} categories)',
			icon_url=self.ctx.author.avatar_url_as(size=64)
		)
		embed.add_field(name='📰 News', value=open("news.md", "r").read())
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
				all_cmds = ', '.join(f'`{c.name}`' for c in cmds)
				if cog:
					cats.append([cog.name, f"> {all_cmds}\n"])

		await MyPages(MainHelp(self.context, cats), timeout=30.0).start(self.context)

	async def send_cog_help(self, cog: Cog):
		if not hasattr(cog, 'name'):
			pass
		entries = await self.filter_commands(cog.get_commands(), sort=True)
		await MyPages(
			GroupHelp(ctx := self.context, cog, entries, prefix=self.clean_prefix),
			clear_reactions_after=True,
			timeout=30.0
		).start(ctx)

	async def send_command_help(self, command):
		embed = self.context.bot.embed.default(
			self.context,
			title=self.get_command_signature(command),
			description=command.help or 'No help found...'
		)
		embed.set_footer(text=await self.get_ending_note())
		if aliases := command.aliases:
			embed.add_field(name='Aliases', value=' | '.join(aliases))
		if category := command.cog_name:
			embed.add_field(name='Category', value=category)
		await self.get_destination().send(embed=embed)

	async def send_group_help(self, group: commands.Group):
		if len(subcommands := group.commands) == 0:
			return await self.send_command_help(group)
		if len(cmds := await self.filter_commands(subcommands, sort=True)) == 0:
			return await self.send_command_help(group)
		source = GroupHelp(ctx=(ctx := self.context), group=group, cmds=cmds, prefix=self.clean_prefix)
		await MyPages(source, timeout=30.0).start(ctx)

	async def command_not_found(self, string):
		msg = f'Could not find the command `{string}`.'
		if dym := '\n'.join(get_close_matches(string, [i.name for i in self.context.bot.commands])):
			msg += f' Did you mean...\n{dym}'
		return msg

	def get_command_signature(self, command):
		return f'{self.clean_prefix}{command.qualified_name} {command.signature}'
