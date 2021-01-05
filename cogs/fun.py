import os
import re
import discord
import asyncio
import random
from io import BytesIO
from discord.ext import commands
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🎉 Fun'

    @commands.command(aliases=['ss'], brief="see a screenshot of a given url.")
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send("Please leave a valid url!")
        cs = self.bot.session
        r = await cs.get(f'{os.getenv("screenshoter")}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @commands.command(aliases=['pp', 'peepee'])
    async def penis(self, ctx, member: discord.Member = None):
        """Basically, returns your PP size."""
        member = member or ctx.author
        random.seed(member.id)
        sz = 100 if member.id in self.bot.owner_ids else random.randint(1, 10)
        pp = f'8{"=" * sz}D'
        await ctx.send(f'{member.display_name}\'s pp size is: {pp}')

    @commands.command()
    async def fact(self, ctx):
        """Returns an useless fact."""
        cs = self.bot.session
        r = await cs.get('https://uselessfacts.jsph.pl/random.json?language=en')
        js = await r.json()
        await ctx.send(embed=Embed(description=js['text']))


def setup(bot):
    bot.add_cog(Fun(bot))
