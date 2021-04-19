from typing import Optional

import discord
from boribay.core import Boribay, Context
from boribay.utils import Cog, is_mod
from discord.ext import commands
from humanize import naturaldate


class Moderation(Cog):
    """Commands for moderators. Manage guild permission required."""
    icon = '🛡'
    name = 'Moderation'

    def __init__(self, bot: Boribay):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        return await is_mod().predicate(ctx)

    @commands.command()
    async def changenick(self, ctx: Context, member: discord.Member, *, new_nick: str):
        """Changes the member's nickname in the current server.

        Args:
            member (discord.Member): A member whose nickname you want to change.
            new_nick (str): A new nickname for the member.
        """
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def kick(self, ctx: Context, member: discord.Member, *, reason='Reason not specified.'):
        """Kicks the member.

        Args:
            member (discord.Member): A member you want to kick.
            reason (str, optional): The reason of kicking. Defaults to 'Reason not specified.'.
        """
        dest = ctx.bot.guild_cache.get('logging_channel') or ctx
        await ctx.guild.kick(user=member, reason=reason)

        embed = ctx.bot.embed.default(
            ctx, title=f'{member} was kicked.', description=reason
        )

        await dest.send(embed=embed)

    @commands.command()
    async def ban(self, ctx: Context, member: discord.Member, *, reason: str = 'Reason not specified.'):
        """Ban the member.

        Args:
            member (discord.Member): A member you want to ban.
            reason (str, optional): The reason of banning. Defaults to 'Reason not specified.'.
        """
        await member.ban(reason=reason)
        await ctx.message.add_reaction('✅')
        # from command, an on_member_ban event will be triggered.

    @commands.command()
    async def unban(self, ctx: Context, member: discord.Member, *, reason: str = 'Reason not specified.'):
        """Unban the user - remove them from the guild blacklist.

        Args:
            member (discord.Member): A member you want to unban.
            reason (str, optional): The reason of unbanning. Defaults to 'Reason not specified.'.
        """
        await member.unban(reason=reason)
        await ctx.message.add_reaction('✅')
        # from command, an on_member_ban event will be triggered.

    @commands.command(aliases=['clear'])
    async def purge(self, ctx: Context, limit: int = 2):
        """Purges the given amount of messages.

        Keep in mind that the limit is 100 messages.

        Args:
            limit (int, optional): Amount of messages to purge. Defaults to 2.

        Raises:
            commands.BadArgument: If the message-limit has reached (100).
        """
        if limit > 100:
            raise commands.BadArgument('That is too big amount. The maximum is 100')

        await ctx.channel.purge(limit=limit)

    @commands.group(invoke_without_command=True)
    async def category(self, ctx: Context):
        """The category-managing commands parent."""
        await ctx.send_help('category')

    @category.command(name='info')
    async def _category_info(self, ctx: Context, *, category: Optional[discord.CategoryChannel]):
        """Get some information about the specified category.

        This takes the current one if no categories were specified.

        Example:
            **{p}category info Voice Channels**

        Args:
            category (Optional[discord.CategoryChannel]): The category name/ID.
        """
        category = category or ctx.channel.category

        fields = [
            ('Channels', f'{len(category.text_channels)} | {len(category.voice_channels)}'),
            ('Is NSFW', category.is_nsfw()),
            ('Created at', naturaldate(category.created_at))
        ]

        embed = ctx.bot.embed.default(
            ctx, description='\n'.join(f'**{n}**: {v}' for n, v in fields)
        ).set_author(name=f'Information for {category}', icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @category.command(name='create')
    async def _create_category(self, ctx: Context, role: discord.Role, *, name: str):
        """Add a category for the current guild.

        Args:
            role (discord.Role): A role that will be able to see this category.
            name (str): The name of the category.
        """
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @category.command(name='delete')
    async def _delete_category(self, ctx: Context, category: discord.CategoryChannel, *, reason: str = 'Reason not specified'):
        """Deletes the specified category.

        Args:
            category (discord.CategoryChannel): ID or the name of a category.
            reason (str, optional): Reason of deleting category. Defaults to 'Reason not specified'.
        """
        await category.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def channel(self, ctx: Context):
        """The channel-managing commands parent."""
        await ctx.send_help('channel')

    @channel.command(name='info')
    async def _channel_info(self, ctx: Context, channel: Optional[discord.TextChannel]):
        channel = channel or ctx.channel

    @channel.command(name='create')
    async def _create_channel(self, ctx: Context, role: discord.Role, *, name: str):
        """Add a category for the current guild.

        Args:
            role (discord.Role): A role that will be able to see this channel.
            name (str): The name of the channel.
        """
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True)
        }

        await ctx.guild.create_text_channel(name=name, overwrites=overwrites)
        await ctx.message.add_reaction('✅')

    @channel.command(name='delete')
    async def _delete_channel(self, ctx: Context, channel: discord.TextChannel, *, reason: str = 'Reason not specified'):
        """Deletes the specified channel.

        Args:
            channel (discord.TextChannel): A channel you want to delete.
            reason (str, optional): Reason of deleting channel. Defaults to 'Reason not specified'.
        """
        await channel.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.command(aliases=['sm'])
    async def slowmode(self, ctx: Context, time: int):
        """Enables slowmode for a given amount of seconds.

        Args:
            time (int): A time in sec users have to wait to send a message.
        """
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(f'✅ Slowmode has set to {time} seconds.')

    @commands.group(invoke_without_command=True)
    async def role(self, ctx: Context):
        """The role-managing commands parent."""
        await ctx.send_help('role')

    @role.command(name='give')
    async def _give_role(self, ctx: Context, role: discord.Role, user: discord.Member):
        """Give the specified role to a user.

        Args:
            role (discord.Role): The role going to be given.
            user (discord.Member): A member you want to give a role to.
        """
        await user.add_roles(role)
        await ctx.message.add_reaction('✅')

    @role.command(name='take')
    async def _take_role(self, ctx: Context, role: discord.Role, user: discord.Member):
        """Take the specified role from a user.

        Args:
            role (discord.Role): A role you want to take.
            user (discord.Member): A member you want to take a role from.
        """
        await user.remove_roles(role)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def warn(self, ctx: Context, member: discord.Member):
        """A little user-warning system commands parent."""
        await ctx.send_help('warn')

    @warn.command(name='set', aliases=['add'])
    async def _set_warn(self, ctx: Context, member: discord.Member):
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
    async def _remove_warn(self, ctx: Context, member: discord.Member):
        """Takes one warning from a specified user.

        Args:
            member (discord.Member): A member to take a warning from.

        Raises:
            commands.BadArgument: If a member has no warns yet.
        """
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
    async def _reset_warn(self, ctx: Context, member: discord.Member):
        """Resets all warnings from a user.

        Args:
            member (discord.Member): A member you want to take all warns from.

        Raises:
            commands.BadArgument: If a member has no warns yet.
        """
        if ctx.bot.user_cache[member.id]['warns'] == 0:
            raise commands.BadArgument(f'**{member}** has no warnings to reset.')

        confirmation = await ctx.confirm(f'Are you sure? All warnings for {member} are going to be reset.')
        if confirmation:
            query = 'UPDATE users SET warns = 0 WHERE user_id = $1'
            await ctx.bot.pool.execute(query, member.id)
            await ctx.send(f'✅ All warnings were successfully reset for **{member}**!')
            return await ctx.bot.user_cache.refresh()

        await ctx.send('The `user warn resetting` session was closed.')


def setup(bot: Boribay):
    bot.add_cog(Moderation(bot))
