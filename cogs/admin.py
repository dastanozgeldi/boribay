import asyncio
from typing import Optional

import discord
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed
from utils.Converters import TimeConverter
from discord.ext import commands


class Administration(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '⚒ Administration'

    async def cog_check(self, ctx):
        return commands.guild_only()
        return commands.bot_has_permissions(administrator=True)
        return ctx.author.has_permissions(administrator=True)

    @commands.command(name='setprefix', brief='Change prefix.')
    @commands.has_permissions(administrator=True)
    async def change_prefix(self, ctx, prefix):
        """Set Prefix command
        Args: prefix (str): a new prefix that you want to set."""
        await self.bot.prefixes.update_one(
            {'_id': ctx.guild.id},
            {"$set": {"prefix": prefix}}
        )
        await ctx.send(f"Prefix has been changed to: {prefix}")

    @commands.command(name="mute", aliases=["block"], brief="mutes member (admins only). also you can specify the time")
    @commands.has_permissions(administrator=True)
    async def mute_user(self, ctx, member: discord.Member, time: TimeConverter = None):
        """Mutes a member for time you specify (role 'Muted' required).
        Example: **mute Dosek 1d2h3m4s**
        Args:
            member (discord.Member): a member you want to mute.
            time (int, optional): time a user going to be muted. Defaults to None."""
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.add_roles(role)
        await ctx.send(f"Muted **{member}** for **{time}s**" if time else f"Muted **{member}**")
        if time:
            if not role:
                return
            await asyncio.sleep(time)
            await ctx.send(f"Time's up! Unmuting {member}...")
            await member.remove_roles(role)

    @commands.command(name="unmute", aliases=["unblock"], brief="unmutes member (admins only)")
    @commands.has_permissions(administrator=True)
    async def unmute_user(self, ctx, member: discord.Member):
        """Unmutes a user (role 'Muted' required).
        Args: member (discord.Member): already muted user.
        """
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(role)
        await ctx.send(f"Unmuted **{member}** successfully.")

    @commands.command(pass_context=True, brief="change someone's nickname")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, new_nick: str):
        """Changes member's nickname in the server.
        Args:
            member (discord.Member): a member whose nickname you wanna change.
            new_nick (str): a new nickname for the member you specified.
        """
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✔')

    @commands.command(brief="kick user")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kicks a user.
        Args:
            member (discord.Member): a member you want to kick.
            reason (str, optional): Reason why you considered kicking. Defaults to None.
        """
        r = reason or 'Reason not specified.'
        await ctx.guild.kick(user=member, reason=r)
        embed = Embed(title=f"{ctx.author.display_name} kicked: {member.display_name}", description=r)
        await ctx.send(embed=embed)

    @commands.command(brief="ban user")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans a user.
        Args:
            member (discord.Member): a member you want to ban.
            reason (str, optional): Reason why you are banning. Defaults to None.
        """
        r = reason or 'Reason not specified.'
        embed = Embed(title=f'{ctx.author.display_name} banned: {member.display_name}', description=r)
        await member.ban(reason=r)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
        """Unban user with their ID
        Args: user (discord.User): Normally takes user ID.
        Returns: Exception: If given user id isn't in server ban-list.
        """
        bans = await ctx.guild.bans()
        if user not in bans:
            return await ctx.send(f'There is not user `{user}` in ban-list.')
        await ctx.guild.unban(user)
        await ctx.send(f'Unbanned {user.mention}')

    @commands.command(aliases=['clear'], brief="clear messages")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount=2):
        """Purges messages of a given amount. Limit is 100.
        Args: amount (int, optional): amount of messages to clear. Defaults to 2
        """
        if amount > 100:
            await ctx.send("That is too big amount. The maximum is 100")

        elif amount <= 100:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(embed=Embed(title="Clear Command", description=f"✅ Purged {len(deleted)} messages by {ctx.author}"))

    @commands.command(brief="add a new category to the server")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def categoryadd(self, ctx, role: discord.Role, *, name: str):
        """Adds a category for the current guild.
        Args:
            role (discord.Role): role that will have access to a category.
            name (str): name of a category.
        """
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        category = await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.send(f"Just made a new category named {category.name}!")

    @commands.command(brief="add a new channel to the server")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def channeladd(self, ctx, role: discord.Role, *, name: str):
        """Adds a channel for the current guild.
        Args:
            role (discord.Role): role that will have access to a category.
            name (str): name of a channel.
        """
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await ctx.guild.create_text_channel(name=name, overwrites=overwrites)
        await ctx.send(f"Just made a new channel named {channel.name}!")

    @commands.command(name='delcat', brief="delete the category")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def _category(self, ctx, category: discord.CategoryChannel, *, reason: str = None):
        """Deletes a specififed category.
        Args:
            category (discord.CategoryChannel): ID of a category.
            reason (str, optional): Reason why you are deleting a category. Defaults to None.
        """
        await category.delete(reason=reason)
        await ctx.send(f"Deleted a channel named {category.name}!")

    @commands.command(name='delchan', brief="delete the channel")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def _channel(self, ctx, channel: Optional[discord.TextChannel], *, reason: str = None):
        """Deletes a specified channel.
        Args:
            channel (Optional[discord.TextChannel]): channel ID,
            deletes current channel if argument is not specified.
            reason (str, optional): Reason why you are deleting a channel. Defaults to None.
        """
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.send(f"Deleted a channel named {channel.name}!")

    @commands.command(aliases=['ld'], brief="channel lockdown")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lockdown(self, ctx, channel: Optional[discord.TextChannel]):
        """Puts a channel on lockdown.
        Args:
            channel (Optional[discord.TextChannel]): channel mention,
            puts the current channel on lockdown if argument is not specified.
        """
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
            await channel.edit(overwrites=overwrites)
            await ctx.send(f"Put `{channel.name}` on lockdown.")

        elif channel.overwrites[ctx.guild.default_role].send_messages is True or channel.overwrites[ctx.guild.default_role].send_messages is None:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await ctx.send(f"Put `{channel.name}` on lockdown.")

        else:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            await ctx.send(f"Removed `{channel.name}` from lockdown.")

    @commands.command(aliases=['sm'], brief="slowmode for a given time")
    @commands.has_permissions(manage_guild=True)
    async def slowmode(self, ctx, arg: int):
        """Enables slowmode for a given amount of seconds.
        Args: arg (int): a time in seconds users have to wait to send a message."""
        if arg == "disable":
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.message.add_reaction('✔')
        else:
            await ctx.channel.edit(slowmode_delay=arg)
            await ctx.send(f"Slowmode has set to {arg} seconds.")

    @commands.command(aliases=['add_role'], brief="add role to the user")
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """Adds a specified role to a user.
        Args:
            role (discord.Role): a role you want to give.
            user (discord.Member): member you want to give a role to."""
        await user.add_roles(role)
        await ctx.message.add_reaction('✔')

    @commands.command(aliases=['remove_role'], brief="remove role from user")
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        """Removes a specified role from a user.
        Args:
            role (discord.Role): role you want to take.
            user (discord.Member): memebr you want to take a role from."""
        await user.remove_roles(role)
        await ctx.message.add_reaction('✔')


def setup(bot):
    bot.add_cog(Administration(bot))
