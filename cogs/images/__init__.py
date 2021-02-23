import random
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands, flags
from utils.Cog import Cog
from utils.Manipulation import (
    Manip,
    make_image,
    make_image_url,
    polaroid_filter
)


class Images(Cog):
    """My own implementation of images."""
    icon = '🖼'
    name = 'Images'

    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    async def dagpi_image(self, url, fn=None):
        cs = self.bot.session
        r = await cs.get(f'https://beta.dagpi.xyz/image/{url}', headers={'Authorization': self.bot.config['API']['dagpi_token']})
        return discord.File(BytesIO(await r.read()), fn or 'dagpi.png')

    async def alex_image(self, url, fn=None):
        cs = self.bot.session
        r = await cs.get(f'https://api.alexflipnote.dev/{url}', headers={'Authorization': self.bot.config['API']['alex_token']})
        return discord.File(BytesIO(await r.read()), fn or 'alex.png')

    @commands.group(invoke_without_command=True)
    async def api(self, ctx):
        """Parent of image-commands that use API to manipulate with."""
        await ctx.send_help('api')

    @commands.group(aliases=['filter'], invoke_without_command=True)
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
    async def invert(self, ctx, image: Optional[str]):
        """Inverts given image."""
        image = await make_image(ctx, image)
        await ctx.send(file=polaroid_filter(ctx, image, method='invert'))

    @filters.command(aliases=['gs'])
    async def grayscale(self, ctx, image: Optional[str]):
        """Adds a greyscale filter to an image."""
        image = await make_image(ctx, image)
        await ctx.send(file=polaroid_filter(ctx, image, method='grayscale'))

    @filters.command()
    async def monochrome(self, ctx, r: Optional[int], g: Optional[int], b: Optional[int], image: Optional[str]):
        """Adds a monochrome filter to an image.
        Takes absolutely random colors if any of r, g, b not specified.
        So be careful!"""
        if not all((r, g, b)):
            r, g, b = random.choices(range(0, 255), k=3)
        image = await make_image(ctx, image)
        file = polaroid_filter(
            ctx, image,
            method='monochrome',
            kwargs={'r_offset': r, 'g_offset': g, 'b_offset': b}
        )
        await ctx.send(f'Taken RGB parameters: {r, g, b}', file=file)

    @filters.command()
    async def solarize(self, ctx, image: Optional[str]):
        """As it says, solarizes an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        image = await make_image(ctx, image)
        await ctx.send(file=polaroid_filter(ctx, image, method='solarize'))

    @filters.command()
    async def brighten(self, ctx, image: Optional[str]):
        """As it says, brightens an image.
        Args: image (str): A specified image, either user, emoji or attachment."""
        image = await make_image(ctx, image)
        await ctx.send(file=polaroid_filter(ctx, image, method='brighten', kwargs={'treshold': 69}))

    @flags.add_flag('--circle', type=bool, help='Whether to circlize an avatar.')
    @flags.command()
    async def avatar(self, ctx, member: Optional[discord.Member], **flags):
        """Returns either author or member avatar if specified.
        Ex: avatar Dosek."""
        member = member or ctx.author
        if flags.pop('circle', False):
            image = await member.avatar_url.read()
            buffer = await Manip.circlize(BytesIO(image))
            return await ctx.send(file=discord.File(buffer, f'{member}.png'))
        await ctx.send(str(member.avatar_url))

    @meme.command()
    async def obama(self, ctx, image: Optional[str]):
        """Do you remember that meme where Obama rewards himself? Yeah, that."""
        image = await make_image(ctx, image)
        buffer = await Manip.obama(BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'obama.png'))

    @meme.command()
    async def wanted(self, ctx, image: Optional[str]):
        """A very simple `wanted` image command.
        Puts given image into a layout and makes that person 'wanted'"""
        image = await make_image(ctx, image)
        buffer = await Manip.wanted(BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'wanted.png'))

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
        await ctx.send(file=discord.File(buffer, 'newbie.png'))

    @meme.command(name='f')
    async def press_f(self, ctx, image: Optional[str]):
        """'Press F to pay respect' meme maker. F your mate using this command.
        Args: image (optional): Image that you want to see on the canvas."""
        image = await make_image(ctx, image)
        buffer = await Manip.press_f(BytesIO(image))
        msg = await ctx.send(file=discord.File(buffer, 'f.png'))
        await msg.add_reaction('<:press_f:796264575065653248>')

    @meme.command(aliases=['5g1g', 'fivegoneg'])
    async def fiveguysonegirl(self, ctx, member: Optional[str]):
        """Legendary '5 guys 1 girl meme maker.
        Args: member: a member you'd like to 5g1g."""
        author = await ctx.author.avatar_url_as(size=128).read()
        buffer = await Manip.fiveguysonegirl(BytesIO(author), BytesIO(await make_image(ctx, member)))
        await ctx.send(file=discord.File(buffer, '5g1g.png'))

    @meme.command()
    async def swirl(self, ctx, degrees: Optional[int], image: Optional[str]):
        """Swirl an image.
        Args: image (str): image that you specify. it's either member/emoji/url.
        degrees (int): this is basically how much do you want to swirl an image.
        takes random values if argument is not passed."""
        image = await make_image(ctx, image)
        degrees = degrees or random.randint(-360, 360)
        buffer = await Manip.swirl(degrees, BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'swirl.png'))

    @meme.command()
    async def communist(self, ctx, image: Optional[str]):
        """The communist meme maker.
        Args: image: image that you specify. it's either member/emoji/url."""
        image = await make_image(ctx, image)
        buffer = await Manip.communist(BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'communist.png'))

    @meme.command()
    async def wider(self, ctx, image: Optional[str]):
        """Widerize an image."""
        image = await make_image(ctx, image)
        buffer = await Manip.wide(BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'wider.png'))

    @meme.command(aliases=['gay', 'gayize'])
    async def rainbow(self, ctx, image: Optional[str]):
        """Put rainbow filter on a user.
        Args: image: image that you specify. it's either member/emoji/url."""
        image = await make_image(ctx, image)
        buffer = await Manip.rainbow(BytesIO(image))
        await ctx.send(file=discord.File(buffer, 'rainbow.png'))

    @meme.command(aliases=['wayg'])
    async def whyareyougay(self, ctx, member: Optional[str]):
        """A legendary "Why are you gay?" meme maker.
        Member argument is optional, so if you call for a command
        without specifying a member you just wayg yourself."""
        author = await ctx.author.avatar_url_as(size=128).read()
        member = await make_image(ctx, member)
        buffer = await Manip.whyareyougae(BytesIO(author), BytesIO(member))
        await ctx.send(file=discord.File(buffer, 'wayg.png'))

    @text.command()
    async def drake(self, ctx, no: str, yes: str):
        """Legendary 'Drake yes/no' meme maker.
        Example: **drake "discord.js" "discord.py"**
        Args: no (str): argument for 'no' side of image.
        yes (str): argument for 'yes' side of image."""
        if len(yes) > 90 or len(no) > 90:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.drake(no, yes)
        await ctx.send(file=discord.File(buffer, 'drake.png'))

    @text.command()
    async def clyde(self, ctx, *, text: str):
        """Make an image with text that Clyde bot sends.
        Args: text (str): the text you want to be displayed."""
        if len(text) > 75:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.clyde(text)
        await ctx.send(file=discord.File(buffer, 'clyde.png'))

    @text.command()
    async def theory(self, ctx, *, text: str):
        """Literally no idea how to describe this command.
        Just try it and see.
        Example: **theory its better using your own commands than someone's API.**
        Args: text (str): text to pass on the board."""
        if len(text) > 144:
            raise commands.BadArgument('The text was too long to render.')
        buffer = await Manip.theory(text)
        await ctx.send(file=discord.File(buffer, 'theory.png'))

    @api.command()
    async def triggered(self, ctx, image: Optional[str]):
        """Makes a "TRIGGERED" meme with whatever you would put there.
        Args: image (Optional[str]): user, image url or an attachment."""
        image = await make_image_url(ctx, image)
        await ctx.send(file=await self.dagpi_image(f'triggered/?url={image}', 'triggered.gif'))

    @api.command(aliases=['colours'])
    async def colors(self, ctx, member: Optional[str]):
        """Colors of the avatar. Displays Top5 colors of a given image.
        Args: member (Optional[discord.Member]): member, which is either specified one or author."""
        image = await make_image_url(ctx, member)
        await ctx.send(file=await self.dagpi_image(f'colors/?url={image}', 'colors.png'))

    @api.command()
    async def captcha(self, ctx, text: str, thing: Optional[str]):
        """Captcha maker command.
        Args: member (Member): member that you specified.
        text (str): text you want to see in a captcha image."""
        image = await make_image_url(ctx, thing)
        await ctx.send(file=await self.dagpi_image(f'captcha/?url={image}&text={text}', 'captcha.png'))

    @api.command(aliases=['ph'])
    async def pornhub(self, ctx, text_1: str, text_2: Optional[str] = 'Hub'):
        '''Pornhub logo maker.
        No matter how long is text, API returns image perfectly (hope so).
        Ex: pornhub Bori bay.'''
        await ctx.send(file=await self.alex_image(f'pornhub?text={text_1.replace(" ", "%20")}&text2={text_2.replace(" ", "%20")}'))

    @api.command(aliases=['dym'])
    async def didyoumean(self, ctx, search: str, did_you_mean: str):
        '''Google search 'Did you mean' meme.
        Arguments are required and raises an exception if one of them is misssing.
        Ex: didyoumean recursion recursion.'''
        await ctx.send(file=await self.alex_image(f'didyoumean?top={search}&bottom={did_you_mean}'))

    @api.command()
    async def achieve(self, ctx, *, text: str):
        '''Minecraft 'Achievement Get!' image maker.
        Challenge icon is random one of 44.
        Ex: challenge slept more than 6 hours.'''
        await ctx.send(file=await self.alex_image(f'achievement?text={text.replace(" ", "%20")}&icon={random.randint(1, 44)}'))

    @api.command()
    async def challenge(self, ctx, *, text):
        '''Minecraft 'Challenge Complete!' image maker.
        Challenge icon is random one of 45.
        Ex: challenge finished all to-do's.'''
        await ctx.send(file=await self.alex_image(f'challenge?text={text.replace(" ", "%20")}&icon={random.randint(1, 45)}'))

    @api.command(name='ascii')
    async def ascii_command(self, ctx, image: Optional[str]):
        '''Makes ASCII version of an user avatar.
        Ex: ascii Dosek'''
        image = await make_image_url(ctx, image)
        await ctx.send(file=await self.dagpi_image(f'ascii/?url={image}', 'ascii.png'))

    @api.command(name='discord')
    async def _discord(self, ctx, member: discord.Member, *, text: str):
        '''Discord message maker.
        Returns an image with text and user avatar you specified.
        Ex: discord Dosek this command is cool ngl.'''
        member = member or ctx.author
        await ctx.send(file=await self.dagpi_image(f'discord/?url={member.avatar_url}&username={member.display_name}&text={text}'))

    @api.command()
    async def caption(self, ctx, arg: Optional[str]):
        '''Caption for an image.
        This command describes a given image being just a piece of code.
        Can handle either image, member or even URL.
        Ex: **caption Dosek**'''
        image = await make_image_url(ctx, arg)
        cs = ctx.bot.session
        r = await cs.post(ctx.bot.config['API']['caption_api'], json={'Content': image, 'Type': 'CaptionRequest'})
        embed = ctx.bot.embed.default(ctx, title=await r.text())
        await ctx.send(embed=embed.set_image(url=image))

    @api.command()
    async def qr(self, ctx, url: Optional[str]):
        '''Makes QR-code of a given URL.
        A great way to make your friends get rickrolled!
        P.S: this command accepts only URLs.'''
        url = await make_image_url(ctx, url)
        cs = ctx.bot.session
        r = await cs.get(ctx.bot.config['API']['qr_api'] + url)
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(io, 'qr.png'))


def setup(bot):
    bot.add_cog(Images(bot))
