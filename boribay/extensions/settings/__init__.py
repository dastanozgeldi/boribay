from .settings import Settings


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Settings())
