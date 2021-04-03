from boribay.core import Boribay
from boribay.utils import Cog
from discord.ext.ipc import server


class IpcRoutes(Cog):
    def __init__(self, bot: Boribay):
        self.bot = bot

    @server.route()
    async def get_general_stats(self, data):
        return {
            'support': self.bot.config.links.support_url,
            'invite': self.bot.config.links.invite_url,
            'guild_count': len(self.bot.guilds),
            'command_count': len(self.bot.commands),
            'command_usage': self.bot.cache.get('command_usage', 0)
        }

    @server.route()
    async def get_command_list(self, data):
        return {str(x): x.help.split('\n')[0] for x in self.bot.commands}


def setup(bot):
    bot.add_cog(IpcRoutes(bot))
