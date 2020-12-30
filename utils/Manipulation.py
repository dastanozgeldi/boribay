import textwrap
from io import BytesIO
from polaroid import Image as PI

from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from wand.image import Image as WI
from utils.Converters import ImageConverter, Degree
from utils.CustomContext import CustomContext


async def make_image(ctx: CustomContext, argument: str):
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
    def facetime(first: bytes, second: bytes):
        with WI(file=BytesIO(first)) as img:
            if (img.width * img.height) >= 1200 * 1000:
                raise commands.BadArgument('Too large image.')

        image = PI(first)
        if image.size != (512, 512):
            image.resize(512, 512, 5)

        image_two = PI(second)
        if image_two.size != (128, 128):
            image_two.resize(128, 128, 5)

        buttons = PI('./data/assets/facetime.png')
        buttons.resize(512, 512, 5)
        image.watermark(image_two, 376, 8)
        image.watermark(buttons, 0, 200)
        io = BytesIO(image.save_bytes())

        return io

    @staticmethod
    def swirl(image: BytesIO, degrees: Degree):
        with WI(file=image) as img:
            if(img.width * img.height) >= (1200 * 1000):
                raise commands.BadArgument('Too large image.')
            img.swirl(degree=degrees)
            buffer = BytesIO()
            img.save(file=buffer)
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
