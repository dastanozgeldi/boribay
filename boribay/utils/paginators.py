from contextlib import suppress

from discord import HTTPException
from discord.ext import menus


class MyPages(menus.MenuPages):
    """My own paginator implementation.
    Subclasses menus.MenuPages. Takes page-source as a main parameter.
    Tries to delete a message when timeout comes, returns if any exceptions."""

    def __init__(self, source, **kwargs):
        super().__init__(source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out):
        with suppress(HTTPException):
            if timed_out:
                return await self.message.clear_reactions()

            await self.message.delete()


class TodoPageSource(menus.ListPageSource):
    """TodoPageSource, a special paginator created for the todo commands parent.
    Takes the list of data, enumerates, then paginates through."""

    def __init__(self, ctx, data):
        super().__init__(data, per_page=10)
        self.ctx = ctx

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = self.ctx.embed()

        if len(entries) < 1:
            embed.description = 'Currently, you have no to-do\'s.\n'
            'To set them use **todo add** command.'

        else:
            maximum = self.get_max_pages()
            embed.set_author(
                name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} todos)',
                icon_url=self.ctx.author.avatar_url
            )
            embed.description = '\n'.join(f'[{i}]({v[1]}). {v[0]}' for i, v in enumerate(entries, start=offset))

        return embed


class EmbedPageSource(menus.ListPageSource):
    """EmbedPageSource, a paginator that takes a list of embeds."""

    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, embed):
        maximum = self.get_max_pages()
        embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
        return embed
