import re
from contextlib import suppress
from typing import Any, List, Tuple

import discord
from boribay.core.constants import URBAN_DICTIONARY_ICON_URL
from boribay.core.context import Context
from boribay.core.exceptions import UserError
from discord.ext import menus


class OptionsNotInRange(UserError):
    """Raised when there were more than 10 options on a poll."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return 'Please keep poll options range (min 2 : max 10).'


class Poll:
    def __init__(self, ctx: Context, options: List[str], **kwargs: Any):
        self.ctx = ctx
        self.options = options
        self.embed = ctx.embed(**kwargs)

    def get_reactions(self) -> Tuple[str]:
        """A user may ask for a "yes/no" poll.

        In this case we are trying to determine what reactions to add below.

        Returns
        -------
        Tuple[str]
            A tuple of reactions to add below the poll in the future.
        """
        if len(self.options) == 2 and ('y', 'n') == tuple(map(str.lower, self.options)):
            return (
                '<:thumbs_up:746352051717406740>',
                '<:thumbs_down:746352095510265881>'
            )

        return (
            '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
        )

    async def start(self) -> None:
        ctx = self.ctx
        opt = len(self.options)
        reactions = self.get_reactions()

        if not 2 <= opt <= 10:
            raise OptionsNotInRange

        # Adding reactions on an embed field.
        self.embed.add_field(
            name='📊 Options',
            value='\n'.join(
                f'{reactions[x]} {option}' for x, option in enumerate(self.options)
            )
        )

        # Attempting to delete a message sent by user.
        await ctx.try_delete(ctx.message)
        message = await ctx.send(embed=self.embed)

        # Adding some real reactions.
        for emoji in reactions[:opt]:
            await message.add_reaction(emoji)


class TodoPageSource(menus.ListPageSource):
    """TodoPageSource, a special paginator created for the todo commands parent.
    Takes the list of data, enumerates, then paginates through."""

    def __init__(self, ctx: Context, data):
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


class UrbanDictionaryPageSource(menus.ListPageSource):
    """A special paginator created for the command called `urbandictionary`.

    Takes the list of data, does formatting, then paginates through.
    """

    def __init__(self, ctx: Context, entries, *, per_page: int = 1):
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
            icon_url=URBAN_DICTIONARY_ICON_URL
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
