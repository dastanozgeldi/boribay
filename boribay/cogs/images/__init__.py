import random
from io import BytesIO
from typing import Optional

import discord
from boribay.core import Boribay, Cog, Context
from boribay.utils import Manip, make_image, make_image_url, polaroid_filter
from discord.ext import commands


class Images(Cog):
    """Images extension. A module that is created to work with images.
    Has features like: filters, text-images and legendary memes."""
    icon = '🖼'

    def __init__(self, bot: Boribay):
        self.bot = bot

    @commands.command()
    async def invert(self, ctx: Context, image: Optional[str]):
        """Invert an image.

        Example:
            **{p}invert @Dosek** - sends Dosek's inverted avatar.

        Args:
            image (Optional[str]): Accordingly an image you want to invert.
        """
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = polaroid_filter(image, method='invert')

        await ctx.send(file=file)

    @commands.command()
    async def grayscale(self, ctx: Context, image: Optional[str]):
        """Add the grayscale filter to an image.

        Example:
            **{p}grayscale @Dosek** - sends Dosek's grayscaled avatar.

        Args:
            image (Optional[str]): Accordingly an image you want to grayscalize.
        """
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = polaroid_filter(image, method='grayscale')

        await ctx.send(file=file)

    @commands.command()
    async def monochrome(self, ctx: Context, rgb: commands.Greedy[int], image: Optional[str]):
        """Add the monochrome filter to an image.

        Takes absolutely random colors if any of r, g, b not specified.

        Example:
            **{p}monochrome @Dosek** - sends Dosek's monochromed avatar.

        Args:
            image (Optional[str]): Accordingly an image you want to monochromize.
        """
        if 0 < len(rgb) < 3:
            raise commands.BadArgument('❌ Not enough colors were given.')

        r, g, b = (rgb := rgb[:3])

        if not rgb:
            r, g, b = random.choices(range(0, 255), k=3)

        async with ctx.timer:
            image = await make_image(ctx, image)
            file = polaroid_filter(image, method='monochrome',
                                   kwargs={'r_offset': r, 'g_offset': g, 'b_offset': b})

        await ctx.send(f'Taken RGB parameters: {r, g, b}', file=file)

    @commands.command()
    async def solarize(self, ctx: Context, image: Optional[str]):
        """Solarize an image.

        Example:
            **{p}solarize @Dosek** - sends Dosek's solarized avatar.

        Args:
            image (Optional[str]): Accordingly an image you want to solarize.
        """
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = polaroid_filter(image, method='solarize')

        await ctx.send(file=file)

    @commands.command()
    async def brighten(self, ctx: Context, image: Optional[str]):
        """Brighten an image.

        Example:
            **{p}brighten @Dosek** - sends Dosek's brightened avatar.

        Args:
            image (Optional[str]): Accordingly an image you want to brighten.
        """
        async with ctx.timer:
            image = await make_image(ctx, image)
            file = polaroid_filter(image, method='brighten', kwargs={'treshold': 69})

        await ctx.send(file=file)

    @commands.command()
    async def avatar(self, ctx: Context, member: Optional[discord.Member]):
        """Returns either author or member avatar if specified.

        Example:
            **{p}avatar @Dosek** - sends Dosek's avatar.

        Args:
            member (Optional[discord.Member]): A member you want to grab avatar from.
        """
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @commands.command()
    async def pixelate(self, ctx: Context, image: Optional[str]):
        """Pixelate an image.

        Example:
            **{p}pixelate @Dosek** - sends Dosek's pixelated avatar.

        Args:
            image (Optional[str]): An image you want to pixelate.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.pixelate(BytesIO(image))

        file = discord.File(buffer, 'pixelated.png')
        await ctx.send(file=file)

    @commands.command()
    async def wanted(self, ctx: Context, image: Optional[str]):
        """Make someone wanted.

        Example:
            **{p}wanted @Dosek** - makes Dosek wanted.

        Args:
            image (Optional[str]): A member you want to make wanted.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.wanted(BytesIO(image))

        file = discord.File(buffer, 'wanted.png')
        await ctx.send(file=file)

    @commands.command()
    async def spawn(self, ctx: Context, member: Optional[discord.Member], top_text: Optional[str], bottom_text: Optional[str]):
        """Welcoming image maker command.

        Example:
            **{p}spawn @Dosek "Member #69" "Welcome to us!"** - spawns Dosek.

        Args:
            member (Optional[discord.Member]): A member you want to "spawn".
            top_text (Optional[str]): Text that will be displayed at the top.
            bottom_text (Optional[str]): Text to put to the bottom.
        """
        member = member or ctx.author

        bottom_text = bottom_text or f'{member} just spawned in the server.'
        top_text = top_text or f'Member #{member.guild.member_count}'

        async with ctx.loading:
            image = await member.avatar_url.read()
            buffer = await Manip.welcome(BytesIO(image), top_text, bottom_text)

        file = discord.File(buffer, 'newbie.png')
        await ctx.send(file=file)

    @commands.command()
    async def jail(self, ctx: Context, image: Optional[str]):
        """Put someone into jail.

        Example:
            **{p}jail @Dosek** - puts Dosek into jail.

        Args:
            image (Optional[str]): A member you want to see in jail.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.jail(BytesIO(image))

        file = discord.File(buffer, 'jail.png')
        await ctx.send(file=file)

    @commands.command(name='f')
    async def press_f(self, ctx: Context, image: Optional[str]):
        """Pay respects to someone.

        Example:
            **{p}f @Dosek** - puts Dosek on the legendary canvas.

        Args:
            image (Optional[str]): A member you want to F.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.press_f(BytesIO(image))

        file = discord.File(buffer, 'f.png')
        message = await ctx.send(file=file)
        await message.add_reaction('<:press_f:796264575065653248>')

    @commands.command(aliases=['5g1g', 'fivegoneg'])
    async def fiveguysonegirl(self, ctx: Context, member: Optional[str]):
        """Legendary "5 guys 1 girl" meme maker.

        Example:
            **{p}5g1g @Dosek** - makes Dosek that one girl.

        Args:
            member (Optional[str]): A member you would like to 5g1g.
        """
        async with ctx.loading:
            author = await ctx.author.avatar_url_as(size=128).read()
            member = await make_image(ctx, member)
            buffer = await Manip.fiveguysonegirl(BytesIO(author), BytesIO(member))

        file = discord.File(buffer, '5g1g.png')
        await ctx.send(file=file)

    @commands.command(aliases=['ko'])
    async def fight(self, ctx: Context, member: str):
        """Fight someone!

        Example:
            **{p}fight @Dosek** - knocks Dosek out.

        Args:
            member (str): A member you would like to knockout.
        """
        async with ctx.loading:
            winner = await ctx.author.avatar_url_as(size=64).read()
            knocked_out = await make_image(ctx, member)
            buffer = await Manip.fight(BytesIO(winner), BytesIO(knocked_out))

        file = discord.File(buffer, 'fight.png')
        await ctx.send(file=file)

    @commands.command()
    async def swirl(self, ctx: Context, degrees: Optional[int], image: Optional[str]):
        """Swirl an image.

        Takes absolutely random degree if none specified.

        Example:
            **{p}swirl @Dosek** - swirlizes Dosek.

        Args:
            degrees (Optional[int]): How much degrees you want to swirl an image.
            image (Optional[str]): An image you want to swirlize.
        """
        degrees = degrees or random.randint(-360, 360)

        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.swirl(degrees, BytesIO(image))

        file = discord.File(buffer, 'swirl.png')
        await ctx.send(file=file)

    @commands.command()
    async def communist(self, ctx: Context, image: Optional[str]):
        """The communist meme maker.

        Example:
            **{p}communist @Dosek** - sends the communist version of Dosek.

        Args:
            image (Optional[str]): An image to put under the communist flag.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.communist(BytesIO(image))

        file = discord.File(buffer, 'communist.png')
        await ctx.send(file=file)

    @commands.command(aliases=['gay', 'gayize'])
    async def rainbow(self, ctx: Context, image: Optional[str]):
        """Put the rainbow filter on a user.

        Example:
            **{p}rainbow @Dosek** - sends the rainbow version of Dosek's avatar.

        Args:
            image (Optional[str]): An image you want to "gayize".
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.rainbow(BytesIO(image))

        file = discord.File(buffer, 'rainbow.png')
        await ctx.send(file=file)

    @commands.command(aliases=['wayg'])
    async def whyareyougay(self, ctx: Context, member: Optional[str]):
        """The legendary "WhY aRe YoU gAy?" meme maker.

        Example:
            **{p}whyareyougay @Dosek** - waygs Dosek.

        Args:
            member (Optional[str]): A member you would like to "wayg".
        """
        author = await ctx.author.avatar_url_as(size=128).read()

        async with ctx.loading:
            member = await make_image(ctx, member)
            buffer = await Manip.whyareyougae(BytesIO(author), BytesIO(member))

        file = discord.File(buffer, 'wayg.png')
        await ctx.send(file=file)

    @commands.command()
    async def drake(self, ctx: Context, no: str, yes: str):
        """The legendary "Drake yes/no" meme maker.

        Example:
            **{p}drake "Using MEE6" "Using Boribay"** - makes Drake meme for that.

        Args:
            no (str): Text that Drake does not prefer.
            yes (str): Text that Drake likes a lot.

        Raises:
            commands.BadArgument: If the text limit reaches (90 characters for each).
        """
        if len(yes) > 90 or len(no) > 90:
            raise commands.BadArgument('The text was too long to render.')

        buffer = await Manip.drake(no, yes)

        file = discord.File(buffer, 'drake.png')
        await ctx.send(file=file)

    @commands.command()
    async def clyde(self, ctx: Context, *, text: str):
        """Send a message from Clyde's POV.

        Example:
            **{p}clyde "Buy a discord nitro!"** - makes Clyde say that.

        Args:
            text (str): What should Clyde say.

        Raises:
            commands.BadArgument: If the text limit reaches (75 characters).
        """
        if len(text) > 75:
            raise commands.BadArgument('The text was too long to render.')

        buffer = await Manip.clyde(text)

        file = discord.File(buffer, 'clyde.png')
        await ctx.send(file=file)

    @commands.command()
    async def caption(self, ctx: Context, image: Optional[str]):
        """Get caption for an image.

        Example:
            **{p}caption @Dosek** - sends caption for Dosek's avatar.

        Args:
            image (Optional[str]): An image you want to get caption for.
        """
        image = await make_image_url(ctx, image)

        r = await ctx.bot.session.post(
            ctx.config.api.caption,
            json={'Content': image, 'Type': 'CaptionRequest'}
        )

        embed = ctx.embed(title=await r.text())
        await ctx.send(embed=embed.set_image(url=image))


def setup(bot: Boribay):
    bot.add_cog(Images(bot))
