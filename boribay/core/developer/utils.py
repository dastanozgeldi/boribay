from discord.ext import menus

from boribay.core import utils


class IdeaPageSource(menus.ListPageSource):
    """IdeaPageSource, a special paginator created for the idea commands parent.

    Takes the list of data, enumerates, then paginates through.
    """

    def __init__(self, ctx: utils.Context, data: list):
        super().__init__(data, per_page=10)
        self.ctx = ctx

    def _format_content(self, entry: str):
        content = entry["content"]
        author = self.ctx.bot.get_user(entry["author_id"]) or entry["author_id"]
        return f"{content[:50] if len(content) > 50 else content} ~ {author}"

    async def format_page(self, menu, entries):
        embed = self.ctx.embed(
            description="\n".join(
                f'{x["id"]}. {self._format_content(x)}' for x in entries
            )
        ).set_author(
            name=f"Page {menu.current_page + 1} of {self.get_max_pages()} ({len(self.entries)} suggestions).",
            icon_url=self.ctx.author.avatar,
        )

        return embed
