import copy
from typing import Optional, Union

import discord
from discord.ext import commands
from utils import Cog, ColorConverter, is_mod


class Moderation(Cog):
    """Administration extension. A module that is created to keep
    discipline in the server. Purging messages, muting members, channel create
    command, all of them are here."""
    icon = '🛡'
    name = 'Moderation'

    def on_or_off(self, ctx, key):
        checks = ['.', None, 0x36393f, None, None]

        for check in checks:
            if ctx.bot.cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

    async def update(self, ctx, key, value):
        me = ctx.bot
        guild = ctx.guild.id
        query = f'UPDATE guild_config SET {key} = $1 WHERE guild_id = $2'

        await me.pool.execute(query, value, guild)
        me.cache[guild][key] = value

    def humanize(self, guild: discord.Guild, config):
        data = copy.copy(config[guild.id])

        for k, v in data.items():
            if k == 'autorole':
                data[k] = guild.get_role(v)

            elif k == 'embed_color':
                data[k] = hex(v)

            elif k in ('welcome_channel', 'automeme'):
                data[k] = guild.get_channel(v)

        return data

    @commands.group(invoke_without_command=True, aliases=['gs'])
    async def settings(self, ctx):
        """The settings parent command.
        Shows the settings of the current server."""
        g = ctx.guild

        creds = self.humanize(g, ctx.bot.cache)
        embed = ctx.bot.embed.default(
            ctx, description='\n'.join(f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        ).set_author(name=f'Settings of {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @settings.command(aliases=['wc'])
    @is_mod()
    async def welcomechannel(self, ctx, channel: Union[discord.TextChannel, str.lower]):
        """Set the welcome channel command.
        To disable this feature just put `disable` after the command."""
        if isinstance(channel, str) and channel == 'disable':
            await self.update(ctx, 'welcome_channel', None)
            return await ctx.send('✅ Disabled welcome-channel.')

        await self.update(ctx, 'welcome_channel', channel.id)
        await ctx.send(f'✅ Set {channel} as a welcoming channel.')

    @settings.command()
    @is_mod()
    async def prefix(self, ctx, new: str):
        """Set Prefix command.
        Args: prefix (str): a new prefix that you want to set."""
        await self.update(ctx, 'prefix', new)
        await ctx.send(f'Prefix has been changed to: `{new}`')

    @settings.command(aliases=['colour'])
    @is_mod()
    async def color(self, ctx, color: ColorConverter):
        """Sets the custom color for the bot. Then all embeds color will be one
        that you specified. To bring the default color back,
        use `settings color #36393e`"""
        color = int(str(color).replace('#', ''), 16)
        await self.update(ctx, 'embed_color', color)

        embed = ctx.bot.embed.default(ctx, title='As of now, the embed color will look like this.')
        await ctx.send(embed=embed)

    @settings.command()
    @is_mod()
    async def autorole(self, ctx, role: Union[discord.Role, str.lower]):
        """Sets the autorole for the current server.
        To disable this feature just put `disable` after the command."""
        if isinstance(role, str) and role == 'disable':
            await self.update(ctx, 'autorole', None)
            return await ctx.send('✅ Disabled autorole.')

        await self.update(ctx, 'autorole', role.id)
        await ctx.send(f'✅ Set `{role}` as an autorole.')

    @settings.command()
    @is_mod()
    async def automeme(self, ctx, channel: Union[discord.TextChannel, str.lower]):
        """Sets the automeme stuff for the current server."""
        if isinstance(channel, str) and channel == 'disable':
            await self.update(ctx, 'automeme', None)
            return await ctx.send('✅ Disabled automemes.')

        await self.update(ctx, 'automeme', channel.id)
        await ctx.send(f'✅ Set {channel} as automemes channel.')

    @commands.group(invoke_without_command=True)
    async def admin(self, ctx):
        """Administrator-only commands, you must have the administrator permission."""
        await ctx.send_help('admin')

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def addbalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Increase someone's balance for being well behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('Balance adding limit has reached. Specify between 10 and 100 000')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank + $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully added **{amount} batyrs** to **{member}**!')
        await ctx.bot.user_cache.refresh()

    @admin.command()
    @commands.has_permissions(administrator=True)
    async def removebalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Decrease someone's balance for being bad behaved."""
        member = member or ctx.author
        query = 'UPDATE users SET bank = bank - $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully removed **{amount} batyrs** from **{member}**!')
        await ctx.bot.user_cache.refresh()

    @admin.command()
    @commands.has_guild_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Bans a user.
        Args: member (discord.Member): a member you want to ban.
        reason (str, optional): Reason why you are banning. Defaults to None."""
        r = reason or 'Reason not specified.'
        await member.ban(reason=r)
        embed = ctx.bot.embed.default(
            ctx,
            title=f'{member} was banned.',
            description=r
        )

        await ctx.send(embed=embed)

    @admin.command()
    @commands.has_guild_permissions(administrator=True)
    async def unban(self, ctx, user: discord.User):
        """Unban user with their ID
        Args: user (discord.User): Normally takes user ID.
        Returns: Exception: If given user id isn't in server ban-list."""
        await ctx.guild.unban(user)
        await ctx.message.add_reaction('✅')

    @admin.command(aliases=['removecategory'])
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def deletecategory(self, ctx, category: discord.CategoryChannel, *, reason: Optional[str]):
        """Deletes a specififed category.
        Args: category (discord.CategoryChannel): ID of a category.
        reason (str, optional): Reason why you are deleting a category. Defaults to None."""
        await category.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @admin.command(aliases=['removechannel'])
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def deletechannel(self, ctx, channel: discord.TextChannel, *, reason: Optional[str]):
        """Deletes a specified channel.
        Args: channel (Optional[discord.TextChannel]): A channel you want to delete,
        deletes current channel if argument was not specified.
        reason (optional): Reason why you are deleting a channel."""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def mod(self, ctx):
        """Commands for moderators. Manage guild permission required."""
        await ctx.send_help('mod')

    @mod.command()
    @is_mod()
    async def changenick(self, ctx, member: discord.Member, *, new_nick: str):
        """Changes member's nickname in the server.
        Args: member: a member whose nickname you want to change.
        new_nick (str): a new nickname for the member you specified."""
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @mod.command()
    @is_mod()
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Kicks a user.
        Args: member (discord.Member): a member you want to kick.
        reason (str, optional): Reason why you considered kicking. Defaults to None."""
        r = reason or 'Reason not specified.'
        await ctx.guild.kick(user=member, reason=r)
        embed = ctx.bot.embed.default(
            ctx,
            title=f'{member} was kicked.',
            description=r
        )

        await ctx.send(embed=embed)

    @mod.command(aliases=['clear'])
    @is_mod()
    async def purge(self, ctx, amount: Optional[int] = 2):
        """Purges messages of a given amount. Limit is 100.
        Args: amount (Optional): amount of messages to clear. Defaults to 2."""
        if amount > 100:
            raise commands.BadArgument('That is too big amount. The maximum is 100')

        await ctx.channel.purge(limit=amount)

    @mod.command(aliases=['add_category'])
    @commands.bot_has_guild_permissions(manage_channels=True)
    @is_mod()
    async def addcategory(self, ctx, role: discord.Role, *, name: str):
        """Adds a category for the current guild.
        Args: role (discord.Role): role that will have access to a category.
        name (str): name of a category."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @mod.command(aliases=['add_channel'])
    @commands.bot_has_guild_permissions(manage_channels=True)
    @is_mod()
    async def addchannel(self, ctx, role: discord.Role, *, name: str):
        """Adds a channel for the current guild.
        Args: role (discord.Role): role that will have access to a category.
        name (str): name of a channel."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_text_channel(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @mod.command(aliases=['sm'])
    @is_mod()
    async def slowmode(self, ctx, arg):
        """Enables slowmode for a given amount of seconds.
        Args: arg (int): a time in seconds users have to wait to send a message."""
        await ctx.channel.edit(slowmode_delay=arg)
        await ctx.send(f'Slowmode has set to {arg} seconds.')

    @mod.command(aliases=['add_role'])
    @is_mod()
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """Adds a specified role to a user.
        Args: role (discord.Role): a role you want to give.
        user (discord.Member): member you want to give a role to."""
        await user.add_roles(role)
        await ctx.message.add_reaction('✅')

    @mod.command(aliases=['take_role'])
    @is_mod()
    async def takerole(self, ctx, role: discord.Role, user: discord.Member):
        """Removes a specified role from a user.
        Args: role (discord.Role): role you want to take.
        user (discord.Member): member you want to take a role from."""
        await user.remove_roles(role)
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Moderation())
