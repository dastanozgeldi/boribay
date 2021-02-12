from io import BytesIO
from discord import File
from utils.Cog import Cog
from utils.Manipulation import Manip


class Events(Cog, command_attrs={'hidden': True}):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1
        await self.bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    @Cog.listener()
    async def on_member_join(self, member):
        g = member.guild
        if wc := self.bot.config['welcome_channel'][g.id]:
            await g.get_channel(wc).send(file=File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := self.bot.config['autorole'][g.id]:
            await member.add_roles(g.get_role(role_id))

    @Cog.listener()
    async def on_guild_unavailable(self, guild):
        await self.bot.get_guild(guild.id).leave()


def setup(bot):
    bot.add_cog(Events(bot))
