from .developer import Developer
from .jishaku import Jishaku


# Setting up developer extensions.
def setup(bot):
    bot.add_cog(Jishaku(bot=bot))
    bot.add_cog(Developer())
