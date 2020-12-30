import functools
import os
import random
import re
import textwrap
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
from utils.Converters import BoolConverter, Degree
from utils.CustomCog import Cog
from utils.CustomContext import CustomContext
from utils.CustomEmbed import Embed
from utils.Manipulation import Manip, make_image
from utils.Paginators import EmbedPageSource, MyPages

load_dotenv()
URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


class Canvas(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🖼 Image Manipulation'
        self.ahb_cache = {}
        self.drake_cache = {}
        self.theory_cache = {}
        self.dagpi_token = os.getenv('dagpi_token')
        self.alex_token = os.getenv('alex_token')

    async def dagpi_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(f'https://api.dagpi.xyz/image/{url}', headers={'Authorization': self.dagpi_token})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'dagpi.png')
        return f

    async def alex_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(f'https://api.alexflipnote.dev/{url}', headers={'Authorization': self.alex_token})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'alex.png')
        return f

    @commands.command(aliases=['colours'], brief='see top 5 colors of your/user avatar.')
    async def colors(self, ctx, member: Optional[discord.Member]):
        """Colors of the avatar. Displays Top5 colors of a given image.
        Args: member (Optional[discord.Member]): member, which is either specified one or author."""
        member = member or ctx.author
        avatar = member.avatar_url_as(size=512)
        file = await self.dagpi_image(
            url=f'colors/?url={str(avatar)}',
            fn='colors.png'
        )
        await ctx.send(file=file)

    @commands.command(
        aliases=['ph'],
        brief='make a pornhub logo with text you want.'
    )
    async def pornhub(self, ctx, text_1: str, text_2: Optional[str]):
        '''Pornhub logo maker.
        No matter how long is text, API returns image perfectly (hope so).
        Ex: pornhub Bori bay.'''
        text_2 = text_2 or 'Hub'
        text_1 = text_1.replace(' ', '%20')
        text_2 = text_2.replace(' ', '%20')
        file = await self.alex_image(
            url=f'pornhub?text={text_1}&text2={text_2}',
            fn='ph.png'
        )
        await ctx.send(file=file)

    @commands.command(
        aliases=['dym'],
        brief='make a google search "did you mean" meme.'
    )
    async def didyoumean(self, ctx, search: str, did_you_mean: str):
        '''Google search 'Did you mean' meme.
        Arguments are required and raises an exception if one of them is misssing.
        Ex: didyoumean recursion recursion.'''
        file = await self.alex_image(
            url=f'didyoumean?top={search}&bottom={did_you_mean}',
            fn='dym.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="shows user's avatar")
    async def avatar(self, ctx, member: Optional[discord.Member]):
        '''Returns either author or member avatar if specified.
        Ex: avatar Dosek.'''
        async with ctx.timeit:
            member = member or ctx.author
            await ctx.send(str(member.avatar_url))

    @commands.command(brief="minecraft achievements maker")
    async def achieve(self, ctx, *, text):
        '''Minecraft 'Achievement Get!' image maker.
        Challenge icon is random one of 44.
        Ex: challenge slept more than 6 hours.'''
        text = text.replace(" ", "%20")
        file = await self.alex_image(
            url=f'achievement?text={text}&icon={random.randint(1, 44)}',
            fn='achieve.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="minecraft challenge complete")
    async def challenge(self, ctx, *, text):
        '''Minecraft 'Challenge Complete!' image maker.
        Challenge icon is random one of 45.
        Ex: challenge finished all to-do's.'''
        text = text.replace(" ", "%20")
        file = await self.alex_image(
            url=f'challenge?text={text}&icon={random.randint(1, 45)}',
            fn='challenge.png'
        )
        await ctx.send(file=file)

    @commands.command(name='qr')
    async def QR_code(self, ctx, url: str):
        '''Makes QR-code of a given URL.
        A great way to make your friends get rickrolled!
        P.S: this command accepts only URLs and raises an exception when it does not see URL.'''
        if not re.match(URL_REGEX, url):
            await ctx.send('Please provide a normal URL.')
        else:
            cs = self.bot.session
            r = await cs.get(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}")
            io = BytesIO(await r.read())
            await ctx.send(file=discord.File(fp=io, filename='qr.png'))

    @commands.command(brief="among us image!", description="among us ejecting image command")
    async def eject(self, ctx, color: str, is_impostor: BoolConverter, *, name: Optional[str]):
        '''Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: eject blue True Dosek.'''
        name = name or ctx.author.display_name
        cs = self.bot.session
        r = await cs.get(f'https://vacefron.nl/api/ejected?name={name}&impostor={is_impostor}&crewmate={color}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='ejected.png'))

    @commands.command(brief="trigger someone", aliases=['trigger'])
    async def triggered(self, ctx, member: Optional[discord.Member]):
        '''Makes "TRIGGERED" meme with an user avatar.
        Ex: triggered Dosek'''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'triggered/?url={member.avatar_url}',
            fn='triggered.gif'
        )
        await ctx.send(file=file)

    @commands.command(name='ascii', brief="cool hackerman filter")
    async def ascii_command(self, ctx, member: Optional[discord.Member]):
        '''Makes ASCII version of an user avatar.
        Ex: ascii Dosek'''
        member = member or ctx.author
        file = await self.dagpi_image(url=f'ascii/?url={member.avatar_url}')
        await ctx.send(file=file)

    @commands.command(name="discord", brief="generate realistic discord messages")
    async def _discord(self, ctx, member: discord.Member, *, text: str):
        '''Discord message maker.
        Returns an image with text and user avatar you specified.
        Ex: discord Dosek this command is cool ngl.'''
        file = await self.dagpi_image(
            url=f'discord/?url={member.avatar_url}&username={member.name}&text={text}',
            fn='discord.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="five guys with one girl meme", aliases=['wayg'])
    async def whyareyougay(self, ctx, member: Optional[discord.Member]):
        '''A legendary "Why are you gay?" meme maker.
        Member argument is optional, so if you call for a command
        without specifying a member you just wayg yourself.'''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'whyareyougay/?url={ctx.author.avatar_url}&url2={member.avatar_url}',
            fn='wayg.png'
        )
        await ctx.send(file=file)

    @commands.command(name='lyrics', aliases=['song', 'track', 'lyric'], brief='find almost every song lyrics with this command.')
    async def lyric_command(self, ctx, *, args: str):
        '''Powerful lyrics command.
        Ex: lyrics believer.
        Has no limits.
        You can find lyrics for song that you want.
        Raises an exception if song does not exist in API data.'''
        args = args.replace(' ', '%20')
        cs = self.bot.session
        r = await cs.get(f'https://some-random-api.ml/lyrics?title={args}')
        js = await r.json()
        try:
            song = str(js['lyrics'])
            song = textwrap.wrap(song, 1000, drop_whitespace=False, replace_whitespace=False)
            embed_list = []
            for lyrics in song:
                embed = Embed(
                    title=f'{js["author"]} — {js["title"]}',
                    description=lyrics
                ).set_thumbnail(url=js['thumbnail']['genius'])
                embed_list.append(embed)
            p = MyPages(source=EmbedPageSource(embed_list))
            await p.start(ctx)
        except KeyError:
            await ctx.send(f'Could not find lyrics for **{args}**')

    @commands.command(aliases=['ft'])
    async def facetime(self, ctx: CustomContext, image: str):
        """Facetime Call Maker.
        Args: image (str): whatever you want to make the image of."""
        async with ctx.timeit:
            author_image = await ctx.author.avatar_url_as(static_format='png', size=512).read()
            image = await make_image(ctx, image)
            f = functools.partial(Manip.facetime, image, author_image)
            image_bytes = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(image_bytes, filename='facetime.png'))

    @commands.command(hidden=True)
    async def swirl(self, ctx: CustomContext, image: Optional[str], degrees: Degree = 90):
        """Swirl Image.
        Example: **swirl Dosek 270**
        Args: image (str, optional): either user, image or url.
            degrees (int, optional): number of degrees you want to swirl image. Defaults to 90.
        Raises: BadArgument if image is too large."""
        async with ctx.timeit:
            image = await make_image(ctx, image)
            buffer = BytesIO(image)

            f = functools.partial(Manip.swirl, buffer, degrees)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='swirl.png'))

    @commands.command(hidden=True)
    async def ahb(self, ctx, *, text: commands.clean_content = 'am I a fool who didn\'t enter the text?'):
        """Always Has Been meme maker.
        Args: text (str, optional): Text you want to see in the image. Defaults to None.
        Example: **ahb wait it's all Ohio?**
        Raises: BadArgument if image is too large."""
        async with ctx.timeit:
            try:
                cached = self.ahb_cache[text]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='ahb.png'))
            except KeyError:
                if len(text) > 50:
                    return await ctx.send(f'The text was too long ({len(text)}')

                f = functools.partial(Manip.alwayshasbeen, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.ahb_cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='ahb.png'))

    @commands.command(brief='create a legendary Drake meme.')
    async def drake(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
        yes (str): argument for 'yes' side of image."""
        async with ctx.timeit:
            try:
                cached = self.drake_cache[no]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='drake.png'))

            except KeyError:
                if len(yes) > 90 or len(no) > 90:
                    return await ctx.send('The text was too long to render.')

                f = functools.partial(Manip.drake, no, yes)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.drake_cache[no] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='drake.png'))

    @commands.command(aliases=['lisa'])
    async def theory(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board.
        Raises: Exception when text > 144 symbols."""
        async with ctx.timeit:
            try:
                cached = self.theory_cache[text]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='theory.png'))

            except KeyError:
                if len(text) > 144:
                    return await ctx.send('The text was too long to render.')

                f = functools.partial(Manip.theory, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.theory_cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='theory.png'))

    @commands.command(
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
    bot.add_cog(Canvas(bot))
