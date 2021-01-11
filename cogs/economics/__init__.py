from discord.ext import commands
from utils.CustomCog import Cog


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


def setup(bot):
    bot.add_cog(Economics(bot))