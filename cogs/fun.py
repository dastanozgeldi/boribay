import re
import discord
import asyncio
import random
from time import time
from io import BytesIO
import textwrap
import json
from PIL import Image, ImageFont, ImageDraw

from discord.ext import commands
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🏓 Fun'

    @commands.command(aliases=['ss'], brief="see a screenshot of a given url.")
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send("Please leave a valid url!")
        cs = self.bot.session
        r = await cs.get(f'https://image.thum.io/get/width/1920/crop/675/maxAge/1/noanimate/{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @commands.command(aliases=['tr'], brief='typeracer command! compete with others using this.')
    async def typeracer(self, ctx):
        """Typeracer Command. Compete with others!
        Returns: Average WPM of the winner, time spent to type and original text."""
        cs = self.bot.session
        r = await cs.get('https://type.fit/api/quotes')
        buffer = BytesIO()
        quote = json.loads(await r.read())
        to_wrap = random.choice(quote)['text']
        wrapped_text = textwrap.wrap(to_wrap, 30)
        text = '\n'.join(wrapped_text)
        font = ImageFont.truetype('./data/fonts/monoid.ttf', size=30)
        w, h = font.getsize(text)
        with Image.new('RGB', (525, h * len(wrapped_text))) as base:
            canvas = ImageDraw.Draw(base)
            canvas.multiline_text((5, 5), text, font=font)
            base.save(buffer, 'png', optimize=True)
        buffer.seek(0)
        race = await ctx.send(
            file=discord.File(buffer, 'typeracer.png'),
            embed=Embed.default(
                ctx,
                title='Typeracer',
                description='see who is fastest at typing.'
            ).set_image(url='attachment://typeracer.png')
        )
        start = time()
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.content == to_wrap, timeout=60.0)
            if not msg:
                return
            end = time()
            final = round((end - start), 2)
            wpm = len(to_wrap.split()) * (60.0 / final)
            await ctx.send(embed=Embed(
                title=f'{msg.author.display_name} won!',
                description=f'**Done in**: {final}s\n**Average WPM**: {round(wpm)} words\n**Original text:**```diff\n+ {to_wrap}```',
            ))
        except asyncio.TimeoutError:
            try:
                await race.delete()
            except discord.errors.NotFound:
                pass

    @commands.command(name='rps', brief="the Rock | Paper | Scissors game.")
    async def rockpaperscissors(self, ctx):
        """The Rock | Paper | Scissors game.
        There are three different reactions, depending on your choice
        random will find did you win, lose or made draw."""
        rps_dict = {
            "🪨": {"🪨": "draw", "📄": "lose", "✂": "win"},
            "📄": {"🪨": "win", "📄": "draw", "✂": "lose"},
            "✂": {"🪨": "lose", "📄": "win", "✂": "draw"}
        }
        choice = random.choice([*rps_dict.keys()])
        msg = await ctx.send(embed=Embed(description="**Choose one 👇**").set_footer(text="10 seconds left⏰"))
        for r in rps_dict.keys():
            await msg.add_reaction(r)
        try:
            r, u = await self.bot.wait_for('reaction_add', timeout=10, check=lambda re, us: us == ctx.author and str(re) in rps_dict.keys() and re.message.id == msg.id)
            play = rps_dict.get(str(r.emoji))
            await msg.edit(embed=Embed(description=f'''Result: **{play[choice].upper()}**\nMy choice: **{choice}**\nYour choice: **{str(r.emoji)}**'''))
        except asyncio.TimeoutError:
            await msg.delete()


def setup(bot):
    bot.add_cog(Fun(bot))
