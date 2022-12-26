from .developer import Developer
from .jishaku import Jishaku


# Setting up developer extensions.
async def setup(bot):
    await bot.add_cog(Jishaku(bot=bot))
    await bot.add_cog(Developer())
