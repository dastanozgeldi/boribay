from discord.ext.commands import command
from utils.Cog import Cog
from typing import Optional
from utils.Manipulation import make_image
from polaroid import Image as PI
from discord import File
from io import BytesIO
from random import choices


class Filters(Cog):
	"""An extension which features were made using Polaroid Image Manipulation Module."""

	def __init__(self, bot):
		self.bot = bot
		self.name = '🎨 Filters'

	@staticmethod
	def polaroid_filter(ctx, image: bytes, *, method: str, fn: str, args: list = None, kwargs: dict = None):
		args = args or []
		kwargs = kwargs or {}
		img = PI(image)
		method = getattr(img, method)
		method(*args, **kwargs)
		buffer = BytesIO(img.save_bytes())
		file = File(fp=buffer, filename=f'{fn}.png')
		return file

	@command()
	async def noise(self, ctx, image: Optional[str]):
		"""Randomly adds noises to an image.
		Args: image (str): A specified image, either user, emoji or attachment."""
		image = await make_image(ctx, image)
		file = self.polaroid_filter(ctx, image, method='add_noise_rand', fn='noise')
		await ctx.send(file=file)

	@command()
	async def invert(self, ctx, image: Optional[str]):
		"""Inverts given image."""
		image = await make_image(ctx, image)
		file = self.polaroid_filter(ctx, image, method='invert', fn='inverted')
		await ctx.send(file=file)

	@command(aliases=['gs'])
	async def grayscale(self, ctx, image: Optional[str]):
		"""Adds a greyscale filter to an image."""
		image = await make_image(ctx, image)
		file = self.polaroid_filter(ctx, image, method='grayscale', fn='grayscaled')
		await ctx.send(file=file)

	@command()
	async def monochrome(self, ctx, r: Optional[int], g: Optional[int], b: Optional[int], image: Optional[str]):
		"""Adds a monochrome filter to an image.
		Takes absolutely random colors if any of r, g, b not specified.
		So be careful!"""
		if not all((r, g, b)):
			r, g, b = choices(range(0, 255), k=3)
		image = await make_image(ctx, image)
		file = self.polaroid_filter(
			ctx,
			image,
			method='monochrome',
			fn='monochromed',
			kwargs={'r_offset': r, 'g_offset': g, 'b_offset': b}
		)
		await ctx.send(f'Taken RGB parameters: {r, g, b}', file=file)

	@command()
	async def solarize(self, ctx, image: Optional[str]):
		"""As it says, solarizes an image.
		Args: image (str): A specified image, either user, emoji or attachment."""
		image = await make_image(ctx, image)
		file = self.polaroid_filter(ctx, image, method='solarize', fn='solarized')
		await ctx.send(file=file)

	@command()
	async def brighten(self, ctx, image: Optional[str]):
		"""As it says, brightens an image.
		Args: image (str): A specified image, either user, emoji or attachment."""
		image = await make_image(ctx, image)
		file = self.polaroid_filter(ctx, image, method='brighten', fn='brightened', kwargs={'treshold': 69})
		await ctx.send(file=file)


def setup(bot):
	bot.add_cog(Filters(bot))
