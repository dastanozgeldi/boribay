from .translate import Translate


# Setting up the cog.
def setup(bot):
    bot.add_cog(Translate(bot))
