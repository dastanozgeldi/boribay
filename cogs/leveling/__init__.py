from discord.ext import commands
from utils.CustomCog import Cog


class Leveling(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🎚 Leveling'

    async def make_rank(self, ctx):
        """Rank card maker function layout.
        TODO use PIL to manipulate with images, maybe use background features."""
        pass

    @commands.command()
    async def rank(self, ctx):
        """I'll leave it here for a while. TODO log database in here to make ranking system"""
        pass


def setup(bot):
    bot.add_cog(Leveling(bot))
