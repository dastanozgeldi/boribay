import asyncio
from contextlib import ContextDecorator, suppress
from time import perf_counter
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from .bot import Boribay

__all__ = ('Context',)


class Context(commands.Context):
    """Customized context for Boribay.

    Any usage case of context in the bot will be of this type.

    This class inherits from `discord.ext.commands.Context`.
    """

    bot: 'Boribay'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer = Timer(self)
        self.loading = Loading(self)

    @property
    def db(self):
        return self.bot.pool

    @property
    def config(self):
        return self.bot.config

    @property
    def user_cache(self):
        return self.bot.user_cache

    @property
    def guild_cache(self):
        return self.bot.guild_cache

    def embed(self, **kwargs):
        return self.bot.embed(self, **kwargs)

    async def try_delete(self, message: discord.Message, **kwargs):
        with suppress(AttributeError, discord.Forbidden, discord.NotFound):
            await message.delete(**kwargs)

    # idea https://github.com/jay3332/ShrimpMaster/blob/master/core/bot.py#L320-L331
    async def getch(self, method: str, object_id: int, obj: str = 'bot'):
        if not object_id:
            return None

        obj = getattr(self, obj)

        try:
            _result = getattr(obj, 'get_' + method)(object_id) or await getattr(obj, 'fetch_' + method)(object_id)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return None

        return _result

    async def confirm(self, message: discord.Message, timeout: float = 10.0):
        msg = await self.send(message)
        emojis = {'✅': True, '❌': False}

        for e in emojis.keys():
            await msg.add_reaction(e)

        payload = await self.bot.wait_for(
            'raw_reaction_add',
            check=lambda p: str(p.emoji) in emojis.keys() and p.user_id == self.author.id and p.message_id == msg.id,
            timeout=timeout
        )

        with suppress(asyncio.TimeoutError):
            if emojis[str(payload.emoji)]:
                return True

            await self.try_delete(msg)
            await self.message.reply('The confirmation session was closed.')


class Timer(ContextDecorator):
    """The Timer class made to count the time spent to execute the known stuff.

    This class inherits from `contextlib.ContextDecorator`."""

    def __init__(self, ctx):
        self.ctx = ctx

    async def __aenter__(self):
        self.start = perf_counter()

    async def __aexit__(self, *args):
        self.end = perf_counter()
        await self.ctx.send(f'Done in `{self.end - self.start:.2f}s`')


class Loading(ContextDecorator):
    """The Loading class made to take some time for users while the command is getting executed.

    This class inherits from `contextlib.ContextDecorator`."""

    def __init__(self, ctx, message='Loading...'):
        self.ctx = ctx
        self.message = None
        self.content = message

    async def __aenter__(self):
        self.message = await self.ctx.send(f'<a:loading:837049644462374935> {self.content}')

    async def __aexit__(self, *args):
        await self.ctx.try_delete(self.message)
