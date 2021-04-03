from typing import Optional

import discord
from discord.ext import commands
from boribay.utils import Cog, is_mod


class Moderation(Cog):
    """Commands for moderators. Manage guild permission required."""
    icon = '🛡'
    name = 'Moderation'

    async def cog_check(self, ctx):
        return await is_mod().predicate(ctx)

    @commands.command()
    async def changenick(self, ctx, member: commands.MemberConverter, *, new_nick: str):
        """Changes member's nickname in the server.
        Args: member: a member whose nickname you want to change.
        new_nick (str): a new nickname for the member you specified."""
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def kick(self, ctx, member: commands.MemberConverter, *, reason='Reason not specified.'):
        """Kicks a user.
        Args: member: a member you want to kick.
        reason (str, optional): Reason why you considered kicking. Defaults to None."""
        dest = ctx.bot.guild_cache.get('logging_channel') or ctx
        await ctx.guild.kick(user=member, reason=reason)
        embed = ctx.bot.embed.default(
            ctx, title=f'{member} was kicked.', description=reason
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
    async def addcategory(self, ctx, role: commands.RoleConverter, *, name: str):
        """Adds a category for the current guild.
        Args: role: role that will have access to a category.
        name (str): name of a category."""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['add_channel'])
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def addchannel(self, ctx, role: commands.RoleConverter, *, name: str):
        """Adds a channel for the current guild.
        Args: role: role that will have access to a category.
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
    async def addrole(self, ctx, role: commands.RoleConverter, user: commands.MemberConverter):
        """Adds a specified role to a user.
        Args: role: a role you want to give.
        user: member you want to give a role to."""
        await user.add_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['take_role'])
    async def takerole(self, ctx, role: commands.RoleConverter, user: commands.MemberConverter):
        """Removes a specified role from a user.
        Args: role: role you want to take.
        user: member you want to take a role from."""
        await user.remove_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def warn(self, ctx, member: commands.MemberConverter):
        """A little user-warning system commands parent."""
        await ctx.send_help('warn')

    @warn.command(name='set', aliases=['add'])
    async def _set_warn(self, ctx, member: commands.MemberConverter):
        """1 - regular warning; 2 - exclusive warning; 3 - blacklist.
        After last 3rd warning a user will be blacklisted and
        no longer able to use features of the bot."""
        if warns := ctx.bot.user_cache[member.id]['blacklisted']:
            raise commands.BadArgument(f'**{member}** has already been blacklisted.')

        confirmation = await ctx.confirm('Are you sure? The warning will not be reset.')
        if confirmation:
            events = [
                'This is the 1st warning this user has.',
                f'The 2nd warning has been sent. Be careful, {member}!',
                f'The 3rd and final warning for {member}, putting them into the blacklist...'
            ]

            query = '''
            UPDATE users SET
            warns = warns + 1,
            blacklisted = CASE WHEN warns = 2 THEN true ELSE false END
            WHERE user_id = $1
            '''  # Checking if warns = 2 ↑ since it will equal 3 after execution.

            await ctx.bot.pool.execute(query, member.id)
            await ctx.send(f'✅ A complaint for **{member}** was sent successfully!\n{events[warns - 1]}')
            return await ctx.bot.user_cache.refresh()

        await ctx.send('The `user warning` session was closed.')

    @warn.command(name='remove')
    async def _remove_warn(self, ctx, member: commands.MemberConverter):
        """Removes 1 warning from a user."""
        if (warns := ctx.bot.user_cache[member.id]['warns']) == 0:
            raise commands.BadArgument(f'**{member}** has no warnings to remove.')

        confirmation = await ctx.confirm(f'Are you sure? {member} is going to have {warns - 1} warnings.')
        if confirmation:
            query = 'UPDATE users SET warns = warns - 1 WHERE user_id = $1'
            await ctx.bot.pool.execute(query, member.id)
            await ctx.send(f'✅ 1 warning was successfully removed from **{member}**!')
            return await ctx.bot.user_cache.refresh()

        await ctx.send('The `user unwarning` session was closed.')

    @warn.command(name='reset')
    async def _reset_warn(self, ctx, member: commands.MemberConverter):
        """Resets all warnings from a user."""
        if ctx.bot.user_cache[member.id]['warns'] == 0:
            raise commands.BadArgument(f'**{member}** has no warnings to reset.')

        confirmation = await ctx.confirm(f'Are you sure? All warnings for {member} are going to be reset.')
        if confirmation:
            query = 'UPDATE users SET warns = 0 WHERE user_id = $1'
            await ctx.bot.pool.execute(query, member.id)
            await ctx.send(f'✅ All warnings were successfully reset for **{member}**!')
            return await ctx.bot.user_cache.refresh()

        await ctx.send('The `user warn resetting` session was closed.')


def setup(bot):
    bot.add_cog(Moderation())
