import logging
from typing import Optional, Union

import discord
from boribay.core import Boribay, Cog, Context
from discord.ext import commands

from .api import FlagTranslation, TranslatorAPI, TranslatorAPIError


class Translate(TranslatorAPI, Cog):
    """Translate the text using this extension."""

    icon = '🌐'

    def __init__(self, bot: Boribay):
        self.bot = bot

    @commands.command()
    async def translate(
        self,
        ctx: Context,
        to_language: FlagTranslation,
        *,
        message: Union[discord.Message, str]
    ) -> None:
        if not self._token:
            return await ctx.send('The bot owner did not set the API key yet!')

        author = ctx.author
        if isinstance(message, discord.Message):
            author = message.author
            message = message.clean_content

        try:
            detected = await self.detect_language(message)
        except TranslatorAPIError as exc:
            return await ctx.send(str(exc))

        from_language = detected[0][0]['language']
        if to_language == from_language:
            return await ctx.send(f'{to_language} to {from_language}? Are you serious?')

        try:
            translated = await self.translate_text(from_language, to_language, message)
        except TranslatorAPIError as exc:
            return await ctx.send(str(exc))

        translation = (translated, from_language, to_language)
        embed = await self.translation_embed(author, translation)
        await ctx.send(embed=embed)
