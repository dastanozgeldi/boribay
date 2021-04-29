import contextlib
import copy
import re
import typing

import discord
import twemoji_parser
from discord.ext import commands
from PIL import ImageColor

from .exceptions import NotAnInteger, PastMinimum, NotEnough


class AuthorCheckConverter(commands.Converter):
    async def convert(self, ctx, argument):
        """The specific converter to check for strangers who
        mention themselves everywhere. This isn't needed in economics."""
        member = await commands.MemberConverter().convert(ctx, argument)

        if ctx.author == member:
            raise commands.BadArgument('❌ Mentioning yourself is not the way.')

        return member


def get_number(argument: str.lower, integer: bool = True):
    if not (argument := argument.replace(',', '').replace('+', '').strip()):
        raise ValueError()

    if argument.endswith('k'):
        argument = str(float(argument.rstrip('k')) * 1000)

    elif argument.endswith('m'):
        argument = str(float(argument.rstrip('m')) * 1000000)

    elif argument.endswith('b'):
        argument = str(float(argument.rstrip('b')) * 1000000000)

    if re.match(r'\de\d+', argument):
        number, expression = argument.split('e')
        number, expression = float(number), round(float(expression))
        argument = float(f'{number}e{expression}') if expression < 24 else 1e24

    argument = float(argument)
    return argument if not integer else round(argument)


def get_amount(_all: float, minimum: int, maximum: int, argument):
    argument = argument.lower().strip()

    if argument in ('all'):
        amount = round(_all)

    elif argument in ('half'):
        amount = round(_all / 2)

    elif argument.endswith('%'):
        percent = argument.rstrip('%')
        try:
            percent = float(percent) / 100

        except (TypeError, ValueError):
            raise NotAnInteger()

        else:
            amount = round(_all * percent)

    else:
        try:
            amount = get_number(argument)

        except ValueError:
            raise NotAnInteger()

    if amount > _all:
        raise NotEnough

    if amount <= 0:
        raise NotAnInteger

    if minimum <= amount <= maximum:
        return amount

    elif amount > maximum:
        return maximum

    raise PastMinimum(minimum)


def CasinoConverter(minimum: int = 100, maximum: int = 100_000):

    class _Wrapper(commands.Converter, int):
        async def convert(self, ctx, argument):
            _all = await ctx.db.fetchval('SELECT wallet FROM users WHERE user_id = $1', ctx.author.id)
            amount = get_amount(_all, minimum, maximum, argument)

            return amount

    return _Wrapper


class SettingsConverter(commands.Converter):
    async def convert(self, guild: discord.Guild, settings: dict):
        data = copy.copy(settings[guild.id])

        for k, v in data.items():
            if k == 'autorole':
                data[k] = guild.get_role(v)

            elif k == 'embed_color':
                data[k] = hex(v)

            elif k in ('welcome_channel', 'automeme', 'logging_channel'):
                data[k] = guild.get_channel(v)

        return data


class ValueConverter(commands.Converter):
    async def convert(self, ctx, setting: str, value: str):
        g = ctx.guild

        try:
            if setting == 'autorole':
                value = g.get_role(value)

            elif setting == 'embedcolor':
                value = await ColorConverter().convert(ctx, value)

            elif setting in ('welcomechannel', 'automeme', 'logging'):
                value = g.get_channel(value)

            return value

        except ValueError:
            raise commands.BadArgument(
                f'Unable to convert {value} into {setting} value.')


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        time = 0
        time_dict = {'h': 3600, 's': 1, 'm': 60, 'd': 86400}
        matches = re.findall(r'(?:(\d{1,5})(h|s|m|d))+?', argument.lower())

        for v, k in matches:
            try:
                time += time_dict[k] * float(v)

            except KeyError:
                raise commands.BadArgument(
                    f'{k} is an invalid time-key! h/m/s/d are valid.')

            except ValueError:
                raise commands.BadArgument(f'{v} is not a number!')

        return time


class ColorConverter(commands.Converter):
    async def convert(self, ctx, arg: str):
        with contextlib.suppress(AttributeError):
            match = re.match(r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?', arg)
            check = all(0 <= int(x) <= 255 for x in match.groups())

        if match and check:
            return discord.Color.from_rgb([int(i) for i in match.groups()])

        converter = commands.ColorConverter()
        try:
            result = await converter.convert(ctx, arg)
        except commands.BadColourArgument:
            try:
                color = ImageColor.getrgb(arg)
                result = discord.Color.from_rgb(*color)
            except ValueError:
                result = None

        if result:
            return result

        raise commands.BadArgument(
            f'Could not find any color that matches this: `{arg}`.')


class ImageURLConverter(commands.Converter):
    async def convert(self, ctx, arg: typing.Union[discord.Emoji, str]):
        try:
            mconv = commands.MemberConverter()
            m = await mconv.convert(ctx, arg)
            image = str(m.avatar_url_as(
                static_format='png', format='png', size=512))
            return image

        except (TypeError, commands.MemberNotFound):
            try:
                url = await twemoji_parser.emoji_to_url(arg, include_check=True)

                if re.match(ctx.bot.regex['URL_REGEX'], url):
                    return url

                if re.match(ctx.bot.regex['URL_REGEX'], arg):
                    return arg

                elif re.match(ctx.bot.regex['EMOJI_REGEX'], arg):
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
                cs = ctx.bot.session

                if re.match(ctx.bot.regex['URL_REGEX'], url):
                    r = await cs.get(url)
                    image = await r.read()
                    return image

                if re.match(ctx.bot.regex['URL_REGEX'], arg):
                    r = await cs.get(arg)
                    image = await r.read()
                    return image

                elif re.match(ctx.bot.regex['EMOJI_REGEX'], arg):
                    econv = commands.PartialEmojiConverter()
                    e = await econv.convert(ctx, arg)
                    asset = e.url
                    image = await asset.read()
                    return image

            except TypeError:
                return None

        return None
