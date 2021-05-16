from .jishaku import Jishaku


def setup(bot):
    bot.add_cog(Jishaku(bot=bot))
