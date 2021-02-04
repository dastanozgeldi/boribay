import discord
from utils.Cog import Cog
from utils.Manipulation import welcome_card


class Events(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1
        await self.bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if (wc := await self.bot.pool.fetchval('SELECT welcome_channel FROM guild_config WHERE guild_id = $1', member.guild.id)):
            await member.guild.get_channel(wc).send(file=await welcome_card(member))

    @Cog.listener()
    async def on_guild_unavailable(self, guild: discord.Guild):
        await self.bot.get_guild(guild.id).leave()


def setup(bot):
    bot.add_cog(Events(bot))
