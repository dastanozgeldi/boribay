from .settings import Settings


# Setting up the cog.
def setup(bot):
    bot.add_cog(Settings())
