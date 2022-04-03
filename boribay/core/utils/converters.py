import re
from contextlib import suppress
from copy import copy
from enum import Enum
from typing import List, Union

import discord
from discord.ext import commands
from PIL import ImageColor

__all__ = (
    'AuthorCheckConverter',
    'TimeConverter',
    'ImageConverter',
    'ColorConverter',
    'SettingsConverter'
)


async def is_valid_url(url: str, session):
    response = await session.head(url)
    return response.status == 200


def codepoint(codes: List[str]):
    if '200d' not in codes:
        return '-'.join(c for c in codes if c != 'fe0f')
    return '-'.join(codes)


async def emoji_to_url(char, *, session):
    path = codepoint([f'{ord(c):x}' for c in char])
    url = f'https://twemoji.maxcdn.com/v/latest/72x72/{path}.png'

    if await is_valid_url(url, session):
        return url

    return char


class Regex(Enum):
    """Enumeration of regexes to help us with converting."""

    RGB = r'\(?(\d+),?\s*(\d+),?\s*(\d+)\)?'
    EMOJI = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'
    URL = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


class ColorConverter(commands.Converter):
    """The color converter class created to convert string color values.

    This class inherits from `commands.Converter`.
    """
    async def convert(self, ctx, arg: str):
        with suppress(AttributeError):
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

        raise commands.BadArgument(f'Could not find any color that matches this: `{arg}`.')


class SettingsConverter(commands.Converter):
    async def convert(self, guild: discord.Guild, settings: dict):
        data = copy(settings[guild.id])

        for k, v in data.items():
            if k == 'autorole':
                data[k] = guild.get_role(v)

            elif k == 'embed_color':
                data[k] = hex(v)

            elif k == 'welcome_channel':
                data[k] = guild.get_channel(v)

        return data


class AuthorCheckConverter(commands.Converter):
    """The author checking converter to check for strangers who
    mention themselves everywhere. This isn't needed in economics.

    `[p]rob @user` command could serve here as an usage case.
    """

    async def convert(self, ctx: commands.Context, argument: str):
        member = await commands.MemberConverter().convert(ctx, argument)

        if ctx.author == member:
            raise commands.BadArgument('❌ Mentioning yourself is not the way.')

        return member


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


class ImageConverter(commands.Converter):
    """The image converter class created to convert argument into image.

    This class inherits from `commands.Converter`.
    """
    async def convert(
        self,
        ctx,
        argument: Union[discord.Emoji, str],
        *,
        return_url: bool = False
    ) -> Union[bytes, str]:
        """The function that does the actual thing we are expecting from this class.

        Parameters
        ----------
        ctx
            The context instance.
        argument : Union[discord.Emoji, str]
            The argument to convert into an image.
        return_url : bool, optional
            Whether to return URL for the image, by default False

        Returns
        -------
        Union[bytes, str]
            We may have a scenario where the user can ask for the image URL,
            i.e str, we expect this, but by default consider returning bytes.
        """
        try:
            mc = commands.MemberConverter()
            member = await mc.convert(ctx, argument)
            avatar = member.avatar_url_as(static_format='png', format='png', size=512)
            if return_url:
                return str(avatar)
            return await avatar.read()

        except (TypeError, commands.MemberNotFound):
            try:
                cs = ctx.bot.session
                url = await emoji_to_url(argument, session=cs)

                if re.match(Regex.URL, url):
                    if return_url:
                        return url
                    r = await cs.get(url)
                    image = await r.read()
                    return image

                if re.match(Regex.URL, argument):
                    if return_url:
                        return argument
                    r = await cs.get(argument)
                    image = await r.read()
                    return image

                elif re.match(Regex.EMOJI, argument):
                    ec = commands.PartialEmojiConverter()
                    emoji = await ec.convert(ctx, argument)
                    asset = emoji.url
                    if return_url:
                        return str(asset)
                    return await asset.read()

            except TypeError:
                return None

        return None
