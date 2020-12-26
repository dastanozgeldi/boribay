from discord.ext import menus


class EmbedPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, embed):
        maximum = self.get_max_pages()
        embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
        return embed
