from .help import Help


# Setting up the cog.
def setup(bot):
    bot.add_cog(Help(bot))
