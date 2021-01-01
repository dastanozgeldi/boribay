import textwrap
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from utils.Converters import ImageConverter, ImageURLConverter


async def make_image_url(ctx, arg: str):
    c = ImageURLConverter()
    image = await c.convert(ctx, arg)
    if not image:
        if ctx.message.attachments:
            image = ctx.message.attachments[0].url
            return image
        else:
            image = str(ctx.author.avatar_url_as(static_format='png', format='png', size=512))
            return image
    else:
        return image


async def make_image(ctx, argument: str):
    converter = ImageConverter()
    image = await converter.convert(ctx, argument)
    if not image:
        if ctx.message.attachments:
            layout = ctx.message.attachments[0]
            image = await layout.read()
            return image
        else:
            layout = ctx.author.avatar_url_as(static_format='png', format='png', size=512)
            image = await layout.read()
            return image
    else:
        return image


class Manip:

    @staticmethod
    def clyde(txt: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open('./data/assets/clyde.png') as img:
            font = ImageFont.truetype('./data/fonts/whitneybook.otf', 18)
            draw = ImageDraw.Draw(img)
            draw.text((72, 33), txt, (255, 255, 255), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')
        buffer.seek(0)
        return buffer

    @staticmethod
    def theory(txt: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open('./data/assets/lisa.jpg') as img:
            wrapped = textwrap.wrap(txt, 24)
            font = ImageFont.truetype('./data/fonts/impact.ttf', 30)
            draw = ImageDraw.Draw(img)
            draw.text((161, 72), '\n'.join(wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')
        buffer.seek(0)
        return buffer

    @staticmethod
    def drake(no: str, yes: str):
        Image.MAX_IMAGE_PIXELS = (1200 * 1000)
        with Image.open('./data/assets/drake.jpg') as img:
            no_wrapped = textwrap.wrap(text=no, width=13)
            yes_wrapped = textwrap.wrap(text=yes, width=13)
            font = ImageFont.truetype('./data/fonts/impact.ttf', size=28)
            draw = ImageDraw.Draw(img)
            draw.text((275, 10), '\n'.join(no_wrapped), (0, 0, 0), font=font)
            draw.text((275, 267), '\n'.join(yes_wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')
        buffer.seek(0)
        return buffer
