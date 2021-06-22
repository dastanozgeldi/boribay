import asyncio
from typing import Optional

import discord
from boribay.core import Cog, Context
from boribay.core.checks import is_mod
from boribay.core.commands.converters import (AuthorCheckConverter,
                                              ColorConverter)
from discord.ext import commands
from humanize import naturaldate


class Moderation(Cog):
    """The moderation extension.

    `Manage guild` permission is required for the user.
    """

    icon = '🛡'

    async def cog_check(self, ctx: Context) -> bool:
        return await is_mod().predicate(ctx)

    @commands.group(invoke_without_command=True)
    async def member(self, ctx: Context) -> None:
        """
        Guild members managing commands parent.
        """
        await ctx.send_help('member')

    @member.command(name='nick')
    @commands.bot_has_guild_permissions(manage_nicknames=True)
    async def _member_nick(
        self, ctx: Context, member: discord.Member, *, new_nick: str
    ) -> None:
        """Changes the member's nickname in the current server.

        Args:
            member (discord.Member): A member whose nickname you want to change.
            new_nick (str): A new nickname for the member.
        """
        await member.edit(nick=new_nick)
        await ctx.message.add_reaction('✅')

    @member.command(name='kick')
    async def _member_kick(
        self, ctx: Context, member: AuthorCheckConverter, *, reason: Optional[str]
    ) -> None:
        """Kicks the member.

        Args:
            member (AuthorCheckConverter): A member you want to kick.
            reason (str, optional): The reason of kicking.
        """
        reason = reason or 'Reason not specified.'
        embed = ctx.embed(title=f'{member} was kicked.', description=reason)

        await ctx.guild.kick(user=member, reason=reason)
        await ctx.send(embed=embed)

    @member.command(name='ban')
    async def _member_ban(
        self, ctx: Context, member: AuthorCheckConverter, *, reason: Optional[str]
    ) -> None:
        """Ban the member.

        Args:
            member (AuthorCheckConverter): A member you want to ban.
            reason (Optional[str]): The reason of banning.
        """
        reason = reason or 'Reason not specified.'
        embed = ctx.embed(title=f'{member} was banned.', description=reason)

        await member.ban(reason=reason)
        await ctx.send(embed=embed)

    @member.command(name='unban')
    async def _member_unban(
        self, ctx: Context, member: AuthorCheckConverter, *, reason: Optional[str]
    ) -> None:
        """Unban the user - remove them from the guild blacklist.

        Args:
            member (AuthorCheckConverter): A member you want to unban.
            reason (str, optional): The reason of unbanning.
        """
        reason = reason or 'Reason not specified.'

        await member.unban(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def category(self, ctx: Context) -> None:
        """
        The category-managing commands parent.
        """
        await ctx.send_help('category')

    @category.command(name='info')
    async def _category_info(
        self, ctx: Context, *, category: Optional[discord.CategoryChannel]
    ) -> None:
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
    async def _create_category(
        self, ctx: Context, role: discord.Role, *, name: str
    ) -> None:
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
    async def _delete_category(
        self,
        ctx: Context,
        category: discord.CategoryChannel,
        *,
        reason: Optional[str]
    ) -> None:
        """Deletes the specified category.

        Args:
            category (discord.CategoryChannel): ID or the name of a category.
            reason (str, optional): Reason of deleting category.
        """
        await category.delete(reason=reason or 'Reason not specified')
        await ctx.message.add_reaction('✅')

    @commands.group(invoke_without_command=True)
    async def channel(self, ctx: Context) -> None:
        """
        The channel-managing commands parent.
        """
        await ctx.send_help('channel')

    @channel.command(name='clear', aliases=('purge',))
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def _clear_channel(self, ctx: Context, limit: int = 2) -> None:
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
    async def _create_channel(
        self, ctx: Context, role: discord.Role, *, name: str
    ) -> None:
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
    async def _delete_channel(
        self, ctx: Context, channel: discord.TextChannel, *, reason: str
    ) -> None:
        """Deletes the specified channel.

        Args:
            channel (discord.TextChannel): A channel you want to delete.
            reason (str, optional): Reason of deleting channel.
        """
        await channel.delete(reason=reason or 'Reason not specified')
        await ctx.message.add_reaction('✅')

    @channel.command(name='slowmode', aliases=('sm',))
    async def _slowmode_channel(self, ctx: Context, time: int) -> None:
        """Enables slowmode for a given amount of seconds.

        Args:
            time (int): A time in sec users have to wait to send a message.
        """
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(f'✅ Slowmode has set to **{time}** seconds.')

    @commands.group(invoke_without_command=True)
    async def role(self, ctx: Context) -> None:
        """
        The role-managing commands parent.
        """
        await ctx.send_help('role')

    @staticmethod
    async def _wait_wizard(
        ctx: Context,
        content: str,
        timeout: float = 20.0,
        message: discord.Message = None
    ) -> str:
        """A wait-for message function to replace repetitions of code.

        Parameters
        ----------
        ctx : Context
            The context instance to get the bot.
        content : str
            Content of a message that is sent beforehand.
        timeout : float, optional
            Time-limit of wait-for, by default 20.0
        message : discord.Message, optional
            To be able to edit a message if it does already exist, by default None

        Returns
        -------
        str
            The message content of the user-input.

        Raises
        ------
        commands.BadArgument
            If time-limit has reached with no arguments provided.
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
    async def _create_role(self, ctx: Context) -> None:
        """Create a role with the interactive way.

        The bot will ask you to provide:
            name, color of the role,
            reason why are you creating it (will be displayed on Audit Logs).
        """
        try:
            cc = ColorConverter()

            role_name = await self._wait_wizard(ctx, 'What shall we call the new role?')

            color_name = await self._wait_wizard(
                ctx, f'Neat, the name is **{role_name}**. What about its color?'
            )
            color = await cc.convert(ctx, color_name)

            reason = await self._wait_wizard(
                ctx, f'Lastly, specify the reason of creating **{role_name}**.'
            )

            role = await ctx.guild.create_role(name=role_name, color=color, reason=reason)
            await ctx.send(f'Great. Created a new role {role.mention}. Now, edit for your purposes.')

        except discord.HTTPException:
            await ctx.send('Failed to create the role.')

    @role.command(name='give')
    async def _give_role(
        self, ctx: Context, role: discord.Role, user: discord.Member
    ) -> None:
        """Give the specified role to a user.

        Args:
            role (discord.Role): The role going to be given.
            user (discord.Member): A member you want to give a role to.
        """
        try:
            await user.add_roles(role)
            await ctx.message.add_reaction('✅')

        except discord.Forbidden:
            await ctx.send(
                f'I am unable to give **{user}** a role.\n'
                f'It is probably caused that {role.mention} is above my role.'
            )

    @role.command(name='take')
    async def _take_role(
        self, ctx: Context, role: discord.Role, user: discord.Member
    ) -> None:
        """Take the specified role from a user.

        Args:
            role (discord.Role): A role you want to take.
            user (discord.Member): A member you want to take a role from.
        """
        try:
            await user.remove_roles(role)
            await ctx.message.add_reaction('✅')

        except discord.Forbidden:
            await ctx.send(
                f'I am unable to take a role from **{user}**.\n'
                f'It is probably caused that {role.mention} is above my role.'
            )

    @role.command(name='delete')
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _delete_role(
        self, ctx: Context, role: discord.Role, *, reason: str
    ) -> None:
        """Delete a guild role through this command.

        Example:
            **{p}role delete @Muted We no longer need this role.**

        Args:
            role (discord.Role): A role to delete (Name/ID/Mention).
            reason (str, optional): The reason of deleting.
        """
        try:
            await role.delete(reason=reason or 'Reason not specified.')
            await ctx.message.add_reaction('✅')

        except discord.HTTPException:
            await ctx.send(f'Failed to delete the role ({role.mention}).')
