"""check_guild_perms, is_mod
are stolen from R. Danny.

Thanks Danny for this awesome piece of code!

The MPL-2.0 License

Copyright (c) 2015 Rapptz"""

from discord.ext import commands


async def check_guild_perms(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if not ctx.guild:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_mod():
    async def predicate(ctx):
        return await check_guild_perms(ctx, {'manage_guild': True})

    return commands.check(predicate)


def beta_command():
    async def predicate(ctx):
        if ctx.author.id not in ctx.bot.owner_ids:
            raise commands.CheckFailure(f'Command `{ctx.command}` is currently in beta-testing and cannot be executed now.')
            return False
        return True

    return commands.check(predicate)
