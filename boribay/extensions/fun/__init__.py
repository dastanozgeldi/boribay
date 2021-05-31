from .fun import Fun


def setup(bot):
    """
    Fun extension setup method.
    """
    bot.add_cog(Fun(bot))
