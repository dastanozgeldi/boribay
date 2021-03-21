import textwrap
from io import BytesIO

from discord import File
from googletrans import Translator
from jishaku.functools import executor_function
from PIL import Image, ImageDraw, ImageFont, ImageOps
from polaroid import Image as PI
from wand.image import Image as WI

from utils import ImageConverter, ImageURLConverter


async def make_image_url(ctx, argument: str):
    converter = ImageURLConverter()
    image = await converter.convert(ctx, argument)

    if not image:
        if ctx.message.attachments:
            image = ctx.message.attachments[0].url
        else:
            image = str(ctx.author.avatar_url_as(static_format='png', format='png', size=512))

    return image


async def make_image(ctx, argument: str):
    converter = ImageConverter()
    image = await converter.convert(ctx, argument)

    if not image:
        if ctx.message.attachments:
            layout = ctx.message.attachments[0]
        else:
            layout = ctx.author.avatar_url_as(static_format='png', format='png', size=256)

        image = await layout.read()

    return image


def polaroid_filter(ctx, image: bytes, *, method: str, args: list = None, kwargs: dict = None):
    args = args or []
    kwargs = kwargs or {}
    img = PI(image)
    filt = getattr(img, method)
    filt(*args, **kwargs)

    return File(BytesIO(img.save_bytes()), f'{method}.png')


class Manip:

    @staticmethod
    @executor_function
    def translate(language, *, sentence):
        t = Translator()
        return t.translate(sentence, dest=language)

    @staticmethod
    @executor_function
    def pixelate(image: BytesIO):
        with Image.open(image) as im:
            small = im.resize((32, 32), resample=Image.BILINEAR)
            result = small.resize(im.size, Image.NEAREST)
            buffer = BytesIO()
            result.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def wide(image: BytesIO):
        with WI(file=image) as im:
            w, h = im.size
            im.resize(w * 2, int(h / 2))
            buffer = BytesIO()
            im.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def circlize(image: BytesIO):
        mask = Image.open('./data/layouts/circle-mask.png').convert('L')

        with Image.open(image) as im:
            output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
            output.putalpha(mask)
            buffer = BytesIO()
            output.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def welcome(member: BytesIO, top_text, bottom_text):
        font = ImageFont.truetype('./data/fonts/arial_bold.ttf', size=20)
        join_w, member_w = font.getsize(bottom_text)[0], font.getsize(top_text)[0]

        with Image.new('RGB', (600, 400)) as card:
            card.paste(Image.open(member).resize((263, 263)), (170, 32))
            draw = ImageDraw.Draw(card)
            draw.text(((600 - join_w) / 2, 309), bottom_text, (255, 255, 255), font=font)
            draw.text(((600 - member_w) / 2, 1), top_text, (169, 169, 169), font=font)
            buffer = BytesIO()
            card.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def whyareyougae(author: BytesIO, member: BytesIO):
        author = Image.open(author)

        with Image.open('./data/layouts/wayg.jpg') as img:
            img.paste(author, (507, 103))
            img.paste(Image.open(member).resize((128, 128)), (77, 120))
            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def fiveguysonegirl(author: BytesIO, member: BytesIO):
        author = Image.open(author)

        with Image.open('./data/layouts/5g1g.png') as img:
            img.paste(Image.open(member).resize((128, 128)), (500, 275))

            for i in [(31, 120), (243, 53), (438, 85), (637, 90), (815, 20)]:
                img.paste(author, i)

            buffer = BytesIO()
            img.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def wanted(image: BytesIO):
        image = Image.open(image).resize((189, 205))

        with Image.open('./data/layouts/wanted.png') as img:
            img.paste(image, (73, 185))
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function  # 395, 206 - knocked out; 236, 50 - winner
    def fight(winner: BytesIO, knocked_out: BytesIO):
        winner = Image.open(winner).resize((40, 40))
        knocked_out = Image.open(knocked_out).resize((60, 60))

        with Image.open('./data/layouts/fight.jpg') as img:
            img.paste(winner, (236, 50))
            img.paste(knocked_out.rotate(-90), (395, 206))
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def clyde(txt: str):
        font = ImageFont.truetype('./data/fonts/whitneybook.otf', 18)

        with Image.open('./data/layouts/clyde.png') as img:
            draw = ImageDraw.Draw(img)
            draw.text((72, 33), txt, (255, 255, 255), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def typeracer(txt: str):
        font = ImageFont.truetype('./data/fonts/monoid.ttf', size=30)
        w, h = font.getsize_multiline(txt)

        with Image.new('RGB', (w + 10, h + 10)) as base:
            canvas = ImageDraw.Draw(base)
            canvas.multiline_text((5, 5), txt, font=font)
            buffer = BytesIO()
            base.save(buffer, 'png', optimize=True)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def theory(txt: str):
        wrapped = textwrap.wrap(txt, 24)
        font = ImageFont.truetype('./data/fonts/arial_bold.ttf', 30)

        with Image.open('./data/layouts/lisa.jpg') as img:
            draw = ImageDraw.Draw(img)
            draw.text((161, 72), '\n'.join(wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def drake(no: str, yes: str):
        no_wrapped = textwrap.wrap(text=no, width=13)
        yes_wrapped = textwrap.wrap(text=yes, width=13)
        font = ImageFont.truetype('./data/fonts/arial_bold.ttf', size=28)

        with Image.open('./data/layouts/drake.jpg') as img:
            draw = ImageDraw.Draw(img)
            draw.text((270, 10), '\n'.join(no_wrapped), (0, 0, 0), font=font)
            draw.text((270, 267), '\n'.join(yes_wrapped), (0, 0, 0), font=font)
            buffer = BytesIO()
            img.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def jail(image: BytesIO):
        layout = WI(filename='./data/layouts/jailbars.png')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.3)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def press_f(image: BytesIO):
        layout = WI(filename='./data/layouts/f.png')

        with WI(file=image) as img:
            img.resize(52, 87)
            img.rotate(-5)
            buffer = BytesIO()
            layout.watermark(img, left=310, top=71)
            layout.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def rainbow(image: BytesIO):
        layout = WI(filename='./data/layouts/rainbow.png')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.5)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
    def communist(image: BytesIO):
        layout = WI(filename='./data/layouts/communist-flag.jpg')

        with WI(file=image) as img:
            w, h = img.size
            layout.resize(w, h)
            img.watermark(layout, 0.7)
            buffer = BytesIO()
            img.save(file=buffer)

        buffer.seek(0)
        return buffer

    @staticmethod
    @executor_function
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
