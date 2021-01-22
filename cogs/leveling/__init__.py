import discord
from utils.CustomCog import Cog
from discord.ext import commands


class Leveling(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🎚 Leveling'

    async def make_rank(self, ctx):
        """Rank card maker function layout.
        TODO use PIL to manipulate with images,
        maybe use background features."""
        pass

    @commands.command(aliases=['card', 'xp'])
    async def rank(self, ctx, member: discord.Member):
        """I'll leave it here for a while.
        TODO log database in here to make ranking system"""
        pass

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx):  # Maybe add support to show another guilds.
        pass

    @commands.command(name='global', aliases=['glob'])
    async def _global(self, ctx):
        """No matter what guild are users from.
        Imma do DESC according to the xp."""
        pass


def setup(bot):
    bot.add_cog(Leveling(bot))
