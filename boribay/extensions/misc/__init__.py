from .misc import Miscellaneous


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Miscellaneous())
