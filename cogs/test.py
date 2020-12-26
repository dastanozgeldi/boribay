import asyncio
import functools
import json
import random
import re
import textwrap
import typing
from io import BytesIO
from time import time

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, Cog, command
from PIL import Image, ImageDraw, ImageFont
from utils.CustomEmbed import Embed
from wand.image import Image as WI
from wand.color import Color


class ImageOrMember(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            member_converter = commands.MemberConverter()
            member = await member_converter.convert(ctx, argument)

            asset = member.avatar_url_as(static_format="png", format="png", size=512)
            image = await asset.read()

            return image

        except (commands.MemberNotFound, TypeError):

            try:
                url_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
                emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"

                if re.match(url_regex, argument):
                    async with ctx.bot.session.get(argument) as response:
                        image = await response.read()
                        return image

                elif re.match(emoji_regex, argument):
                    emoji_converter = commands.EmojiConverter()
                    emoji = await emoji_converter.convert(ctx, argument)

                    asset = emoji.url
                    image = await asset.read()
                    return image

            except TypeError:
                return None

        return None


async def get_image(ctx: commands.Context, argument: str):
    converter = ImageOrMember()
    image = await converter.convert(ctx, argument)
    if not image:
        if ctx.message.attachments:
            asset = ctx.message.attachments[0]
            image = await asset.read()
            return image
        else:
            asset = ctx.author.avatar_url_as(static_format='png', format='png', size=512)
            image = await asset.read()
            return image
    else:
        return image


class Manipulation:

    @staticmethod
    def floor(image: BytesIO):
        with WI(file=image) as img:
            if (img.width * img.height) >= (1200 * 1000):
                raise commands.BadArgument('Too large image.')

            img.resize(256, 256)
            img.matte_color = Color('BLACK')
            img.virtual_pixel = 'tile'
            args = (0, 0, 77, 153,
                    img.height, 0, 179, 153,
                    0, img.width, 51, 255,
                    img.height, img.width, 204, 255)
            img.distort('perspective', args)
            buffer = BytesIO()
            img.save(file=buffer, optimize=True)
        buffer.seek(0)
        return buffer

    @staticmethod
    def swirl(image: BytesIO, degrees: int = 90):
        with WI(file=image) as img:
            if(img.width * img.height) >= (1200 * 1000):
                raise commands.BadArgument(
                    'Too large image.'
                )
            if degrees > 360:
                degrees = 360
            elif degrees < -360:
                degrees = -360
            else:
                degrees = degrees

            img.swirl(degree=degrees)
            buffer = BytesIO()
            img.save(file=buffer, optimize=True)
        buffer.seek(0)
        return buffer

    @staticmethod
    def theory(txt: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open('./assets/lisa.jpg') as img:
            wrapped = textwrap.wrap(txt, 24)
            font = ImageFont.truetype('./fonts/impact.ttf', 30)
            draw = ImageDraw.Draw(img)
            draw.text((161, 72), '\n'.join(wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)
        buffer.seek(0)
        return buffer

    @staticmethod
    def alwayshasbeen(txt: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open("./assets/ahb.jpg") as img:
            wrapped = textwrap.wrap(txt, 20)

            set_back = sum(12 for char in txt) if len(wrapped) == 1 else sum(6 for char in txt)
            up_amount = sum(35 for newline in wrapped)
            coords = (700 - set_back, 300 - up_amount)

            font = ImageFont.truetype("./fonts/monoid.ttf", 48)
            draw = ImageDraw.Draw(img)

            draw.text(coords, "\n".join(wrapped), (255, 255, 255), font=font)

            buffer = BytesIO()
            img.save(buffer, "png", optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    def drake(no: str, yes: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open('./assets/drake.jpg') as img:
            no_wrapped = textwrap.wrap(text=no, width=13)
            yes_wrapped = textwrap.wrap(text=yes, width=13)
            font = ImageFont.truetype('./fonts/impact.ttf', size=28)
            draw = ImageDraw.Draw(img)
            draw.text((275, 10), '\n'.join(no_wrapped), (0, 0, 0), font=font)
            draw.text((275, 267), '\n'.join(yes_wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer


class ImageTest(Cog, name='Testing', command_attrs=dict(cooldown=commands.Cooldown(1, 10, BucketType.channel))):
    def __init__(self, bot):
        self.bot = bot
        self.ahb_cache = {}
        self.drake_cache = {}
        self.theory_cache = {}
        self.asset = './assets/'
        self.image = './images/'
        self.font = './fonts/'

    @command(hidden=True)
    async def floor(self, ctx: commands.Context, what=None):
        """Floor of Images.
        Example: **floor Dosek**
        Args: what (str, optional): either user, image or url. Defaults to None.
        Raises: BadArgument if image is too large.
        """
        async with ctx.timeit:
            async with ctx.typing():
                image = await get_image(ctx, what)
                buffer = BytesIO(image)

                func = functools.partial(Manipulation.floor, buffer)
                buffer = await self.bot.loop.run_in_executor(None, func)

                embed = Embed.default(ctx)
                f = discord.File(fp=buffer, filename='floor.png')
                embed.set_image(url='attachment://floor.png')
                await ctx.send(file=f, embed=embed)

    @command(hidden=True)
    async def swirl(self, ctx: commands.Context, what: typing.Optional[str], degrees: int = 90):
        """Swirl Image.
        Example: **swirl Dosek 270**
        Args: what (str, optional): either user, image or url.
            degrees (int, optional): number of degrees you want to swirl image. Defaults to 90.
        Raises: BadArgument if image is too large.
        """
        async with ctx.timeit:
            async with ctx.typing():
                image = await get_image(ctx, what)
                buffer = BytesIO(image)

                func = functools.partial(Manipulation.swirl, buffer, degrees)
                buffer = await self.bot.loop.run_in_executor(None, func)

                embed = Embed.default(ctx)
                f = discord.File(fp=buffer, filename='swirl.png')
                embed.set_image(url='attachment://swirl.png')

                await ctx.send(file=f, embed=embed)

    @command(hidden=True)
    async def ahb(self, ctx, *, text: commands.clean_content = None):
        """Always Has Been meme maker.
        Args: text (str, optional): Text you want to see in the image. Defaults to None.
        Example: **ahb wait it's all Ohio?**
        Raises: BadArgument if image is too large.
        """
        if not text:
            text = 'was I the fool who didn\'t enter the text?'
        async with ctx.timeit:
            async with ctx.typing():
                try:
                    cached = self.ahb_cache[text]
                    cached.seek(0)
                    embed = Embed.default(ctx)

                    f = discord.File(fp=cached, filename='ahb.png')
                    embed.set_image(url='attachment://ahb.png')

                    await ctx.send(file=f, embed=embed)
                except KeyError:
                    if len(text) > 50:
                        return await ctx.send(f'The text was too long ({len(text)})')

                    func = functools.partial(Manipulation.alwayshasbeen, text)
                    buffer = await self.bot.loop.run_in_executor(None, func)

                    self.ahb_cache[text] = buffer

                    embed = Embed.default(ctx)
                    f = discord.File(fp=buffer, filename='ahb.png')
                    embed.set_image(url='attachment://ahb.png')
                    await ctx.send(file=f, embed=embed)

    @command(name='drake', brief='create a legendary Drake meme.')
    async def drake_image(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
            yes (str): argument for 'yes' side of image
        """
        async with ctx.timeit:
            async with ctx.typing():
                try:
                    cached = self.drake_cache[no]
                    cached.seek(0)
                    embed = Embed.default(ctx)

                    f = discord.File(fp=cached, filename='drake.png')
                    embed.set_image(url='attachment://drake.png')
                    await ctx.send(file=f, embed=embed)
                except KeyError:
                    if len(yes) > 90 or len(no) > 90:
                        return await ctx.send('The text was too long to render.')

                    func = functools.partial(Manipulation.drake, no, yes)
                    buffer = await self.bot.loop.run_in_executor(None, func)
                    self.drake_cache[no] = buffer

                    embed = Embed.default(ctx)
                    f = discord.File(fp=buffer, filename='drake.png')
                    await ctx.send(file=f, embed=embed)

    @command(
        name='theory',
        brief='idk how to name that but you can make a text on the board ok?',
        aliases=['lisa']
    )
    async def lisa_board(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board.
        Raises: Exception when text > 144 symbols.
        """
        async with ctx.timeit:
            async with ctx.typing():
                try:
                    cached = self.theory_cache[text]
                    cached.seek(0)
                    embed = Embed.default(ctx)
                    f = discord.File(fp=cached, filename='theory.png')
                    embed.set_image(url='attachment://theory.png')
                    await ctx.send(file=f, embed=embed)

                except KeyError:
                    if len(text) > 144:
                        return await ctx.send('The text was too long to render.')

                    func = functools.partial(Manipulation.theory, text)
                    buffer = await self.bot.loop.run_in_executor(None, func)
                    self.theory_cache[text] = buffer
                    embed = Embed.default(ctx)
                    f = discord.File(fp=buffer, filename='theory.png')
                    await ctx.send(file=f, embed=embed)

    @command(
        name='typeracer',
        aliases=['tr'],
        brief='compete with others using this typeracer command.'
    )
    async def typeracer_image(self, ctx):
        """Typeracer in Discord (60 seconds)!
        Returns: Average WPM: formula (word * (60 / time))
            Time the winner was typing.
        Raises: TimeoutError: if no time left.
        """
        cs = self.bot.session
        quote = await cs.get('https://type.fit/api/quotes')
        quote = json.loads(await quote.read())
        to_wrap = random.choice(quote)['text']
        text = textwrap.wrap(text=to_wrap, width=28)
        font = ImageFont.truetype(f'{self.font}monoid.ttf', size=30)
        image = Image.open(f'{self.asset}black_bg.jpg')
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), '\n'.join(text), (255, 255, 255), font=font)
        image.save(f'{self.image}typeracer.png', optimize=True)

        f = discord.File(f'{self.image}typeracer.png')
        race = await ctx.send(file=f, embed=Embed(
            title='Typeracer', description='see who is fastest at typing.'
        ).set_image(url='attachment://typeracer.png'))
        start = time()

        await self.bot.add_delete_reaction(ctx, ctx.channel.id, race.id)

        def check(message):
            return message.content == to_wrap
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
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

    @command(
        name='5g1g',
        brief='[BETA] make a meme "5 guys one girl" with someone\'s avatar.'
    )
    async def make_5g1g_meme(self, ctx, member: discord.Member):
        """Legendary '5 guys 1 girl meme maker.
        Example: **5g1g Dosek** — 5 guys = author pfp; 1 girl = member pfp.
        Args: member (discord.Member): a member you'd like to 5g1g.
        Raises: MissingRequiredArgument: if member is not specified.
        """
        img = Image.open(f'{self.asset}5g1g.png')
        author = ctx.author.avatar_url_as(size=128)
        member = member.avatar_url_as(size=128)
        author_data = BytesIO(await author.read())
        author_pfp = Image.open(author_data)
        author_dir = [(31, 120), (243, 53), (438, 85), (637, 90), (815, 20)]

        member_data = BytesIO(await member.read())
        member_pfp = Image.open(member_data)
        member_pfp = member_pfp.resize((105, 105))
        img.paste(member_pfp, (504, 279))
        for i in author_dir:
            img.paste(author_pfp, i)

        img.save(f'{self.image}success.png', optimize=True)
        await ctx.send(file=discord.File(f'{self.image}success.png'))


def setup(bot):
    bot.add_cog(ImageTest(bot))
