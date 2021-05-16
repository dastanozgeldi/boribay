from .events import Events


def setup(bot):
    bot.add_cog(Events(bot))
