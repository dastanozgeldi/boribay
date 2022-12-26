from .help import Help


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Help(bot))
