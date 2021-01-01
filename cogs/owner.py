from discord.ext.commands import Cog, ExtensionError, command
from dotenv import load_dotenv
load_dotenv()


class Owner(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @command(aliases=['l'], brief='Loads a module.')
    async def load(self, ctx, *, module: str):
        try:
            self.bot.load_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @command(aliases=['u'], brief='Unloads a module.')
    async def unload(self, ctx, *, module: str):
        try:
            self.bot.reload_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @command(name='reload', aliases=['r'], brief='Reloads a module.')
    async def _reload(self, ctx, *, module: str):
        try:
            self.bot.reload_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('🔄')


def setup(bot):
    bot.add_cog(Owner(bot))
