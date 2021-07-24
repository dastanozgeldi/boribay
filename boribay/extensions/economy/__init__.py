from .economy import Economics


# Setting up the cog.
def setup(bot):
    bot.add_cog(Economics(bot))
