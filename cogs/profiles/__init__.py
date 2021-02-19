import discord
from utils.Cog import Cog
from discord.ext import commands


class Profiles(Cog):
    icon = '🎚'
    name = 'Leveling'

    def __init__(self, bot):
        self.bot = bot

    async def make_rank(self, ctx):
        """Rank card maker function layout.
        TODO use PIL to manipulate with images,
        maybe use background features."""
        pass

    @commands.command(aliases=['card', 'xp'])
    async def rank(self, ctx, member: discord.Member):
        """I'll leave it here for a while.
        TODO log database in here to make ranking system"""
        a = ctx.author  # idk why am i doing this
        await ctx.send(f'https://vacefron.nl/api/rankcard?username={a.display_name}&avatar={a.avatar_url}&currentxp=2001&nextlevelxp=2250&previouslevelxp=1750&level=8&rank=1&circleavatar=true')

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx):  # Maybe add support to show another guilds.
        pass

    @commands.command(aliases=['global'])
    async def globe(self, ctx):
        """No matter what guild are users from.
        Imma do DESC according to the xp."""
        pass

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
    bot.add_cog(Profiles(bot))
