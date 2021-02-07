from discord import utils
from utils.Cog import Cog


class ReactionRoles(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = {
            'ping': 'Pingable',
            'blobaww': 'Tester'
        }

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 807660589559971940:
            guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

            for emoji_name, role_name in self.reactions.items():
                if payload.emoji.name == emoji_name:
                    role = utils.get(guild.roles, name=role_name)

            if role:
                member = payload.member
                if member:
                    await member.add_roles(role)
                else:
                    print('Member not found.')
            else:
                print('Role not found.')

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == 807660589559971940:
            guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

            for emoji_name, role_name in self.reactions.items():
                if payload.emoji.name == emoji_name:
                    role = utils.get(guild.roles, name=role_name)

            if role:
                member = payload.member
                if member:
                    await member.remove_roles(role)
                else:
                    print('Member not found.')
            else:
                print('Role not found.')


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
