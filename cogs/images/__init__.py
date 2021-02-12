import random
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from polaroid import Image
from utils.Cog import Cog
from utils.Manipulation import Manip, make_image


class Images(Cog):
    """My own implementation of images."""
    icon = '🖼'
    name = 'Images'

    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    @staticmethod
    def polaroid_filter(ctx, image: bytes, *, method: str, fn: str, args: list = None, kwargs: dict = None):
        args = args or []
        kwargs = kwargs or {}
        img = Image(image)
        method = getattr(img, method)
        method(*args, **kwargs)
        buffer = BytesIO(img.save_bytes())
        file = discord.File(fp=buffer, filename=f'{fn}.png')
        return file

    @commands.group(invoke_without_command=True)
    async def filters(self, ctx):
        """Image filtering commands parent powered using Polaroid."""
        await ctx.send_help('filters')

    @commands.group(invoke_without_command=True)
    async def meme(self, ctx):
        """Meme-based images manipulation commands parent."""
        await ctx.send_help('meme')

    @commands.group(invoke_without_command=True)
    async def text(self, ctx):
        """Parent of image-commands that manipulate with text."""
        await ctx.send_help('text')

    @filters.command()
    async def noise(self, ctx, image: Optional[str]):
        """Randomly adds noises to an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        image = await make_image(ctx, image)
        file = self.polaroid_filter(ctx, image, method='add_noise_rand', fn='noise')
        await ctx.send(file=file)

    @filters.command()
    async def invert(self, ctx, image: Optional[str]):
        """Inverts given image."""
        image = await make_image(ctx, image)
        file = self.polaroid_filter(ctx, image, method='invert', fn='inverted')
        await ctx.send(file=file)

    @filters.command(aliases=['gs'])
    async def grayscale(self, ctx, image: Optional[str]):
        """Adds a greyscale filter to an image."""
        image = await make_image(ctx, image)
        file = self.polaroid_filter(ctx, image, method='grayscale', fn='grayscaled')
        await ctx.send(file=file)

    @filters.command()
    async def monochrome(self, ctx, r: Optional[int], g: Optional[int], b: Optional[int], image: Optional[str]):
        """Adds a monochrome filter to an image.
        Takes absolutely random colors if any of r, g, b not specified.
        So be careful!"""
        if not all((r, g, b)):
            r, g, b = random.choices(range(0, 255), k=3)
        image = await make_image(ctx, image)
        file = self.polaroid_filter(
            ctx,
            image,
            method='monochrome',
            fn='monochromed',
            kwargs={'r_offset': r, 'g_offset': g, 'b_offset': b}
        )
        await ctx.send(f'Taken RGB parameters: {r, g, b}', file=file)

    @filters.command()
    async def solarize(self, ctx, image: Optional[str]):
        """As it says, solarizes an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        image = await make_image(ctx, image)
        file = self.polaroid_filter(ctx, image, method='solarize', fn='solarized')
        await ctx.send(file=file)

    @filters.command()
    async def brighten(self, ctx, image: Optional[str]):
        """As it says, brightens an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        image = await make_image(ctx, image)
        file = self.polaroid_filter(ctx, image, method='brighten', fn='brightened', kwargs={'treshold': 69})
        await ctx.send(file=file)

    @commands.command()
    async def avatar(self, ctx, member: Optional[discord.Member]):
        """Returns either author or member avatar if specified.
        Ex: avatar Dosek."""
        member = member or ctx.author
        await ctx.send(str(member.avatar_url))

    @meme.command()
    async def obama(self, ctx, image: Optional[str]):
        """Do you remember that meme where Obama rewards himself? Yeah, that."""
        image = await make_image(ctx, image)
        buffer = await Manip.obama(BytesIO(image))
        await ctx.send(file=discord.File(fp=buffer, filename='obama.png'))

    @meme.command()
    async def triggered(self, ctx, image: Optional[str]):
        """Makes a "TRIGGERED" meme with whatever you would put there.
        Ex: triggered Dosek
        Args: image (Optional[str]): user, image url or an attachment."""
        image = await make_image(ctx, image)
        buffer = await Manip.triggered(BytesIO(image))
        await ctx.send(file=discord.File(fp=buffer, filename='triggered.png'))

    @meme.command()
    async def wanted(self, ctx, image: Optional[str]):
        """A very simple `wanted` image command.
        Puts given image into a layout and makes that person 'wanted'"""
        image = await make_image(ctx, image)
        buffer = await Manip.wanted(BytesIO(image))
        await ctx.send(file=discord.File(fp=buffer, filename='wanted.png'))

    @meme.command()
    async def spawn(self, ctx, member: Optional[discord.Member], top_text: Optional[str], bottom_text: Optional[str]):
        """Welcoming image maker command.
        Args: member: A member you want to "spawn"
        top_text: Text that will be displayed at the top.
        bottom_text: Text at the bottom."""
        member = member or ctx.author
        bottom_text = bottom_text or f'{member} just spawned in the server.'
        top_text = top_text or f'Member #{member.guild.member_count}'
        image = await member.avatar_url.read()
        buffer = await Manip.welcome(BytesIO(image), top_text, bottom_text)
        await ctx.send(file=discord.File(fp=buffer, filename='newbie.png'))

    @meme.command(name='f')
    async def press_f(self, ctx, image: Optional[str]):
        """'Press F to pay respect' meme maker. F your mate using this command.
        Args: image (optional): Image that you want to see on the canvas."""
        image = await make_image(ctx, image)
        buffer = await Manip.press_f(BytesIO(image))
        msg = await ctx.send(file=discord.File(fp=buffer, filename='f.png'))
        await msg.add_reaction('<:press_f:796264575065653248>')

    @meme.command()
    async def swirl(self, ctx, degrees: Optional[int], image: Optional[str]):
        """Swirl an image.
        Args: image (str): image that you specify. it's either member/emoji/url.
        it swirls your avatar if argument is not passed.
        degrees (int): this is basically how much do you want to swirl an image.
        takes random values if argument is not passed."""
        image = await make_image(ctx, image)
        degrees = degrees or random.randint(-360, 360)
        buffer = await Manip.swirl(degrees, BytesIO(image))
        await ctx.send(file=discord.File(fp=buffer, filename='swirl.png'))

    @text.command()
    async def drake(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
        yes (str): argument for 'yes' side of image."""
        if len(yes) > 90 or len(no) > 90:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.drake(no, yes)
        await ctx.send(file=discord.File(fp=buffer, filename='drake.png'))

    @text.command()
    async def clyde(self, ctx, *, text: str):
        """Make an image with text that Clyde bot sends.
        Args: text (str): the text you want to be displayed."""
        if len(text) > 75:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.clyde(text)
        await ctx.send(file=discord.File(fp=buffer, filename='clyde.png'))

    @text.command()
    async def theory(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board."""
        if len(text) > 144:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.theory(text)
        await ctx.send(file=discord.File(fp=buffer, filename='theory.png'))


def setup(bot):
    bot.add_cog(Images(bot))
