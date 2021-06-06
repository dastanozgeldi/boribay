from .images import Images


def setup(bot):
    """
    Images extension setup method.
    """
    bot.add_cog(Images())
