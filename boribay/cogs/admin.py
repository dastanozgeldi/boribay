from typing import Optional

import discord
from discord.ext import commands
from boribay.utils import Cog


class Admin(Cog):
    """Administration extension. A module that is created to keep
    discipline in the server. Purging messages, muting members, channel create
    command, all of them are here."""
    icon = '👩‍⚖️'
    name = 'Administration'

    async def cog_check(self, ctx):
        return await commands.has_guild_permissions(administrator=True).predicate(ctx)

    @commands.command()
    async def addbalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Increase someone's balance for being well behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('Balance adding limit has reached. Specify between 10 and 100 000')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank + $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully added **{amount} batyrs** to **{member}**!')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    async def removebalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Decrease someone's balance for being bad behaved."""
        member = member or ctx.author
        query = 'UPDATE users SET bank = bank - $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully removed **{amount} batyrs** from **{member}**!')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    async def ban(self, ctx, member: commands.MemberConverter, *, reason: str = 'Reason not specified.'):
        """Bans a user.
        Args: member (discord.Member): a member you want to ban.
        reason (str, optional): Reason why you are banning. Defaults to None."""
        await member.ban(reason=reason)
        await ctx.message.add_reaction('✅')
        # from command, an on_member_ban event will be triggered.

    @commands.command()
    async def unban(self, ctx, member: commands.MemberConverter, *, reason: str = 'Reason not specified.'):
        """Unban a user - remove from the guild banned members.
        Args: user (discord.User): Normally takes user ID.
        Returns: Exception: If given user id isn't in server ban-list."""
        await member.unban(reason=reason)
        await ctx.message.add_reaction('✅')
        # from command, an on_member_ban event will be triggered.

    @commands.command()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def deletecategory(self, ctx, category: discord.CategoryChannel, *, reason: Optional[str]):
        """Deletes a specififed category.
        Args: category (discord.CategoryChannel): ID of a category.
        reason (str, optional): Reason why you are deleting a category. Defaults to None."""
        await category.delete(reason=reason)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def deletechannel(self, ctx, channel: discord.TextChannel, *, reason: Optional[str]):
        """Deletes a specified channel.
        Args: channel (Optional[discord.TextChannel]): A channel you want to delete,
        deletes current channel if argument was not specified.
        reason (optional): Reason why you are deleting a channel."""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Admin())
