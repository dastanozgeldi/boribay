import json
from io import BytesIO

import discord
from boribay.core import PATH, Boribay, Cog, Context, create_logger
from boribay.utils import Manip
from discord.ext import tasks


class Events(Cog):
    """The Global events cog that handles every specified event below."""

    def __init__(self, bot: Boribay):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

        with open(f'{PATH}/main/rr.json', 'r') as f:
            self.local_reaction_roles = json.load(f)

        if not self.bot.config.main.beta:
            self.update_stats.start()

    # Tasks.
    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        try:
            await self.bot.dblpy.post_guild_count()
            self.logger.info('Updating TopGG data...')

        except Exception as e:
            self.logger.warning(f'Failed to post the server count\n{type(e).__name__}: {e}')

    # Bot-related events.
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

    # Guild logging.
    async def _log_guild(self, guild: discord.Guild, **kwargs):
        """A general guild-logging method since both events are pretty similar.

        Args:
            guild (discord.Guild): The guild object produced by the event.
        """
        embed = self.bot.embed(
            title=kwargs.pop('text').format(guild),
            description=f'Member count: {guild.member_count}'
            f'Guild ID: {guild.id}\nNow in {len(self.bot.guilds)} guilds.',
            color=kwargs.pop('color')
        ).set_thumbnail(url=guild.icon_url)

        await self.bot.webhook.send(embed=embed)
        await self.bot.pool.execute(kwargs.pop('query'), guild.id)
        await self.bot.guild_cache.refresh()

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self._log_guild(guild, text='Joined a server: {}🎉', color=0x2ecc71,
                              query='INSERT INTO guild_config(guild_id) VALUES($1);')

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self._log_guild(guild, text='Lost a server: {}💔', color=0xff0000,
                              query='DELETE FROM guild_config WHERE guild_id = $1;')

    @Cog.listener()
    async def on_command_completion(self, ctx: Context):
        me = self.bot
        author = ctx.author.id
        me.command_usage += 1
        await me.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

        if not await me.pool.fetch('SELECT * FROM users WHERE user_id = $1', author):
            query = 'INSERT INTO users(user_id) VALUES($1)'
            await me.pool.execute(query, author)
            await me.user_cache.refresh()

    # Member-logging.
    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g = member.guild

        if wc := self.bot.guild_cache[g.id].get('welcome_channel', False):
            await g.get_channel(wc).send(file=discord.File(fp=await Manip.welcome(
                BytesIO(await member.avatar_url.read()),
                f'Member #{g.member_count}',
                f'{member} just spawned in the server.',
            ), filename=f'{member}.png'))

        if role_id := self.bot.guild_cache[g.id].get('autorole', False):
            await member.add_roles(g.get_role(role_id), reason='Autorole')

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if (m_id := str(payload.message_id)) in self.local_reaction_roles.keys():
            guild = discord.utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)
            for emoji, name in self.local_reaction_roles[m_id].items():
                if payload.emoji.name == emoji:
                    role = discord.utils.get(guild.roles, name=name)

            await payload.member.add_roles(role)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if (m_id := str(payload.message_id)) in self.local_reaction_roles.keys():
            guild = discord.utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)
            for emoji, name in self.local_reaction_roles[m_id].items():
                if payload.emoji.name == emoji:
                    role = discord.utils.get(guild.roles, name=name)

            member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
            await member.remove_roles(role)

    # Next the stuff related to the guild logging.
    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if not (channel_id := self.bot.guild_cache[guild.id].get('logging_channel')):
            return

        data = (await (guild.audit_logs(action=discord.AuditLogAction.ban)).flatten())[0]
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
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if not (channel_id := self.bot.guild_cache[guild.id].get('logging_channel')):
            return

        data = (await (guild.audit_logs(action=discord.AuditLogAction.unban)).flatten())[0]
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
