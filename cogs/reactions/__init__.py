from discord import utils
from utils.Cog import Cog


class ReactionRoles(Cog):
    """A reaction-roles cog which is in testing."""
    icon = '🔨'
    name = 'Reaction-Roles'

    def __init__(self, bot):
        self.bot = bot
        self.reactions = {
            'ping': 'Pingable',
            'blobaww': 'Tester'
        }

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 807660589559971940:
            guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

            for emoji_name, role_name in self.reactions.items():
                if payload.emoji.name == emoji_name:
                    role = utils.get(guild.roles, name=role_name)

            await payload.member.add_roles(role)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
