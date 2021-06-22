import asyncio
import logging
import re
import time
from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
import discord
from boribay.core import Boribay, Context
from discord.ext import commands

from .constants import FLAGS

API_URL = 'https://translation.googleapis.com'

logger = logging.getLogger('bot.translate')


class TranslatorAPIError(Exception):
    """Raised when the API is facing some issues."""
    pass


class FlagTranslation(commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> List[str]:
        res = []
        if argument in FLAGS:
            res = FLAGS[argument]['code'].upper()
        else:
            for language in FLAGS:
                if FLAGS[language]['name'].lower() in argument.lower():
                    res = FLAGS[language]['code']
                    break
                if FLAGS[language]['country'].lower() in argument.lower():
                    res = FLAGS[language]['code']
                    break
                if not FLAGS[language]['code']:
                    continue
                if FLAGS[language]['code'] in argument.lower() and len(argument) == 2:
                    res = FLAGS[language]['code']
                    break
        if not res:
            raise commands.BadArgument(f'Language "{argument}" not found.')

        return res


class TranslatorAPI:
    def __init__(self, bot: Boribay, token: Optional[str] = None):
        self.bot = bot
        self._token = token or bot.config.api.google_key
        self.count = bot.counter['translated']

    async def detect_language(self, text: str) -> List[List[Dict[str, str]]]:
        p = {'q': text, 'key': self._token}
        url = API_URL + '/language/translate/v2/detect'
        r = await self.bot.session.get(url, params=p)
        data = await r.json()

        if 'error' in data:
            msg = data['error']['message']
            logger.error(msg)
            raise TranslatorAPIError(msg)

        return data['data']['detections']

    async def translation_embed(
        self,
        ctx: Context,
        translation: Tuple[str, str, str],
        requestor: Optional[Union[discord.Member, discord.User]] = None
    ) -> discord.Embed:
        embed = ctx.embed(description=translation[0])
        embed.set_author(
            name=ctx.author.display_name + ' said:',
            icon_url=str(ctx.author.avatar_url)
        )
        details = f'{translation[1].upper()} to {translation[2].upper()} | Requested by '
        if requestor:
            details += str(requestor)
        else:
            details += str(ctx.author)

        embed.set_footer(text=details)
        return embed

    async def translate_text(
        self,
        from_language: str,
        target: str,
        text: str
    ) -> Optional[str]:
        p = {
            'q': text,
            'target': target,
            'key': self._token,
            'format': 'text',
            'source': from_language
        }
        url = API_URL + '/language/translate/v2'
        try:
            r = await self.bot.session.get(url, params=p)
            data = await r.json()
        except Exception:
            return None

        if 'error' in data:
            msg = data['error']['message']
            logger.error(msg)
            raise TranslatorAPIError(msg)

        if 'data' in data:
            result = data['data']['translations'][0]['translatedText']
        return result
