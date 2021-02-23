from io import BytesIO
from discord import AsyncWebhookAdapter, File, Webhook
from discord.ext import tasks
from utils.Cog import Cog
from utils.Manipulation import Manip


class Events(Cog, command_attrs={'hidden': True}):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()
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
        await self.bot.cache_guilds()
        embed = self.bot.embed(
            title=f'Joined a server: {guild}🎉',
            description=f'Total members: {guild.member_count}'
            f'Now in {len(self.bot.guilds)} guilds!',
            color=0x2ecc71
        ).set_thumbnail(url=guild.icon_url_as(size=256))
        await self.webhook.send(embed=embed)

    @Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.pool.execute('DELETE FROM guild_config WHERE guild_id = $1', guild.id)
        embed = self.bot.embed(
            title=f'Lost a server: {guild}💔',
            description=f'Total members: {guild.member_count}'
            f'Now in {len(self.bot.guilds)} guilds.',
            color=0xff0000
        ).set_thumbnail(url=guild.icon_url_as(size=256))
        await self.webhook.send(embed=embed)

    @Cog.listener()
    async def on_dbl_vote(self, data):
        await self.webhook.send(f'**New upvote** by {data["user"]}!')

    @Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1
        await self.bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    @Cog.listener()
    async def on_member_join(self, member):
        g = member.guild
        if wc := self.bot.cache['welcome_channel'][g.id]:
            await g.get_channel(wc).send(file=File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := self.bot.cache['autorole'][g.id]:
            await member.add_roles(g.get_role(role_id))

    @Cog.listener()
    async def on_guild_unavailable(self, guild):
        await self.bot.get_guild(guild.id).leave()


def setup(bot):
    bot.add_cog(Events(bot))
