import functools
import random
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from utils.Manipulation import Manip, make_image, make_image_url
from utils.CustomCog import Cog

EMOJI_REGEX = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'


class Canvas(Cog, name='Images'):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🖼 Images'
        self.drake_cache = {}
        self.clyde_cache = {}
        self.spongebob_cache = {}
        self.theory_cache = {}

    async def dagpi_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(f'https://api.dagpi.xyz/image/{url}', headers={'Authorization': self.bot.config['API']['dagpi_token']})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'dagpi.png')
        return f

    async def alex_image(self, url, fn: str = None):
        cs = self.bot.session
        r = await cs.get(f'https://api.alexflipnote.dev/{url}', headers={'Authorization': self.bot.config['API']['alex_token']})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'alex.png')
        return f

    @commands.command()
    async def emoji(self, ctx, emoji: str):
        """Simply get an image of the given emoji.
        Args: thing (str): emoji that you want to convert to an image."""
        async with ctx.timer:
            image = await make_image(ctx, emoji)
            io = BytesIO(image)
            await ctx.send(file=discord.File(io, filename='emoji.png'))

    @commands.command(aliases=['colours'], brief='see top 5 colors of your/user avatar.')
    async def colors(self, ctx, member: Optional[str]):
        """Colors of the avatar. Displays Top5 colors of a given image.
        Args: member (Optional[discord.Member]): member, which is either specified one or author."""
        image = await make_image_url(ctx, member)
        file = await self.dagpi_image(
            url=f'colors/?url={image}',
            fn='colors.png'
        )
        await ctx.send(file=file)

    @commands.command()
    async def captcha(self, ctx, thing: str, text: str):
        """Captcha maker command.
        Args: member (Member): member that you specified.
        text (str): text you want to see in a captcha image."""
        image = await make_image_url(ctx, thing)
        await ctx.send(file=await self.dagpi_image(url=f'captcha/?url={image}&text={text}'))

    @commands.command(aliases=['ph'], brief='make a pornhub logo with text you want.')
    async def pornhub(self, ctx, text_1: str, text_2: Optional[str]):
        '''Pornhub logo maker.
        No matter how long is text, API returns image perfectly (hope so).
        Ex: pornhub Bori bay.'''
        text_2 = text_2 or 'Hub'
        file = await self.alex_image(
            url=f'pornhub?text={text_1.replace(" ", "%20")}&text2={text_2.replace(" ", "%20")}',
            fn='ph.png'
        )
        await ctx.send(file=file)

    @commands.command(aliases=['dym'], brief='make a "did you mean" meme.')
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

    @commands.command(aliases=['trigger'])
    async def triggered(self, ctx, thing: Optional[str]):
        '''Makes "TRIGGERED" meme with an user avatar.
        Ex: triggered Dosek'''
        image = await make_image_url(ctx, thing)
        file = await self.dagpi_image(
            url=f'triggered/?url={image}',
            fn='triggered.gif'
        )
        await ctx.send(file=file)

    @commands.command(name='ascii')
    async def ascii_command(self, ctx, thing: Optional[str]):
        '''Makes ASCII version of an user avatar.
        Ex: ascii Dosek'''
        image = await make_image_url(ctx, thing)
        file = await self.dagpi_image(url=f'ascii/?url={image}', fn='ascii.png')
        await ctx.send(file=file)

    @commands.command(name="discord")
    async def _discord(self, ctx, member: discord.Member, *, text: str):
        '''Discord message maker.
        Returns an image with text and user avatar you specified.
        Ex: discord Dosek this command is cool ngl.'''
        member = member or ctx.author
        file = await self.dagpi_image(
            url=f'discord/?url={member.avatar_url}&username={member.name}&text={text}',
            fn='discord.png'
        )
        await ctx.send(file=file)

    @commands.command(aliases=['wayg'])
    async def whyareyougay(self, ctx, member: Optional[str]):
        '''A legendary "Why are you gay?" meme maker.
        Member argument is optional, so if you call for a command
        without specifying a member you just wayg yourself.'''
        image = await make_image_url(ctx, member)
        file = await self.dagpi_image(
            url=f'whyareyougay/?url={ctx.author.avatar_url}&url2={image}',
            fn='wayg.png'
        )
        await ctx.send(file=file)

    @commands.command()
    async def drake(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
        yes (str): argument for 'yes' side of image."""
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

    @commands.command()
    async def clyde(self, ctx, *, text: str):
        """Make an image with text that Clyde bot sends.
        Args: text (str): the text you want to be displayed."""
        async with ctx.timer:
            try:
                cached = self.clyde_cache[text]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='clyde.png'))

            except KeyError:
                if len(text) > 75:
                    return await ctx.send('The text was too long to render.')

                f = functools.partial(Manip.clyde, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.clyde_cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='clyde.png'))

    @commands.command(aliases=['lisa'])
    async def theory(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board.
        Raises: Exception when text > 144 symbols."""
        async with ctx.timer:
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

    @commands.command()
    async def solarize(self, ctx, image: Optional[str]):
        """Solarizes given image.
        Args: image (str): passed image. if not specified, takes author avatar."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            f = functools.partial(Manip.solarize, image)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='solarized.png'))

    @commands.command()
    async def brighten(self, ctx, image: Optional[str], quantity: Optional[int] = 69):
        """Makes image brightened.
        Args: image (str): passed image.
        quantity (int): How much do you want to brighten an image. Defaults to 69."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            f = functools.partial(Manip.brighten, image, quantity)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='brightened.png'))


def setup(bot):
    bot.add_cog(Canvas(bot))
