from .help import Help


def setup(bot):
    """
    Help extension setup method.
    """
    bot.add_cog(Help(bot))
