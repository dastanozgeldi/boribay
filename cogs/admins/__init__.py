import discord
import asyncio
from typing import Optional
from utils.Cog import Cog
from discord.ext import commands
from utils.Converters import TimeConverter
from utils.Checks import is_mod


class Management(Cog):
    '''Administration extension. A module that is created to keep
    discipline in the server. Purging messages, muting members, channel create
    command, all of them are here.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '🛡 Management'

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def addlog(self, ctx, message: str, channel: Optional[discord.TextChannel]):
        """Adds log channel with log message to the DB. When someone joins to
        your guild, that channel will be notified."""
        channel = channel or ctx.channel
        await self.bot.pool.execute('UPDATE guild_config SET member_log = $1, member_log_message = $2 WHERE guild_id = $3', channel.id, message, ctx.guild.id)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['block'])
    @is_mod()
    async def mute(self, ctx, member: discord.Member, time: Optional[TimeConverter]):
        """Mutes a member for time you specify (role 'Muted' required).
        Example: **mute Dosek 1d2h3m4s**
        Args: member (discord.Member): a member you want to mute.
        time (int, optional): time a user going to be muted. Defaults to None."""
        role = discord.utils.get(ctx.guild.roles, name='Muted')
        await member.add_roles(role)
        await ctx.send(f'Muted **{member}** for **{time}s**' if time else f'Muted **{member}**')
        if time:
            if not role:
                return
            await asyncio.sleep(time)
            await ctx.send(f'Time\'s up! Unmuting {member}...')
            await member.remove_roles(role)

    @commands.command(aliases=['unblock'])
    @is_mod()
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a user (role 'Muted' required).
        Args: member (discord.Member): already muted user."""
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @is_mod()
    async def nick(self, ctx, member: discord.Member, *, new_nick: str):
        """Changes member's nickname in the server.
        Args: member (discord.Member): a member whose nickname you wanna change.
        new_nick (str): a new nickname for the member you specified."""
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @is_mod()
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Kicks a user.
        Args: member (discord.Member): a member you want to kick.
        reason (str, optional): Reason why you considered kicking. Defaults to None."""
        r = reason or 'Reason not specified.'
        await ctx.guild.kick(user=member, reason=r)
        embed = self.bot.embed.default(ctx, title=f"{ctx.author.display_name} kicked: {member.display_name}", description=r)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Bans a user.
        Args: member (discord.Member): a member you want to ban.
        reason (str, optional): Reason why you are banning. Defaults to None."""
        r = reason or 'Reason not specified.'
        embed = self.bot.embed.default(ctx, title=f'{ctx.author.display_name} banned: {member.display_name}', description=r)
        await member.ban(reason=r)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def unban(self, ctx, user: discord.User):
        """Unban user with their ID
        Args: user (discord.User): Normally takes user ID.
        Returns: Exception: If given user id isn't in server ban-list."""
        await ctx.guild.unban(user)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['clear'])
    @is_mod()
    async def purge(self, ctx, amount: int = 2):
        """Purges messages of a given amount. Limit is 100.
        Args: amount (int, optional): amount of messages to clear. Defaults to 2"""
        if amount > 100:
            return await ctx.send('That is too big amount. The maximum is 100')
        await ctx.channel.purge(limit=amount)

    @commands.command()
    @is_mod()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def categoryadd(self, ctx, role: discord.Role, *, name: str):
        """Adds a category for the current guild.
        Args: role (discord.Role): role that will have access to a category.
        name (str): name of a category."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @is_mod()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def channeladd(self, ctx, role: discord.Role, *, name: str):
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

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def delcat(self, ctx, category: discord.CategoryChannel, *, reason: Optional[str]):
        """Deletes a specififed category.
        Args: category (discord.CategoryChannel): ID of a category.
        reason (str, optional): Reason why you are deleting a category. Defaults to None."""
        await category.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def delchan(self, ctx, channel: discord.TextChannel, *, reason: Optional[str]):
        """Deletes a specified channel.
        Args: channel (Optional[discord.TextChannel]): channel ID,
        deletes current channel if argument is not specified.
        reason (optional): Reason why you are deleting a channel. Defaults to None."""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['ld'])
    @is_mod()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lockdown(self, ctx, channel: Optional[discord.TextChannel]):
        """Puts a channel on lockdown.
        Args: channel (Optional[discord.TextChannel]): channel mention,
        puts the current channel on lockdown if argument is not specified."""
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
            await channel.edit(overwrites=overwrites)

        elif channel.overwrites[ctx.guild.default_role].send_messages is True or channel.overwrites[ctx.guild.default_role].send_messages is None:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

        else:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['sm'])
    @is_mod()
    async def slowmode(self, ctx, arg):
        """Enables slowmode for a given amount of seconds.
        Args: arg (int): a time in seconds users have to wait to send a message."""
        await ctx.channel.edit(slowmode_delay=arg)
        await ctx.send(f'Slowmode has set to {arg} seconds.')

    @commands.command(aliases=['add_role'])
    @is_mod()
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """Adds a specified role to a user.
        Args: role (discord.Role): a role you want to give.
        user (discord.Member): member you want to give a role to."""
        await user.add_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['remove_role'])
    @is_mod()
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        """Removes a specified role from a user.
        Args: role (discord.Role): role you want to take.
        user (discord.Member): member you want to take a role from."""
        await user.remove_roles(role)
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Management(bot))
