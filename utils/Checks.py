"""check_guild_perms, is_mod
are stolen from R. Danny.

Thanks Danny for this awesome piece of code!

The MIT License (MIT)

Copyright (c) 2015 Rapptz"""

from discord.ext import commands


async def check_guild_perms(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_mod():
    async def predicate(ctx):
        return await check_guild_perms(ctx, {'manage_guild': True})
    return commands.check(predicate)


def has_voted():
    async def predicate(ctx):
        check = await ctx.bot.dblpy.get_user_vote(ctx.author.id)
        if check:
            return True
        else:
            raise commands.CheckFailure('This message means that you didn\'t vote last 12 hours.\n'
                                        f'Fix it clicking **[here!]({ctx.bot.topgg_url})**')
            return False
    return commands.check(predicate)
