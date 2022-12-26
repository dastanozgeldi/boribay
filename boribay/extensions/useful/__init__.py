from .useful import Useful


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Useful(bot))
