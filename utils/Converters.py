import re
import discord
import contextlib
import twemoji_parser
from discord.ext import commands
from utils.CustomContext import CustomContext

URL_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
RGB_REGEX = '\(?(\d+),?\s*(\d+),?\s*(\d+)\)?'
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
    async def convert(self, ctx: CustomContext, degree: int = 90):
        if int(degree) > 360:
            degree = 360
        elif int(degree) < -360:
            degree = -360
        else:
            degree = int(degree)
        return degree


class ColorConverter(commands.Converter):
    async def convert(self, ctx: CustomContext, arg: str):
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


class ImageConverter(commands.Converter):
    async def convert(self, ctx: CustomContext, argument: str):
        try:
            member_converter = commands.MemberConverter()
            member = await member_converter.convert(ctx, argument)
            asset = member.avatar_url_as(static_format="png", format="png", size=512)
            image = await asset.read()
            return image

        except (commands.MemberNotFound, TypeError):
            try:
                emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"
                url = await twemoji_parser.emoji_to_url(argument, include_check=True)
                if re.match(URL_REGEX, url):
                    async with ctx.bot.session.get(url) as response:
                        byte_image = await response.read()
                        return byte_image

                if re.match(URL_REGEX, argument):
                    async with ctx.bot.session.get(argument) as response:
                        image = await response.read()
                        return image

                elif re.match(emoji_regex, argument):
                    emoji_converter = commands.PartialEmojiConverter()
                    emoji = await emoji_converter.convert(ctx, argument)
                    asset = emoji.url
                    image = await asset.read()
                    return image

            except TypeError:
                return None
        return None


class MemberRoles(commands.MemberConverter):
    async def convert(self, ctx: CustomContext, argument: str):
        member = await super().convert(ctx, argument)
        return [role.name for role in member.roles[1:]]


class BoolConverter(commands.Converter):
    async def convert(self, ctx: CustomContext, argument: str):
        if argument in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif argument in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False
