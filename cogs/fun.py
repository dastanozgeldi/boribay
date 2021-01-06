import os
import re
import discord
import random
import functools
from io import BytesIO
from typing import Optional
from PIL import Image
from utils.Manipulation import Manip, make_image
from utils.Converters import BoolConverter
from discord.ext import commands
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🎉 Fun'
        self.asset = './data/assets/'
        self.image = './data/images/'
        self.font = './data/fonts/'
        self.URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    @commands.command(name='f')
    async def press_f(self, ctx, image: Optional[str]):
        """'Press F to pay respect' meme maker. F your mate using this command.
        Args: image (optional): Image that you want to see on the canvas."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            buffer = BytesIO(image)
            f = functools.partial(Manip.press_f, buffer)
            buffer = await self.bot.loop.run_in_executor(None, f)
            msg = await ctx.send(file=discord.File(fp=buffer, filename='f.png'))
            await msg.add_reaction('<:press_f:796264575065653248>')

    @commands.command(aliases=['5g1g', 'fivegoneg'])
    async def fiveguysonegirl(self, ctx, member: Optional[str], member2: Optional[str]):
        """Legendary '5 guys 1 girl meme maker.
        Example: **5g1g Dosek** — 5 guys = author pfp; 1 girl = member pfp.
        Args: member (discord.Member): a member you'd like to 5g1g.
        Raises: MissingRequiredArgument: if member is not specified."""
        async with ctx.timer:
            if member2:
                author = await make_image(ctx, member)
                member = await make_image(ctx, member2)
            else:
                author = ctx.author.avatar_url_as(size=128)
                author = await author.read()
                member = await make_image(ctx, member)
            a_data = BytesIO(author)
            m_data = BytesIO(member)
            img = Image.open(f'{self.asset}5g1g.png')
            a_pfp = Image.open(a_data).resize((128, 128))
            m_pfp = Image.open(m_data).resize((105, 105))
            img.paste(m_pfp, (504, 279))
            for i in [(31, 120), (243, 53), (438, 85), (637, 90), (815, 20)]:
                img.paste(a_pfp, i)
            img.save(f'{self.image}5g1g.png', optimize=True)
            await ctx.send(file=discord.File(f'{self.image}5g1g.png'))

    @commands.command()
    async def qr(self, ctx, url: Optional[str]):
        '''Makes QR-code of a given URL.
        A great way to make your friends get rickrolled!
        P.S: this command accepts only URLs and raises an exception when it does not see URL.'''
        if re.match(self.URL_REGEX, url):
            url
        else:
            return await ctx.send('Please, specify a valid URL.')
        cs = self.bot.session
        r = await cs.get(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}")
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='qr.png'))

    @commands.command()
    async def swirl(self, ctx, image: Optional[str], degrees: Optional[int]):
        """Swirl an image.
        Args: image (str): image that you specify. it's either member/emoji/url.
        it swirls your avatar if argument is not passed.
        degrees (int): this is basically how much do you want to swirl an image.
        takes random values if argument is not passed."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            degrees = random.randint(-360, 360) if degrees is None else degrees
            buffer = BytesIO(image)
            f = functools.partial(Manip.swirl, buffer, degrees)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='swirl.png'))

    @commands.command()
    async def eject(self, ctx, color: str, is_impostor: BoolConverter, *, name: Optional[str]):
        '''Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: eject blue True Dosek.'''
        name = name or ctx.author.display_name
        cs = self.bot.session
        r = await cs.get(f'https://vacefron.nl/api/ejected?name={name}&impostor={is_impostor}&crewmate={color}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='ejected.png'))

    @commands.command(aliases=['ss'])
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send("Please leave a valid url!")
        cs = self.bot.session
        r = await cs.get(f'{os.getenv("screenshoter")}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @commands.command(aliases=['pp', 'penis'])
    async def peepee(self, ctx, member: discord.Member = None):
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
