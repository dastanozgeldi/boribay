from contextlib import ContextDecorator
from time import perf_counter
from discord.ext import commands


class Context(commands.Context):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.timer = Timer(self)


class Timer(ContextDecorator):
	def __init__(self, ctx):
		self.ctx = ctx

	async def __aenter__(self):
		self.start = perf_counter()

	async def __aexit__(self, *args):
		self.end = perf_counter()
		await self.ctx.send(f'Done in `{self.end - self.start:.2f}s`')
