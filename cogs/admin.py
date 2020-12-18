import asyncio
import re
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument(f"{k} is an invalid time-key! h/m/s/d are valid.")
            except ValueError:
                raise commands.BadArgument(f"{v} is not a number!")
        return time


class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mute", aliases=["block"], brief="mutes member (admins only). also you can specify the time")
    @commands.has_permissions(administrator=True)
    async def mute_user(self, ctx, member: discord.Member, time: TimeConverter = None):
        """Mutes a member for a given amount of time. Ex: .mute @someone"""
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
    async def unmute_user(self, ctx, member: discord.Member):
        """Unmutes a member (removes Muted role). Ex: .unmute @someone who is already muted"""
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await member.remove_roles(role)
        await ctx.send(f"Unmuted **{member}** successfully.")

    @commands.command(pass_context=True, brief="change someone's nickname")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, new_nick: str):
        """Changes user's nickname."""
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✔')

    @commands.command(brief="kick user")
    @commands.guild_only()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kicks user (reason is optional)."""
        r = reason if reason is not None else 'Reason not specified.'
        await ctx.guild.kick(user=member, reason=r)
        embed = discord.Embed(
            title=f"{ctx.author.display_name} kicked: {member.display_name}",
            description=r,
            color=discord.Color.dark_theme()
        )
        await ctx.send(embed=embed)

    @commands.command(brief="ban user")
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans user (reason is optional)."""
        r = reason if reason is not None else 'Reason not specified.'
        embed = discord.Embed(
            title=f'{ctx.author.display_name} banned: {member.display_name}',
            description=r,
            color=discord.Color.dark_theme()
        )
        await member.ban(reason=r)
        await ctx.send(embed=embed)

    @commands.command(brief="unban user")
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, *, member):
        """Unbans already banned user."""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return

    @commands.command(aliases=['clear'], brief="clear messages")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount=2):
        """Purges messages of given amount (limit is 100 messages)."""
        if amount > 100:
            await ctx.send("That is too big amount. The maximum is 100")
        elif amount <= 100:
            deleted = await ctx.channel.purge(limit=amount)
            purge_embed = discord.Embed(title="Clear Command",
                                        description=f"✅ Purged {len(deleted)} messages by {ctx.author.name}",
                                        colour=discord.Color.red(),
                                        timestamp=datetime.utcnow())
            await ctx.send(embed=purge_embed)

    @commands.command(brief="add a new category to the server")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def categoryadd(self, ctx, role: discord.Role, *, name):
        """Adds a category for guild (you should specify role and category name)."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        category = await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.send(f"Just made a new category named {category.name}!")

    @commands.command(brief="add a new channel to the server")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def channeladd(self, ctx, role: discord.Role, *, name):
        """Adds a channel for guild (you should specify role and channel name)."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await ctx.guild.create_text_channel(name=name, overwrites=overwrites)
        await ctx.send(f"Just made a new channel named {channel.name}!")

    @commands.command(name='delcat', brief="delete the category")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def _category(self, ctx, category: discord.CategoryChannel, *, reason=Optional[str]):
        """Deletes given category (reason is optional)."""
        await category.delete(reason=reason)
        await ctx.send(f"Deleted a channel named {category.name}!")

    @commands.command(name='delchan', brief="delete the channel")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def _channel(self, ctx, channel: Optional[discord.TextChannel], *, reason=None):
        """Deletes given channel (reason is optional)."""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.send(f"Deleted a channel named {channel.name}!")

    @commands.command(aliases=['ld'], brief="channel lockdown")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lockdown(self, ctx, channel: Optional[discord.TextChannel]):
        """Puts channel on lockdown. You can specify the channel, otherwise it puts the channel where the message was given."""
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
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
    async def slowmode(self, ctx, arg):
        """Activates slowmode for a given amount of seconds."""
        if arg == "disable":
            await ctx.channel.edit(slowmode_delay=0)
            await ctx.send("Disabled slowmode successfully")

        elif int(arg):
            await ctx.channel.edit(slowmode_delay=int(arg))
            await ctx.send(f"Slowmode has activated to {arg} seconds")

    @commands.command(aliases=['add_role'], brief="add role to the user")
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """Adds a given role to the user."""
        await user.add_roles(role)
        await ctx.send(f"Successfully given a {role.mention} role to {user.mention}.")

    @commands.command(aliases=['remove_role'], brief="remove role from user")
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        """Removes given role from the user."""
        await user.remove_roles(role)
        await ctx.send(f"Successfully removed a {role.mention} role from {user.mention}.")


def setup(bot):
    bot.add_cog(Administration(bot))
