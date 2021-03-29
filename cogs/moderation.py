from typing import Optional

import discord
from discord.ext import commands
from utils import Cog, is_mod


class Moderation(Cog):
    """Commands for moderators. Manage guild permission required."""
    icon = '🛡'
    name = 'Moderation'

    async def cog_check(self, ctx):
        return await is_mod().predicate(ctx)

    @commands.command()
    async def changenick(self, ctx, member: discord.Member, *, new_nick: str):
        """Changes member's nickname in the server.
        Args: member: a member whose nickname you want to change.
        new_nick (str): a new nickname for the member you specified."""
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str]):
        """Kicks a user.
        Args: member (discord.Member): a member you want to kick.
        reason (str, optional): Reason why you considered kicking. Defaults to None."""
        dest = ctx.bot.guild_cache.get('logging_channel') or ctx
        reason = reason or 'Reason not specified.'

        await ctx.guild.kick(user=member, reason=reason)
        embed = ctx.bot.embed.default(
            ctx,
            title=f'{member} was kicked.',
            description=reason
        )

        await dest.send(embed=embed)

    @commands.command(aliases=['clear'])
    async def purge(self, ctx, limit: Optional[int] = 2):
        """Purges messages of a given amount. Limit is 100.
        Args: amount (Optional): amount of messages to clear. Defaults to 2."""
        if limit > 100:
            raise commands.BadArgument('That is too big amount. The maximum is 100')

        await ctx.channel.purge(limit=limit)

    @commands.command(aliases=['add_category'])
    @commands.bot_has_guild_permissions(manage_channels=True)
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

    @commands.command(aliases=['add_channel'])
    @commands.bot_has_guild_permissions(manage_channels=True)
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

    @commands.command(aliases=['sm'])
    async def slowmode(self, ctx, arg):
        """Enables slowmode for a given amount of seconds.
        Args: arg (int): a time in seconds users have to wait to send a message."""
        await ctx.channel.edit(slowmode_delay=arg)
        await ctx.send(f'Slowmode has set to {arg} seconds.')

    @commands.command(aliases=['add_role'])
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """Adds a specified role to a user.
        Args: role (discord.Role): a role you want to give.
        user (discord.Member): member you want to give a role to."""
        await user.add_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['take_role'])
    async def takerole(self, ctx, role: discord.Role, user: discord.Member):
        """Removes a specified role from a user.
        Args: role (discord.Role): role you want to take.
        user (discord.Member): member you want to take a role from."""
        await user.remove_roles(role)
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Moderation())
