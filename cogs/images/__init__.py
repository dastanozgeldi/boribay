from functools import partial
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from utils.Cog import Cog
from utils.Manipulation import Manip, make_image


class Images(Cog):
    """My own implementation of images."""

    def __init__(self, bot):
        self.bot = bot
        self.name = '🖼 Images'
        self.cache = {}

    @commands.command()
    async def avatar(self, ctx, member: Optional[discord.Member]):
        """Returns either author or member avatar if specified.
        Ex: avatar Dosek."""
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @commands.command()
    async def triggered(self, ctx, image: Optional[str]):
        """Makes a "TRIGGERED" meme with whatever you would put there.
        Ex: triggered Dosek
        Args: image (Optional[str]): user, image url or an attachment."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            buffer = BytesIO(image)
            f = partial(Manip.triggered, buffer)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='triggered.png'))

    @commands.command()
    async def wanted(self, ctx, image: Optional[str]):
        """A very simple `wanted` image command.
        Puts given image into a layout and makes that person 'wanted'"""
        async with ctx.timer:
            image = await make_image(ctx, image)
            buffer = BytesIO(image)
            f = partial(Manip.wanted, buffer)
            buffer = await self.bot.loop.run_in_executor(None, f)
            await ctx.send(file=discord.File(fp=buffer, filename='wanted.png'))

    @commands.command()
    async def drake(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
        yes (str): argument for 'yes' side of image."""
        if len(yes) > 90 or len(no) > 90:
            return await ctx.send('The text was too long to render.')
        async with ctx.timer:
            f = partial(Manip.drake, no, yes)
            buffer = await self.bot.loop.run_in_executor(None, f)
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

                f = partial(Manip.clyde, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='clyde.png'))

    @commands.command(name='f')
    async def press_f(self, ctx, image: Optional[str]):
        """'Press F to pay respect' meme maker. F your mate using this command.
        Args: image (optional): Image that you want to see on the canvas."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            buffer = BytesIO(image)
            f = partial(Manip.press_f, buffer)
            buffer = await self.bot.loop.run_in_executor(None, f)
            msg = await ctx.send(file=discord.File(fp=buffer, filename='f.png'))
        await msg.add_reaction('<:press_f:796264575065653248>')

    @commands.command(hidden=True)
    async def swirl(self, ctx, degrees: Optional[int], image: Optional[str]):
        """Swirl an image.
        Args: image (str): image that you specify. it's either member/emoji/url.
        it swirls your avatar if argument is not passed.
        degrees (int): this is basically how much do you want to swirl an image.
        takes random values if argument is not passed."""
        async with ctx.timer:
            image = await make_image(ctx, image)
            degrees = degrees or __import__('random').randint(-360, 360)
            buffer = BytesIO(image)
            f = partial(Manip.swirl, degrees, buffer)
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

                f = partial(Manip.theory, text)
                buffer = await self.bot.loop.run_in_executor(None, f)
                self.cache[text] = buffer
                await ctx.send(file=discord.File(fp=buffer, filename='theory.png'))


def setup(bot):
    bot.add_cog(Images(bot))
