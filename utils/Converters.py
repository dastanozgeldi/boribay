import re
import typing
import discord
import contextlib
import twemoji_parser
from discord.ext import commands

URL_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
RGB_REGEX = '\(?(\d+),?\s*(\d+),?\s*(\d+)\)?'
EMOJI_REGEX = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'
time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument(f"{k} is an invalid time-key! h/m/s/d are valid.")
            except ValueError:
                raise commands.BadArgument(f"{v} is not a number!")
        return time


class Degree(commands.Converter):
    async def convert(self, ctx, degree: int = 90):
        if int(degree) > 360:
            degree = 360
        elif int(degree) < -360:
            degree = -360
        else:
            degree = int(degree)
        return degree


class ColorConverter(commands.Converter):
    async def convert(self, ctx, arg: str):
        with contextlib.suppress(AttributeError):
            match = re.match(RGB_REGEX, arg)
            check = all(0 <= int(x) <= 255 for x in match.groups())

        if match and check:
            return discord.Color.from_rgb([int(i) for i in match.groups()])

        converter = commands.ColorConverter()
        result = await converter.convert(ctx, arg)

        if result:
            return result

        raise commands.BadArgument('Could not find any color that matches this.')


class ImageURLConverter(commands.Converter):
    async def convert(self, ctx, arg: typing.Union[discord.Emoji, str]):
        try:
            mconv = commands.MemberConverter()
            m = await mconv.convert(ctx, arg)
            image = str(m.avatar_url_as(static_format='png', format='png', size=512))
            return image

        except (TypeError, commands.MemberNotFound):
            try:
                url = await twemoji_parser.emoji_to_url(arg, include_check=True)
                if re.match(URL_REGEX, url):
                    return url
                if re.match(URL_REGEX, arg):
                    return arg
                elif re.match(EMOJI_REGEX, arg):
                    econv = commands.PartialEmojiConverter()
                    e = await econv.convert(ctx, arg)
                    image = str(e.url)
                    return image
            except TypeError:
                return None

        return None


class ImageConverter(commands.Converter):
    async def convert(self, ctx, arg: typing.Union[discord.Emoji, str]):
        try:
            mconv = commands.MemberConverter()
            m = await mconv.convert(ctx, arg)
            pfp = m.avatar_url_as(static_format='png', format='png', size=512)
            image = await pfp.read()
            return image

        except (TypeError, commands.MemberNotFound):
            try:
                url = await twemoji_parser.emoji_to_url(arg, include_check=True)
                if re.match(URL_REGEX, url):
                    cs = ctx.bot.session
                    r = await cs.get(url)
                    image = await r.read()
                    return image
                if re.match(URL_REGEX, arg):
                    cs = ctx.bot.session
                    r = await cs.get(arg)
                    image = await r.read()
                    return image
                elif re.match(EMOJI_REGEX, arg):
                    econv = commands.PartialEmojiConverter()
                    e = await econv.convert(ctx, arg)
                    asset = e.url
                    image = await asset.read()
                    return image
            except TypeError:
                return None

        return None


class MemberRoles(commands.MemberConverter):
    async def convert(self, ctx, argument: str):
        member = await super().convert(ctx, argument)
        return [role.name for role in member.roles[1:]]


class BoolConverter(commands.Converter):
    async def convert(self, ctx, argument: str):
        if argument in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif argument in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False
