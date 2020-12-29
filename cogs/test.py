from discord.ext import commands
from discord.ext.commands import BucketType, command
from utils.Converters import MemberRoles
from utils.CustomCog import Cog


class ImageTest(Cog, name='Testing', command_attrs=dict(hidden=True, cooldown=commands.Cooldown(1, 5, BucketType.channel))):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🧪 Testing'
        self.asset = './data/assets/'
        self.image = './data/images/'
        self.font = './data/fonts/'

    @command()
    async def roles(self, ctx, *, member: MemberRoles):
        await ctx.send('I see the following roles:\n' + '\n'.join(member))


def setup(bot):
    bot.add_cog(ImageTest(bot))
