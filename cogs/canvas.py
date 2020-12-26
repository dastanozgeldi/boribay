import os
import random
import re
import textwrap
from io import BytesIO

import discord
from typing import Optional
from discord.ext import commands
from utils.CustomEmbed import Embed
from dotenv import load_dotenv
from utils.EmbedPagination import EmbedPageSource
from utils.HelpCommand import MyPages

load_dotenv()
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


class Canvas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dagpi_token = os.getenv('dagpi_token')
        self.alex_token = os.getenv('alex_token')

    async def dagpi_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(url, headers={'Authorization': self.dagpi_token})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'dagpi.png')
        return f

    async def alex_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(url, headers={'Authorization': self.alex_token})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'alex.png')
        return f

    @commands.command(
        aliases=['ph'],
        brief='make a pornhub logo with text you want.'
    )
    async def pornhub(self, ctx, text_1: str, text_2: Optional[str]):
        '''
        Pornhub logo maker.
        No matter how long is text, API returns image perfectly (hope so).
        Ex: pornhub Bori bay.
        '''
        text_2 = text_2 or 'Hub'
        text_1 = text_1.replace(' ', '+')
        text_2 = text_2.replace(' ', '+')
        file = await self.alex_image(
            url=f'https://api.alexflipnote.dev/pornhub?text={text_1}&text2={text_2}',
            fn='ph.png'
        )
        await ctx.send(file=file)

    @commands.command(
        aliases=['dym'],
        brief='make a google search "did you mean" meme.'
    )
    async def didyoumean(self, ctx, search: str, did_you_mean: str):
        '''
        Google search 'Did you mean' meme.
        Arguments are required and raises an exception if one of them is misssing.
        Ex: didyoumean recursion recursion.
        '''
        file = await self.alex_image(
            url=f'https://api.alexflipnote.dev/didyoumean?top={search}&bottom={did_you_mean}',
            fn='dym.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="shows user's avatar")
    async def avatar(self, ctx, member: Optional[discord.Member]):
        '''
        Returns either author or member avatar if specified.
        Ex: avatar Dosek.
        '''
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @commands.command(brief="minecraft achievements maker")
    async def achieve(self, ctx, *, text):
        '''
        Minecraft 'Achievement Get!' image maker.
        Challenge icon is random one of 44.
        Ex: challenge slept more than 6 hours.
        '''
        text = text.replace(" ", "+")
        file = await self.alex_image(
            url=f'https://api.alexflipnote.dev/achievement?text={text}&icon={random.randint(1, 44)}',
            fn='achieve.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="minecraft challenge complete")
    async def challenge(self, ctx, *, text):
        '''
        Minecraft 'Challenge Complete!' image maker.
        Challenge icon is random one of 45.
        Ex: challenge finished all to-do's.
        '''
        text = text.replace(" ", "+")
        file = await self.alex_image(
            url=f'https://api.alexflipnote.dev/challenge?text={text}&icon={random.randint(1, 45)}',
            fn='challenge.png'
        )
        await ctx.send(file=file)

    @commands.command(name='qr', brief="make a QR code", description="this command lets you to create a QR code image for a given url. hyperlink argument is optional and by default it is [False]. you can set hyperlink by typing [True]")
    async def QR_code(self, ctx, url: str):
        '''
        Makes QR-code of a given URL.
        A great way to make your friends get rickrolled!
        Ex: qr https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO&t=42.
        P.S: this command accepts only URLs and raises an exception when it does not see URL.
        '''
        if not re.match(URL_REGEX, url):
            await ctx.send('Please provide a normal URL.')
        else:
            cs = self.bot.session
            r = await cs.get(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}")
            io = BytesIO(await r.read())
            await ctx.send(file=discord.File(fp=io, filename='qr.png'))

    @commands.command(brief="among us image!", description="among us ejecting image command")
    async def eject(self, ctx, color: str, is_impostor: bool, *, name: Optional[str]):
        '''
        Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: eject blue True Dosek.
        '''
        name = name or ctx.author.display_name
        cs = self.bot.session
        r = await cs.get(f'https://vacefron.nl/api/ejected?name={name}&impostor={is_impostor}&crewmate={color}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='ejected.png'))

    @commands.command(brief="trigger someone", aliases=['trigger'])
    async def triggered(self, ctx, member: Optional[discord.Member]):
        '''
        Makes "TRIGGERED" meme with an user avatar.
        Ex: triggered Dosek
        '''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'https://api.dagpi.xyz/image/triggered/?url={member.avatar_url}',
            fn='triggered.gif'
        )
        await ctx.send(file=file)

    @commands.command(name='ascii', brief="cool hackerman filter")
    async def ascii_command(self, ctx, member: Optional[discord.Member]):
        '''
        Makes ASCII version of an user avatar.
        Ex: ascii Dosek
        '''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'https://api.dagpi.xyz/image/ascii/?url={member.avatar_url}'
        )
        await ctx.send(file=file)

    @commands.command(name="discord", brief="generate realistic discord messages")
    async def _discord(self, ctx, member: discord.Member, *, text: str):
        '''
        Discord message maker.
        Returns an image with text and user avatar you specified.
        Ex: discord Dosek this command is cool ngl.
        '''
        file = await self.dagpi_image(
            url=f'https://api.dagpi.xyz/image/discord/?url={member.avatar_url}&username={member.name}&text={text}',
            fn='discord.png'
        )
        await ctx.send(file=file)

    @commands.command(brief="five guys with one girl meme", aliases=['wayg'])
    async def whyareyougay(self, ctx, member: Optional[discord.Member]):
        '''
        A legendary "Why are you gay?" meme maker.
        Member argument is optional, so if you call for a command
        without specifying a member you just wayg yourself.
        '''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'https://api.dagpi.xyz/image/whyareyougay/?url={ctx.author.avatar_url}&url2={member.avatar_url}',
            fn='wayg.png'
        )
        await ctx.send(file=file)

    @commands.command(name='lyrics', aliases=['song', 'track', 'lyric'], brief='find almost every song lyrics with this command.')
    async def lyric_command(self, ctx, *, args: str):
        '''
        Powerful lyrics command.
        Ex: lyrics believer.
        Has no limits.
        You can find lyrics for song that you want.
        Raises an exception if song does not exist in API data.
        '''
        args = args.replace(' ', '+')
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


def setup(bot):
    bot.add_cog(Canvas(bot))
