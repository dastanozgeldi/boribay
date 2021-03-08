from typing import Optional

import discord
from discord.ext import commands
from utils import Cog, ColorConverter, is_mod


class Moderation(Cog):
    '''Administration extension. A module that is created to keep
    discipline in the server. Purging messages, muting members, channel create
    command, all of them are here.'''
    icon = '🛡'
    name = 'Moderation'

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    def on_or_off(self, ctx, key, checks):
        for check in checks:
            if ctx.bot.cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'
        return '<:tick:814838692459446293>'

    async def update(self, ctx, key, value):
        query = f'UPDATE guild_config SET {key} = $1 WHERE guild_id = $2'
        ctx.bot.cache[ctx.guild.id][key] = value
        await ctx.bot.pool.execute(query, value, ctx.guild.id)

    @commands.group(invoke_without_command=True, aliases=['gs'])
    async def settings(self, ctx):
        """The settings parent command.
        Shows settings statistic of the current server:
        Custom color and custom prefix."""
        g = ctx.guild
        creds = ctx.bot.cache[g.id]
        embed = ctx.bot.embed.default(ctx)
        embed.add_field(
            name='Guild Settings',
            value='\n'.join(f'**{self.on_or_off(ctx, k, [".", 3553598, None, None])} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        )
        await ctx.send(embed=embed)

    @settings.command(aliases=['wc'])
    @is_mod()
    async def welcomechannel(self, ctx, channel: discord.TextChannel):
        """Set Welcome channel command.
        Args: channel: Channel where the bot should log messages to."""
        await self.update(ctx, 'welcome_channel', channel.id)
        await ctx.send(f'Set {channel.mention} as a welcoming channel.')

    @settings.command()
    @is_mod()
    async def prefix(self, ctx, prefix: str):
        """Set Prefix command
        Args: prefix (str): a new prefix that you want to set."""
        await self.update(ctx, 'prefix', prefix)
        await ctx.send(f'Prefix has been changed to: `{prefix}`')

    @settings.command(aliases=['colour'])
    @is_mod()
    async def color(self, ctx, color: ColorConverter):
        """Sets the custom color for the bot. Then all embeds color will be one
        that you specified. To bring the default color back,
        use `settings color #36393e`"""
        color = int(str(color).replace('#', ''), 16)
        await self.update(ctx, 'embed_color', color)
        msg = 'As of now, the embed color will look like this.'
        await ctx.send(embed=ctx.bot.embed.default(ctx, title=msg))

    @settings.command()
    @is_mod()
    async def autorole(self, ctx, role: discord.Role):
        """Sets the autorole for the current server.
        This will handle all joined users and give them the role
        that you have specified."""
        await self.update(ctx, 'autorole', role.id)
        await ctx.send(f'As of now, a role `{role.name}` will be automatically given when a member joins this server.')

    @commands.group(invoke_without_command=True)
    async def admin(self, ctx):
        """Administrator-only commands."""
        await ctx.send_help('admin')

    @admin.command()
    @commands.has_guild_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Bans a user.
        Args: member (discord.Member): a member you want to ban.
        reason (str, optional): Reason why you are banning. Defaults to None."""
        r = reason or 'Reason not specified.'
        embed = ctx.bot.embed.default(
            ctx, title=f'{ctx.author.display_name} banned → {member.display_name}', description=r)
        await member.ban(reason=r)
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
        Args: channel (Optional[discord.TextChannel]): channel ID,
        deletes current channel if argument is not specified.
        reason (optional): Reason why you are deleting a channel. Defaults to None."""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def mod(self, ctx):
        """Commands that moderators can execute."""
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
            ctx, title=f"{ctx.author.display_name} kicked: {member.display_name}", description=r)
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
