from .moderation import Moderation


# Setting up the cog.
def setup(bot):
    bot.add_cog(Moderation())
