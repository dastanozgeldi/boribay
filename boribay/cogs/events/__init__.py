from io import BytesIO

from boribay.core import Boribay, Cog, create_logger
from boribay.utils import Manip
from discord import AsyncWebhookAdapter, AuditLogAction, File, Webhook, utils
from discord.ext import tasks


class Events(Cog):
    """The Global events cog that handles every specified event below."""

    def __init__(self, bot: Boribay):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)
        self.reactions = {'ping': 'Pingable', 'blobaww': 'Tester'}
        self.webhook = Webhook.from_url(
            self.bot.config.links.log_url,
            adapter=AsyncWebhookAdapter(self.bot.session)
        )

        if not self.bot.config.main.beta:
            self.update_stats.start()

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        try:
            await self.bot.dblpy.post_guild_count()
            self.logger.info('Updating TopGG data...')

        except Exception as e:
            self.logger.warning(f'Failed to post server count\n{type(e).__name__}: {e}')

    @Cog.listener()
    async def on_ready(self):
        self.logger.info(f'Logged in as -> {self.bot.user}')
        self.logger.info(f'Guild Count -> {len(self.bot.guilds)}')

    @Cog.listener()
    async def on_message_edit(self, before, after):
        # making able to process commands on message edit only for owner.
        if before.content != after.content:
            if after.author.id in self.bot.owner_ids:
                return await self.bot.process_commands(after)

        # on_message_edit gets tracked twice when a message gets edited, god knows why.
        if before.embeds:
            return

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
        await self.bot.guild_cache.refresh()

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
        await self.bot.guild_cache.refresh()

    @Cog.listener()
    async def on_command_completion(self, ctx):
        me = self.bot
        author = ctx.author.id
        me.command_usage += 1
        await me.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

        if not await me.pool.fetch('SELECT * FROM users WHERE user_id = $1', author):
            query = 'INSERT INTO users(user_id) VALUES($1)'
            await me.pool.execute(query, author)
            await me.user_cache.refresh()

    @Cog.listener()
    async def on_member_join(self, member):
        g = member.guild

        if wc := self.bot.guild_cache[g.id].get('welcome_channel', False):
            await g.get_channel(wc).send(file=File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := self.bot.guild_cache[g.id].get('autorole', False):
            await member.add_roles(g.get_role(role_id), reason='Autorole')

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

    # Next the stuff related to the guild logging.
    @Cog.listener()
    async def on_member_ban(self, guild, user):
        if not (channel_id := self.bot.guild_cache[guild.id].get('logging_channel')):
            return

        data = (await (guild.audit_logs(action=AuditLogAction.ban)).flatten())[0]
        fields = [
            ('User', f'{user.mention} | {user}'),
            ('Reason', data.reason or 'None provided.'),
            ('Moderator', data.user.mention)
        ]

        embed = self.bot.embed(
            title='Member Ban',
            description='\n'.join(f'**{n}:** {v}' for n, v in fields)
        )
        await guild.get_channel(channel_id).send(embed=embed)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        if not (channel_id := self.bot.guild_cache[guild.id].get('logging_channel')):
            return

        data = (await (guild.audit_logs(action=AuditLogAction.unban)).flatten())[0]
        fields = [
            ('User', f'{user.mention} | {user}'),
            ('Reason', data.reason or 'None provided.'),
            ('Moderator', data.user.mention)
        ]

        embed = self.bot.embed(
            title='Member Unban',
            description='\n'.join(f'**{n}:** {v}' for n, v in fields)
        )
        await guild.get_channel(channel_id).send(embed=embed)


def setup(bot: Boribay):
    bot.add_cog(Events(bot))
