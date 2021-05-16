from .errors import ErrorHandler


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
