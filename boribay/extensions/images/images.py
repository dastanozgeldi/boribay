import random
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands

from boribay.core import utils
from boribay.core.utils.manipulation import Manip, make_image


class Images(utils.Cog):
    """The image commands extension.

    A module that is created to work with images.

    Has features like: filters, text-images and legendary memes.
    """

    icon = "🖼"

    @utils.command()
    async def avatar(self, ctx, member: Optional[discord.Member]) -> None:
        """Sends either author or member avatar if specified.

        Example:
            **{p}avatar @Dosek** - sends Dosek's avatar.

        Args:
            member (Optional[discord.Member]): A member you want to grab avatar from.
        """
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @utils.command()
    async def pixelate(self, ctx, image: Optional[str]) -> None:
        """Pixelate an image.

        Example:
            **{p}pixelate @Dosek** - sends Dosek's pixelated avatar.

        Args:
            image (Optional[str]): An image you want to pixelate.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.pixelate(BytesIO(image))

        file = discord.File(buffer, "pixelated.png")
        await ctx.send(file=file)

    @utils.command()
    async def achievement(self, ctx: utils.Context, *, title: str):
        if len(title) > 90:
            raise commands.BadArgument("The text was too long to render.")

        buffer = await Manip.achievement(title, "ema")
        file = discord.File(buffer, "achievement.png")
        await ctx.send(file=file)

    @utils.command()
    async def wanted(self, ctx, image: Optional[str]) -> None:
        """Make someone wanted.

        Example:
            **{p}wanted @Dosek** - makes Dosek wanted.

        Args:
            image (Optional[str]): A member you want to make wanted.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.wanted(BytesIO(image))

        file = discord.File(buffer, "wanted.png")
        await ctx.send(file=file)

    @utils.command()
    async def jail(self, ctx, image: Optional[str]) -> None:
        """Put someone into jail.

        Example:
            **{p}jail @Dosek** - puts Dosek into jail.

        Args:
            image (Optional[str]): A member you want to see in jail.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.jail(BytesIO(image))

        file = discord.File(buffer, "jail.png")
        await ctx.send(file=file)

    @utils.command(name="f")
    async def press_f(self, ctx, image: Optional[str]) -> None:
        """Pay respects to someone.

        Example:
            **{p}f @Dosek** - puts Dosek on the legendary canvas.

        Args:
            image (Optional[str]): A member you want to F.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.press_f(BytesIO(image))

        file = discord.File(buffer, "f.png")
        message = await ctx.send(file=file)
        await message.add_reaction("<:press_f:796264575065653248>")

    @utils.command(aliases=("5g1g", "fivegoneg"))
    async def fiveguysonegirl(self, ctx, member: Optional[str]) -> None:
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

        file = discord.File(buffer, "5g1g.png")
        await ctx.send(file=file)

    @utils.command(aliases=("ko",))
    async def fight(self, ctx, member: str) -> None:
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

        file = discord.File(buffer, "fight.png")
        await ctx.send(file=file)

    @utils.command()
    async def swirl(self, ctx, degrees: Optional[int], image: Optional[str]) -> None:
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

        file = discord.File(buffer, "swirl.png")
        await ctx.send(file=file)

    @utils.command()
    async def communist(self, ctx, image: Optional[str]) -> None:
        """The communist meme maker.

        Example:
            **{p}communist @Dosek** - sends the communist version of Dosek.

        Args:
            image (Optional[str]): An image to put under the communist flag.
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.communist(BytesIO(image))

        file = discord.File(buffer, "communist.png")
        await ctx.send(file=file)

    @utils.command(aliases=("gay", "gayize"))
    async def rainbow(self, ctx, image: Optional[str]) -> None:
        """Put the rainbow filter on a user.

        Example:
            **{p}rainbow @Dosek** - sends the rainbow version of Dosek's avatar.

        Args:
            image (Optional[str]): An image you want to "gayize".
        """
        async with ctx.loading:
            image = await make_image(ctx, image)
            buffer = await Manip.rainbow(BytesIO(image))

        file = discord.File(buffer, "rainbow.png")
        await ctx.send(file=file)

    @utils.command(aliases=("wayg",))
    async def whyareyougay(self, ctx, member: Optional[str]) -> None:
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

        file = discord.File(buffer, "wayg.png")
        await ctx.send(file=file)

    @utils.command()
    async def drake(self, ctx, no: str, yes: str) -> None:
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
            raise commands.BadArgument("The text was too long to render.")

        buffer = await Manip.drake(no, yes)

        file = discord.File(buffer, "drake.png")
        await ctx.send(file=file)

    @utils.command()
    async def clyde(self, ctx, *, text: str) -> None:
        """Send a message from Clyde's POV.

        Example:
            **{p}clyde "Buy a discord nitro!"** - makes Clyde say that.

        Args:
            text (str): What should Clyde say.

        Raises:
            commands.BadArgument: If the text limit reaches (75 characters).
        """
        if len(text) > 75:
            raise commands.BadArgument("The text was too long to render.")

        buffer = await Manip.clyde(text)

        file = discord.File(buffer, "clyde.png")
        await ctx.send(file=file)
