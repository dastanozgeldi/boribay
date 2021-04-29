import asyncio
from typing import Optional

import discord
from boribay.core import Boribay, Cog, Context
from boribay.utils import AuthorCheckConverter, ColorConverter, is_mod
from discord.ext import commands
from humanize import naturaldate


class Moderation(Cog):
    """Commands for moderators. Manage guild permission required."""
    icon = '🛡'

    def __init__(self, bot: Boribay):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        return await is_mod().predicate(ctx)

    @commands.group(invoke_without_command=True)
    async def member(self, ctx: Context):
        await ctx.send_help('member')

    @member.command(name='nick')
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    async def _member_nick(self, ctx: Context, member: discord.Member, *, new_nick: str):
        """Changes the member's nickname in the current server.

        Args:
            member (discord.Member): A member whose nickname you want to change.
            new_nick (str): A new nickname for the member.
        """
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @member.command(name='kick')
    async def _member_kick(self, ctx: Context, member: AuthorCheckConverter, *, reason='Reason not specified.'):
        """Kicks the member.

        Args:
            member (AuthorCheckConverter): A member you want to kick.
            reason (str, optional): The reason of kicking. Defaults to 'Reason not specified.'.
        """
        dest = ctx.bot.guild_cache.get('logging_channel') or ctx
        await ctx.guild.kick(user=member, reason=reason)

        embed = ctx.embed(title=f'{member} was kicked.', description=reason)
        await dest.send(embed=embed)

    @member.command(name='ban')
    async def _member_ban(self, ctx: Context, member: AuthorCheckConverter, *, reason: str = 'Reason not specified.'):
        """Ban the member.

        Args:
            member (AuthorCheckConverter): A member you want to ban.
            reason (str, optional): The reason of banning. Defaults to 'Reason not specified.'.
        """
        await member.ban(reason=reason)
        await ctx.message.add_reaction('✅')
        # from command, an on_member_ban event will be triggered.

    @member.command(name='unban')
    async def _member_unban(self, ctx: Context, member: AuthorCheckConverter, *, reason: str = 'Reason not specified.'):
        """Unban the user - remove them from the guild blacklist.

        Args:
            member (AuthorCheckConverter): A member you want to unban.
            reason (str, optional): The reason of unbanning. Defaults to 'Reason not specified.'.
        """
        await member.unban(reason=reason)
        await ctx.message.add_reaction('✅')

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

        embed = ctx.embed(
            description='\n'.join(f'**{n}**: {v}' for n, v in fields)
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

    @channel.command(name='clear', aliases=['purge'])
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def _clear_channel(self, ctx: Context, limit: int = 2):
        """Purges the given amount of messages.

        Keep in mind that the limit is 100 messages.

        Args:
            limit (int, optional): Amount of messages to purge. Defaults to 2.

        Raises:
            commands.BadArgument: If the message-limit has reached (100).
        """
        if limit > 100:
            raise commands.BadArgument('That is too big amount. The maximum is 100')

        try:
            await ctx.channel.purge(limit=limit)

        except discord.HTTPException:
            await ctx.send(f'Failed to purge {limit} messages.')

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

    @channel.command(name='slowmode', aliases=['sm'])
    async def _slowmode_channel(self, ctx: Context, time: int):
        """Enables slowmode for a given amount of seconds.

        Args:
            time (int): A time in sec users have to wait to send a message.
        """
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(f'✅ Slowmode has set to **{time}** seconds.')

    @commands.group(invoke_without_command=True)
    async def role(self, ctx: Context):
        """The role-managing commands parent."""
        await ctx.send_help('role')

    @staticmethod
    async def _wait_wizard(ctx, content: str, timeout: float = 20.0, message: discord.Message = None) -> str:
        """A wait-for message function to replace repetitions of code.

        Args:
            ctx (Context): The context isntance to get the bot instance.
            content (str): Content of a message that is sent beforehand.
            timeout (float, optional): Time-limit of wait-for. Defaults to 20.0.
            message (discord.Message, optional): To be able to edit a message
            if it does already exist. Defaults to None.

        Raises:
            commands.BadArgument: If time-limit has reached with no arguments provided.

        Returns:
            str: The message content of the user-input.
        """
        try:
            message = await message.edit(content=content)

        except AttributeError:
            message = await ctx.send(content)

        try:
            thing = await ctx.bot.wait_for(
                'message', timeout=timeout,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

        except asyncio.TimeoutError:
            raise commands.BadArgument('❌ You took long.')

        return thing.content

    @role.command(name='create')
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _create_role(self, ctx: Context):
        """Create a role with the interactive way.

        The bot will ask you to provide:
            name, color of the role,
            reason why are you creating it (will be displayed on Audit Logs).
        """
        try:
            cc = ColorConverter()

            role_name = await self._wait_wizard(ctx, 'What shall we call the new role?')

            color_name = await self._wait_wizard(ctx, f'Neat, the name is **{role_name}**. What about its color?\n')
            color = await cc.convert(ctx, color_name)

            reason = await self._wait_wizard(ctx, f'Lastly, specify the reason of creating **{role_name}**.')

            role = await ctx.guild.create_role(name=role_name, color=color, reason=reason)
            await ctx.send(f'Great. Created a new role {role.mention}. Now, edit for your purposes.')

        except discord.HTTPException:
            await ctx.send('Failed to create the role.')

    @role.command(name='give')
    async def _give_role(self, ctx: Context, role: discord.Role, user: discord.Member):
        """Give the specified role to a user.

        Args:
            role (discord.Role): The role going to be given.
            user (discord.Member): A member you want to give a role to.
        """
        try:
            await user.add_roles(role)
            return await ctx.message.add_reaction('✅')

        except discord.Forbidden:
            return await ctx.send(f'I am unable to give **{user}** a role.\n'
                                  f'It is probably caused that {role.mention} is above my role.')

    @role.command(name='take')
    async def _take_role(self, ctx: Context, role: discord.Role, user: discord.Member):
        """Take the specified role from a user.

        Args:
            role (discord.Role): A role you want to take.
            user (discord.Member): A member you want to take a role from.
        """
        try:
            await user.remove_roles(role)
            return await ctx.message.add_reaction('✅')

        except discord.Forbidden:
            return await ctx.send(f'I am unable to take a role from **{user}**.\n'
                                  f'It is probably caused that {role.mention} is above my role.')

    @role.command(name='delete')
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _delete_role(self, ctx: Context, role: discord.Role, *, reason: str = 'Reason not specified.'):
        """Delete a guild role through this command.

        Example:
            **{p}role delete @Muted We no longer need this role.**

        Args:
            role (discord.Role): A role to delete (Name/ID/Mention).
            reason (str, optional): The reason of deleting. Defaults to 'Reason not specified.'.
        """
        try:
            await role.delete(reason=reason)

        except discord.HTTPException:
            await ctx.send(f'Failed to delete the role ({role.mention}).')


def setup(bot: Boribay):
    bot.add_cog(Moderation(bot))
