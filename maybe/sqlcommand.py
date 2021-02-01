from discord.ext import commands
from .paginators import SQLListPageSource
from utils.Paginators import MyPages
from jishaku.codeblocks import codeblock_converter


@commands.command()
async def sql(ctx, *, query: codeblock_converter):
    """Does an SQL query."""
    query = query.content
    data = []
    for result in (await ctx.bot.pool.fetch(query) if query.lower().startswith('select') else await ctx.bot.pool.execute(query)):
        data.append(repr(result))
    await MyPages(SQLListPageSource(ctx, data)).start(ctx)
