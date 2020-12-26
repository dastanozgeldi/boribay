import time
from contextlib import ContextDecorator
from discord.ext import commands


class CustomContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeit = timeit(self)


class timeit(ContextDecorator):
    def __init__(self, ctx):
        self.ctx = ctx

    async def __aenter__(self):
        self.start = time.perf_counter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()

        await self.ctx.send(f'Finished in `{self.end - self.start:,.2f}`s')
