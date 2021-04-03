from contextlib import ContextDecorator
from time import perf_counter

from discord.ext.commands import Context as C


class Context(C):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer = Timer(self)
        self.config = self.bot.config

    @property
    def db(self):
        return self.bot.pool

    async def confirm(self, message):
        msg = await self.send(message)
        emojis = {'✅': True, '❌': False}

        for e in emojis.keys():
            await msg.add_reaction(e)

        payload = await self.bot.wait_for(
            'raw_reaction_add',
            check=lambda p: str(p.emoji) in emojis.keys() and p.user_id == self.author.id and p.message_id == msg.id,
        )

        if emojis[str(payload.emoji)] is True:
            return True


class Timer(ContextDecorator):
    def __init__(self, ctx):
        self.ctx = ctx

    async def __aenter__(self):
        self.start = perf_counter()

    async def __aexit__(self, *args):
        self.end = perf_counter()
        await self.ctx.send(f'Done in `{self.end - self.start:.2f}s`')
