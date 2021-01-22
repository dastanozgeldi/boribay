import random
import re
import zipfile
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from PIL import Image
from utils.CustomCog import Cog
from utils.Manipulation import make_image, make_image_url


class Fun(Cog):
    '''Fun extension. Hope the name makes sense and commands correspond
    their parent.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '🎉 Fun'

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.guild)
    async def zipemojis(self, ctx, guild: Optional[discord.Guild]):
        guild = guild or ctx.guild
        buf = BytesIO()
        async with ctx.typing():
            with zipfile.ZipFile(buf, 'w') as f:
                for emoji in guild.emojis:
                    _bytes = await emoji.url.read()
                    f.writestr(f'{emoji.name}.{"gif" if emoji.animated else "png"}', _bytes)
            buf.seek(0)
        await ctx.reply('Sorry for being slow as hell but anyways:', file=discord.File(fp=buf, filename='emojis.zip'))

    @commands.command()
    async def caption(self, ctx, arg: Optional[str]):
        '''Caption for an image.
        This command describes a given image being just a piece of code.
        Can handle either image, member or even URL.
        Ex: **caption Dosek**'''
        image = await make_image_url(ctx, arg)
        cs = self.bot.session
        r = await cs.post(self.bot.config['API']['caption_api'], json={'Content': image, 'Type': 'CaptionRequest'})
        await ctx.send(embed=self.bot.embed(title=await r.text()).set_image(url=image))

    @commands.command(aliases=['5g1g', 'fivegoneg'])
    async def fiveguysonegirl(self, ctx, member: str, member2: Optional[str]):
        """Legendary '5 guys 1 girl meme maker.
        Example: **5g1g Dosek** — 5 guys = author pfp; 1 girl = member pfp.
        Args: member (discord.Member): a member you'd like to 5g1g.
        Raises: MissingRequiredArgument: if member is not specified."""
        async with ctx.timer:
            if member2:
                author = await make_image(ctx, member)
                member = await make_image(ctx, member2)
            else:
                author = await ctx.author.avatar_url_as(size=128).read()
                member = await make_image(ctx, member)
            buffer = BytesIO()
            with Image.open('./data/assets/5g1g.jpg') as img:
                img.paste(Image.open(BytesIO(member)), (500, 275))
                author_image = Image.open(BytesIO(author))
                for i in [(31, 120), (243, 53), (438, 85), (637, 90), (815, 20)]:
                    img.paste(author_image, i)
                img.save(buffer, 'png', optimize=True)
            buffer.seek(0)
            await ctx.send(file=discord.File(buffer, '5g1g.png'))

    @commands.command()
    async def qr(self, ctx, url: Optional[str]):
        '''Makes QR-code of a given URL.
        A great way to make your friends get rickrolled!
        P.S: this command accepts only URLs.'''
        url = await make_image_url(ctx, url)
        cs = self.bot.session
        r = await cs.get(self.bot.config['API']['qr_api'] + url)
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='qr.png'))

    @commands.command()
    async def eject(self, ctx, color: str.lower, is_impostor: bool, *, name: Optional[str]):
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
        r = await cs.get(f'{self.bot.config["API"]["screenshot_api"]}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @commands.command(aliases=['pp', 'penis'])
    async def peepee(self, ctx, member: discord.Member = None):
        """Basically, returns your PP size."""
        member = member or ctx.author
        random.seed(member.id)
        sz = 100 if member.id in self.bot.owner_ids else random.randint(1, 10)
        pp = f'8{"=" * sz}D'
        await ctx.send(f'{member.display_name}\'s pp size is:\n||{pp}||')

    @commands.command()
    async def fact(self, ctx):
        """Returns an useless fact."""
        cs = self.bot.session
        r = await cs.get('https://uselessfacts.jsph.pl/random.json?language=en')
        js = await r.json()
        await ctx.send(embed=self.bot.embed(description=js['text']))


def setup(bot):
    bot.add_cog(Fun(bot))
