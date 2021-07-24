import asyncio
import functools
import textwrap
from io import BytesIO
from typing import Union

import discord
from PIL import Image, ImageColor, ImageDraw, ImageFont
from polaroid import Image as PI
from wand.image import Image as WI

from .converters import ImageConverter

FONT_PATH = './data/fonts'
IMAGE_PATH = './data/layouts'


def executor(func):
    """Wraps a sync function into an async function.

    This provides us non-blocking wrapped functions.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """Sync function wrapper."""
        loop = asyncio.get_event_loop()
        partial_function = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, partial_function)

    return wrapper


def color_exists(color: str) -> bool:
    """Checking whether the given color exists is important in some commands.

    This is done by using `ImageColor.getrgb` method and try/catch.

    Args:
        color (str): The color to check existence of.

    Returns:
        bool: The boolean according to the color value.
    """
    try:
        ImageColor.getrgb(color)
        return True
    except ValueError:
        return False


async def make_image(
    ctx,
    argument: str,
    *,
    return_url: bool = False
) -> Union[bytes, str]:
    converter = ImageConverter()
    image = await converter.convert(ctx, argument, return_url=return_url)

    if not image:
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            image = attachment.url if return_url else await attachment.read()
        else:
            avatar = ctx.author.avatar_url_as(static_format='png', format='png', size=512)
            image = str(avatar) if return_url else await avatar.read()

    return image


def polaroid_filter(image: bytes, *, method: str, args: list = [], kwargs: dict = {}):
    image = PI(image)
    func = getattr(image, method)
    func(*args, **kwargs)
    byt = image.save_bytes()
    return discord.File(byt, f'{method}.png')


class Manip:
    """A set of static methods used in the Image extension."""

    @staticmethod
    @executor
    def typeracer(txt: str):
        font = ImageFont.truetype(f'{FONT_PATH}/monoid.ttf', size=30)
        w, h = font.getsize_multiline(txt)

        with Image.new('RGB', (w + 10, h + 10)) as base:
            canvas = ImageDraw.Draw(base)
            canvas.multiline_text((5, 5), txt, font=font)
            buffer = BytesIO()
            base.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def welcome(top_text: str, bottom_text: str, member_avatar: BytesIO):
        font = ImageFont.truetype(f'{FONT_PATH}/arial_bold.ttf', size=20)
        join_w, member_w = font.getsize(bottom_text)[0], font.getsize(top_text)[0]

        with Image.new('RGB', (600, 400)) as card:
            card.paste(Image.open(member_avatar).resize((263, 263)), (170, 32))
            draw = ImageDraw.Draw(card)
            draw.text(((600 - join_w) / 2, 309), bottom_text, (255, 255, 255), font=font)
            draw.text(((600 - member_w) / 2, 1), top_text, (169, 169, 169), font=font)
            buffer = BytesIO()
            card.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def pixelate(image: BytesIO):
        with Image.open(image) as im:
            small = im.resize((32, 32), resample=Image.BILINEAR)
            result = small.resize(im.size, Image.NEAREST)
            buffer = BytesIO()
            result.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def whyareyougae(author: BytesIO, member: BytesIO):
        author = Image.open(author)

        with Image.open(f'{IMAGE_PATH}/wayg.jpg') as img:
            img.paste(author, (507, 103))
            img.paste(Image.open(member).resize((128, 128)), (77, 120))
            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def fiveguysonegirl(author: BytesIO, member: BytesIO):
        author = Image.open(author)

        with Image.open(f'{IMAGE_PATH}/5g1g.png') as img:
            img.paste(Image.open(member).resize((128, 128)), (500, 275))

            for i in [(31, 120), (243, 53), (438, 85), (637, 90), (815, 20)]:
                img.paste(author, i)

            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def wanted(image: BytesIO):
        image = Image.open(image).resize((189, 205))

        with Image.open(f'{IMAGE_PATH}/wanted.png') as img:
            img.paste(image, (73, 185))
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor  # 395, 206 - knocked out; 236, 50 - winner
    def fight(winner: BytesIO, knocked_out: BytesIO):
        winner = Image.open(winner).resize((40, 40))
        knocked_out = Image.open(knocked_out).resize((60, 60))

        with Image.open(f'{IMAGE_PATH}/fight.jpg') as img:
            img.paste(winner, (236, 50))
            img.paste(knocked_out.rotate(-90), (395, 206))
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def clyde(txt: str):
        font = ImageFont.truetype(f'{FONT_PATH}/whitneybook.otf', 18)

        with Image.open(f'{IMAGE_PATH}/clyde.png') as img:
            draw = ImageDraw.Draw(img)
            draw.text((72, 33), txt, (255, 255, 255), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def drake(no: str, yes: str):
        no_wrapped = textwrap.wrap(text=no, width=13)
        yes_wrapped = textwrap.wrap(text=yes, width=13)
        font = ImageFont.truetype(f'{FONT_PATH}/arial_bold.ttf', size=28)

        with Image.open(f'{IMAGE_PATH}/drake.jpg') as img:
            draw = ImageDraw.Draw(img)
            draw.text((270, 10), '\n'.join(no_wrapped), (0, 0, 0), font=font)
            draw.text((270, 267), '\n'.join(yes_wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def jail(image: BytesIO):
        layout = WI(filename=f'{IMAGE_PATH}/jailbars.png')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.3)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def press_f(image: BytesIO):
        layout = WI(filename=f'{IMAGE_PATH}/f.png')

        with WI(file=image) as img:
            img.resize(52, 87)
            img.rotate(-5)
            buffer = BytesIO()
            layout.watermark(img, left=310, top=71)
            layout.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def rainbow(image: BytesIO):
        layout = WI(filename=f'{IMAGE_PATH}/rainbow.png')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.5)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def communist(image: BytesIO):
        layout = WI(filename=f'{IMAGE_PATH}/communist-flag.jpg')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.7)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor
    def swirl(degree: int, image: BytesIO):
        if degree > 360:
            degree = 360

        elif degree < -360:
            degree = -360

        with WI(file=image) as img:
            img.swirl(degree=degree)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer
