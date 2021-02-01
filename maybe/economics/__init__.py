from discord.ext import commands
from utils.Cog import Cog
# well, I must create a new table especially for this cog.
# seems more to create the general table for both, leveling and economics.


class Economics(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '💲 Economics'

    @commands.command()
    async def balance(self, ctx):
        pass

    @commands.command()
    async def pay(self, ctx):
        pass

    @commands.command()
    async def rob(self, ctx):
        pass

    @commands.command()
    async def work(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Economics(bot))
