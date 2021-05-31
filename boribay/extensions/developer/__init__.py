from .developer import Developer


def setup(bot):
    """
    Developer extension setup method.
    """
    bot.add_cog(Developer(bot))
