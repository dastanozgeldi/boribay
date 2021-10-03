from contextlib import suppress

import nextcord
from nextcord.ext import menus


class Paginate(menus.MenuPages):
    """My own paginator implementation.

    Subclasses menus.MenuPages. Takes page-source as a main parameter.

    Tries to delete a message when timeout comes, returns if any exceptions.
    """

    def __init__(self, source, **kwargs):
        super().__init__(source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out: bool):
        with suppress(nextcord.HTTPException):
            if timed_out:
                return await self.message.clear_reactions()

            await self.message.delete()


class EmbedPageSource(menus.ListPageSource):
    """EmbedPageSource, a paginator that takes a list of embeds."""

    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, embed):
        maximum = self.get_max_pages()
        embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
        return embed
