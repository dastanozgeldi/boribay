from io import BytesIO

from discord import AsyncWebhookAdapter, File, Webhook, utils
from discord.ext import tasks
from utils import Cog, Manip


class Events(Cog, command_attrs={'hidden': True}):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
        self.reactions = {
            'ping': 'Pingable',
            'blobaww': 'Tester'
        }
        self.webhook = Webhook.from_url(
            self.bot.config['links']['log_url'],
            adapter=AsyncWebhookAdapter(self.bot.session)
        )

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        try:
            await self.bot.dblpy.post_guild_count()

        except Exception as e:
            self.bot.log.warning(f'Failed to post server count\n{type(e).__name__}: {e}')

    @Cog.listener()
    async def on_guild_join(self, guild):
        embed = self.bot.embed(
            title=f'Joined a server: {guild}🎉',
            description=f'Total members: {guild.member_count}\n'
            f'Guild ID: {guild.id}\nNow in {len(self.bot.guilds)} guilds!',
            color=0x2ecc71
        ).set_thumbnail(url=guild.icon_url)

        await self.webhook.send(embed=embed)
        await self.bot.pool.execute('INSERT INTO guild_config(guild_id) VALUES ($1)', guild.id)
        await self.bot.cache.refresh()

    @Cog.listener()
    async def on_guild_remove(self, guild):
        embed = self.bot.embed(
            title=f'Lost a server: {guild}💔',
            description=f'Total members: {guild.member_count}\n'
            f'Guild ID: {guild.id}\nNow in {len(self.bot.guilds)} guilds.',
            color=0xff0000
        ).set_thumbnail(url=guild.icon_url)

        await self.webhook.send(embed=embed)
        await self.bot.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild.id)
        await self.bot.cache.refresh()

    @Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1
        await self.bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    @Cog.listener()
    async def on_member_join(self, member):
        g = member.guild

        if wc := self.bot.cache[g.id].get('welcome_channel', False):
            await g.get_channel(wc).send(file=File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := self.bot.cache[g.id].get('autorole', False):
            await member.add_roles(g.get_role(role_id))

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 807660589559971940:
            guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

            for emoji_name, role_name in self.reactions.items():
                if payload.emoji.name == emoji_name:
                    role = utils.get(guild.roles, name=role_name)

            await payload.member.add_roles(role)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == 807660589559971940:
            guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

            for emoji_name, role_name in self.reactions.items():
                if payload.emoji.name == emoji_name:
                    role = utils.get(guild.roles, name=role_name)

            member = utils.find(lambda m: m.id == payload.user_id, guild.members)
            await member.remove_roles(role)


def setup(bot):
    bot.add_cog(Events(bot))
