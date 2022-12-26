from .fun import Fun


# Setting up the cog.
async def setup(bot):
    await bot.add_cog(Fun(bot))
