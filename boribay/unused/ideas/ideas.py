from boribay.core import Boribay, Cog, Context
from discord.ext import commands, flags


class Ideas(Cog):
    """TODO: create the table 'Suggestions' where:
    ID: pkey of the suggestion.
    Content: the content of suggestion, TEXT.
    Approved: is the suggestion approved, BOOLEAN.
    Added: when the suggestion was added, timestamp without time zone."""

    def __init__(self, bot: Boribay):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def idea(self, ctx: Context):
        ...

    @idea.command()
    async def suggest(self, ctx: Context, *, suggestion: str):
        ...

    @idea.command()
    @commands.is_owner()
    async def approve(self, ctx: Context, id: commands.Greedy[int]):
        # TODO on approving, set the column approved to 'true'.
        ...

    @idea.command()
    @commands.is_owner()
    async def reject(self, ctx: Context, id: commands.Greedy[int]):
        # TODO on rejecting, delete the rejected suggestions.
        ...

    @flags.add_flag('--approved', action='store_true',
                    help='Whether to list only approved suggestions.')
    @flags.add_flag('--limit', type=int, help='Set the limit of ')
    @flags.command(cls=flags.FlagCommand)
    @commands.is_owner()
    async def pending(self, ctx: Context):
        # TODO paginate all suggestions that aren't approved yet by default.
        # If --approved flag was specified, accordingly show them.
        ...

    @idea.command()
    @commands.is_owner()
    async def info(self, ctx: Context, id: int):
        ...


def setup(bot: Boribay):
    bot.add_cog(Ideas(bot))
