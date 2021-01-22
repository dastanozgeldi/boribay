import discord
import random
import functools
from io import BytesIO
from typing import Optional
from utils.CustomCog import Cog
from discord.ext import commands
from utils.Manipulation import Manip, make_image, make_image_url


class Images(Cog):
    """Image manipulation extension! Make many different kinds of memes, images,
    convert emojis into images etc."""

    def __init__(self, bot):
        self.bot = bot
        self.name = '🖼 Images'
        self.cache = {}

    async def dagpi_image(self, url, fn: Optional[str]):
        cs = self.bot.session
        r = await cs.get(f'https://api.dagpi.xyz/image/{url}', headers={'Authorization': self.bot.config['API']['dagpi_token']})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'dagpi.png')
        return f

    async def alex_image(self, url, fn: Optional[str]):
        cs = self.bot.session
        r = await cs.get(f'https://api.alexflipnote.dev/{url}', headers={'Authorization': self.bot.config['API']['alex_token']})
        io = BytesIO(await r.read())
        f = discord.File(fp=io, filename=fn or 'alex.png')
        return f

    @commands.command(aliases=['trigger'])
    async def triggered(self, ctx, whatever: Optional[str]):
        '''Makes "TRIGGERED" meme with an user avatar.
        Ex: triggered Dosek'''
        image = await make_image_url(ctx, whatever)
        file = await self.dagpi_image(
            url=f'triggered/?url={image}',
            fn='triggered.gif'
        )
        await ctx.send(file=file)

    @commands.command(name='f')
    async def press_f(self, ctx, image: Optional[str]):
        """'Press F to pay respect' meme maker. F your mate using this command.
        Args: image (optional): Image that you want to see on the canvas."""
        image = await make_image(ctx, image)
        buffer = BytesIO(image)
        f = functools.partial(Manip.press_f, buffer)
        buffer = await self.bot.loop.run_in_executor(None, f)
        msg = await ctx.send(file=discord.File(fp=buffer, filename='f.png'))
        await msg.add_reaction('<:press_f:796264575065653248>')

    @commands.command()
    async def emoji(self, ctx, emoji: str):
        """Simply get an image of the given emoji.
        Args: thing (str): emoji that you want to convert to an image."""
        async with ctx.timer:
            image = await make_image(ctx, emoji)
            io = BytesIO(image)
            await ctx.send(file=discord.File(io, filename='emoji.png'))

    @commands.command(aliases=['colours'])
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
    async def captcha(self, ctx, text: str, thing: Optional[str]):
        """Captcha maker command.
        Args: member (Member): member that you specified.
        text (str): text you want to see in a captcha image."""
        image = await make_image_url(ctx, thing)
        await ctx.send(file=await self.dagpi_image(url=f'captcha/?url={image}&text={text}'))

    @commands.command(aliases=['ph'])
    async def pornhub(self, ctx, text_1: str, text_2: Optional[str] = 'Hub'):
        '''Pornhub logo maker.
        No matter how long is text, API returns image perfectly (hope so).
        Ex: pornhub Bori bay.'''
        file = await self.alex_image(
            url=f'pornhub?text={text_1.replace(" ", "%20")}&text2={text_2.replace(" ", "%20")}',
            fn='ph.png'
        )
        await ctx.send(file=file)

    @commands.command(aliases=['dym'])
    async def didyoumean(self, ctx, search: str, did_you_mean: str):
        '''Google search 'Did you mean' meme.
        Arguments are required and raises an exception if one of them is misssing.
        Ex: didyoumean recursion recursion.'''
        file = await self.alex_image(
            url=f'didyoumean?top={search}&bottom={did_you_mean}',
            fn='dym.png'
        )
        await ctx.send(file=file)

    @commands.command()
    async def avatar(self, ctx, member: Optional[discord.Member]):
        '''Returns either author or member avatar if specified.
        Ex: avatar Dosek.'''
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @commands.command()
    async def achieve(self, ctx, *, text: str):
        '''Minecraft 'Achievement Get!' image maker.
        Challenge icon is random one of 44.
        Ex: challenge slept more than 6 hours.'''
        text = text.replace(' ', '%20')
        file = await self.alex_image(
            url=f'achievement?text={text}&icon={random.randint(1, 44)}',
            fn='achieve.png'
        )
        await ctx.send(file=file)

    @commands.command()
    async def challenge(self, ctx, *, text):
        '''Minecraft 'Challenge Complete!' image maker.
        Challenge icon is random one of 45.
        Ex: challenge finished all to-do's.'''
        text = text.replace(' ', '%20')
        file = await self.alex_image(
            url=f'challenge?text={text}&icon={random.randint(1, 45)}',
            fn='challenge.png'
        )
        await ctx.send(file=file)

    @commands.command(name='ascii')
    async def ascii_command(self, ctx, thing: Optional[str]):
        '''Makes ASCII version of an user avatar.
        Ex: ascii Dosek'''
        image = await make_image_url(ctx, thing)
        file = await self.dagpi_image(url=f'ascii/?url={image}', fn='ascii.png')
        await ctx.send(file=file)

    @commands.command(name='discord')
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
            cached = self.cache[no]
            cached.seek(0)
            await ctx.send(file=discord.File(fp=cached, filename='drake.png'))

        except KeyError:
            if len(yes) > 90 or len(no) > 90:
                return await ctx.send('The text was too long to render.')

            f = functools.partial(Manip.drake, no, yes)
            buffer = await self.bot.loop.run_in_executor(None, f)
            self.cache[no] = buffer
            await ctx.send(file=discord.File(fp=buffer, filename='drake.png'))

    @commands.command()
    async def clyde(self, ctx, *, text: str):
        """Make an image with text that Clyde bot sends.
        Args: text (str): the text you want to be displayed."""
        async with ctx.timer:
            try:
                cached = self.cache[text]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='clyde.png'))

            except KeyError:
                if len(text) > 75:
                    return await ctx.send('The text was too long to render.')

                f = functools.partial(Manip.clyde, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='clyde.png'))

    @commands.command()
    async def noise(self, ctx, image: Optional[str]):
        """Randomly adds noises to an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = Manip.polaroid_filter(ctx, image, method='add_noise_rand', fn='noise')
            await ctx.send(file=file)

    @commands.command()
    async def solarize(self, ctx, image: Optional[str]):
        """As it says, solarizes an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = Manip.polaroid_filter(ctx, image, method='solarize', fn='solarized')
            await ctx.send(file=file)

    @commands.command()
    async def brighten(self, ctx, image: Optional[str]):
        """As it says, brightens an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = Manip.polaroid_filter(ctx, image, method='brighten', fn='brightened', kwargs={'treshold': 69})
            await ctx.send(file=file)

    @commands.command(hidden=True)
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

    @commands.command(aliases=['lisa'])
    async def theory(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board."""
        async with ctx.timer:
            try:
                cached = self.cache[text]
                cached.seek(0)
                await ctx.send(file=discord.File(fp=cached, filename='theory.png'))

            except KeyError:
                if len(text) > 144:
                    return await ctx.send('The text was too long to render.')

                f = functools.partial(Manip.theory, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='theory.png'))


def setup(bot):
    bot.add_cog(Images(bot))
