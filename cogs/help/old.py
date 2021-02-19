from discord.ext import commands, menus
from utils.Paginators import MyPages


class MainHelp(menus.ListPageSource):
    '''Creates an embedded message including all commands (if not hidden).'''

    def __init__(self, ctx, categories: list):
        super().__init__(entries=categories, per_page=3)
        self.ctx = ctx
        self.count = len(categories)

    async def format_page(self, menu, entries):
        links = self.ctx.bot.config['links']
        embed = self.ctx.bot.embed.default(
            self.ctx,
            description=f'{self.ctx.prefix}help [Category | group] to get module help\n'
            f'[Invite]({links["invite_url"]}) | [Support]({links["support_url"]}) | [Source]({links["github_url"]}) | [Vote]({links["topgg_url"]})'
        ).set_footer(text=f'{self.ctx.prefix}help <command> to get command help.')
        embed.set_author(
            name=f'Page {menu.current_page + 1} of {self.get_max_pages()} ({self.count} categories)',
            icon_url=self.ctx.author.avatar_url_as(size=64)
        )
        news = open('news.md', 'r').readlines()
        embed.add_field(name=f'📰 News - {news[0]}', value=''.join(news[1:]))
        for name, value in entries:
            embed.add_field(name=name, value=value, inline=False)
        return embed


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        cats = []
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                all_cmds = ' → '.join(f'`{c.name}`' for c in cmds)
                if cog:
                    cats.append([str(cog), f'> {all_cmds}\n'])
        await MyPages(MainHelp(self.context, cats)).start(self.context)
