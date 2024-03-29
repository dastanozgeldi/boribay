from __future__ import annotations

import asyncio
from contextlib import ContextDecorator, suppress
from time import perf_counter
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from ..bot import Boribay

__all__ = ("Context",)


class Context(commands.Context):
    """Customized context for Boribay.

    Any usage case of context in the bot will be of this type.

    This class inherits from `discord.ext.commands.Context`.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.bot: Boribay
        self.timer = Timer(self)
        self.loading = Loading(self)

    @property
    async def db_latency(self) -> float:
        start = perf_counter()
        await self.bot.pool.fetchval("SELECT 1;")
        end = perf_counter()

        return end - start

    @property
    def db(self):
        return self.bot.db

    @property
    def config(self):
        return self.bot.config

    @property
    def user_cache(self):
        return self.bot.user_cache

    @property
    def guild_cache(self):
        return self.bot.guild_cache

    def embed(self, **kwargs: Any):
        return self.bot.embed(self, **kwargs)

    async def try_delete(self, message: discord.Message, **kwargs: Any):
        with suppress(AttributeError, discord.Forbidden, discord.NotFound):
            await message.delete(**kwargs)

    # idea: https://github.com/jay3332/ShrimpMaster/blob/master/core/bot.py#L320-L331
    async def getch(self, method: str, object_id: int, obj: str = "bot") -> None:
        if not object_id:
            return None

        obj = getattr(self, obj)

        try:
            _result = getattr(obj, "get_" + method)(object_id) or await getattr(
                obj, "fetch_" + method
            )(object_id)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return None

        return _result

    async def confirm(self, message: discord.Message, timeout: float = 10.0):
        msg = await self.send(message)
        emojis = {"✅": True, "❌": False}

        for e in emojis:
            await msg.add_reaction(e)

        payload = await self.bot.wait_for(
            "raw_reaction_add",
            check=lambda p: str(p.emoji) in emojis.keys()
            and p.user_id == self.author.id
            and p.message_id == msg.id,
            timeout=timeout,
        )

        with suppress(asyncio.TimeoutError):
            if emojis[str(payload.emoji)]:
                return True

            await self.try_delete(msg)
            await self.message.reply("The confirmation session was closed.")


class Timer(ContextDecorator):
    """The Timer class made to count the time spent to execute the known stuff.

    This class inherits from `contextlib.ContextDecorator`."""

    def __init__(self, ctx: Context):
        self.ctx = ctx

    async def __aenter__(self):
        self.start = perf_counter()

    async def __aexit__(self, *args: Any):
        self.end = perf_counter()
        await self.ctx.send(f"Done in `{self.end - self.start:.2f}s`")


class Loading(ContextDecorator):
    """Made to take some time for users while the command is getting executed.

    This class inherits from `contextlib.ContextDecorator`.
    """

    def __init__(self, ctx: Context, content: str = "Loading..."):
        self.ctx = ctx
        self.message = None
        self.content = content

    async def __aenter__(self):
        self.message = await self.ctx.send(
            f"<a:loading:837049644462374935> {self.content}"
        )

    async def __aexit__(self, *args):
        await self.ctx.try_delete(self.message)
