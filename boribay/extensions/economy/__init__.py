from .economy import Economics


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Economics(bot))
