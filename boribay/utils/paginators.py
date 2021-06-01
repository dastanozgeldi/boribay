import re
from contextlib import suppress

import discord
from boribay.core import constants
from discord.ext import menus


class Paginate(menus.MenuPages):
    """My own paginator implementation.
    Subclasses menus.MenuPages. Takes page-source as a main parameter.
    Tries to delete a message when timeout comes, returns if any exceptions.
    """

    def __init__(self, source, **kwargs):
        super().__init__(source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out):
        with suppress(discord.HTTPException):
            if timed_out:
                return await self.message.clear_reactions()

            await self.message.delete()


class IdeaPageSource(menus.ListPageSource):
    """IdeaPageSource, a special paginator created for the idea commands parent.

    Takes the list of data, enumerates, then paginates through.
    """

    def __init__(self, ctx, data: list):
        super().__init__(data, per_page=10)
        self.ctx = ctx

    def _format_content(self, entry: str):
        content = entry['content']
        author = self.ctx.bot.get_user(entry['author_id']) or entry['author_id']
        return f'{content[:50] if len(content) > 50 else content} ~ {author}'

    async def format_page(self, menu, entries):
        embed = self.ctx.embed(
            description='\n'.join(f'{x["id"]}. {self._format_content(x)}' for x in entries)
        ).set_author(
            name=f'Page {menu.current_page + 1} of {self.get_max_pages()} ({len(self.entries)} suggestions).',
            icon_url=self.ctx.author.avatar_url
        )

        return embed


class UrbanDictionaryPageSource(menus.ListPageSource):
    """A special paginator created for the command called `urbandictionary`.

    Takes the list of data, does formatting, then paginates through.
    """

    def __init__(self, ctx, entries, *, per_page: int = 1):
        super().__init__(entries=entries, per_page=per_page)
        self.ctx = ctx

    @staticmethod
    def cleanup(definition: str, *, limit: int) -> str:
        """A method created to clean the urban dictionary definition up.

        Parameters
        ----------
        definition : str
            The definition we have to parse.

        Returns
        -------
        str
            Formatted string we are able to use in embed.
        """
        brackets = re.compile(r'(\[(.+?)\])')

        def func(m):  # idk how to name this.
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        if len(ret := brackets.sub(func, definition)) >= limit:
            return ret[0:2000] + ' [...]'

        return ret

    async def format_page(self, menu, entry) -> discord.Embed:
        mx = self.get_max_pages()

        embed = self.ctx.embed(
            description=self.cleanup(entry['definition'], limit=2048),
        ).set_footer(text=f'by {entry["author"]}')

        embed.set_author(
            name=f'{entry["word"]} ({menu.current_page + 1} of {mx})' if mx else entry['word'],
            url=entry['permalink'],
            icon_url=constants.URBAN_DICTIONARY_ICON_URL
        )

        embed.add_field(
            name='Example:',
            # Examples can be not given (null) so we should handle this.
            value=self.cleanup(entry['example'], limit=1024) or 'No examples given.',
            inline=False  # We don't really need this.
        )

        with suppress(KeyError):
            up, down = entry['thumbs_up'], entry['thumbs_down']

        embed.add_field(name='Votes:', value=f'👍 {up} | 👎 {down}', inline=False)

        with suppress(KeyError, ValueError):
            date = discord.utils.parse_time(entry['written_on'][0:-1])

        embed.timestamp = date
        return embed


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
