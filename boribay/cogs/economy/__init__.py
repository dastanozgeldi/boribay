from .economy import Economics


def setup(bot):
    bot.add_cog(Economics(bot))
