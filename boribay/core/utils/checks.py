import re
from typing import Dict

from nextcord.ext import commands

__all__ = (
    'is_mod',
    'beta_command',
    'is_valid_alias',
    'is_blacklisted',
)


async def check_guild_perms(
    ctx: commands.Context,
    perms: Dict[str, bool],
    *,
    check: object = all
) -> bool:
    """Method that checks the contextual guild with given permissions.

    Parameters
    ----------
    ctx : commands.Context
        The context instance.
    perms : Dict[str, bool]
        A dict of permissions, e.g {'manage_guild': True}
    check : object, optional
        The function to check with, either 'any' | 'all', by default all

    Returns
    -------
    bool
        True - if the check got passed, otherwise False.
    """
    if await ctx.bot.is_owner(ctx.author):
        return True
    if not ctx.guild:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_mod():
    """The method to check whether the message author has a moderator perms."""

    async def predicate(ctx: commands.Context):
        return await check_guild_perms(ctx, {'manage_guild': True})

    return commands.check(predicate)


def beta_command():
    """The check to mark a command as a "beta" one that is only available

    for the bot owners and no one else.
    """

    async def predicate(ctx: commands.Context):
        if ctx.author.id not in ctx.bot.owner_ids:
            raise commands.CheckFailure(
                f'Command `{ctx.command}` is currently in beta-testing'
                ' and cannot be executed now.'
            )
            return False
        return True

    return commands.check(predicate)


def is_valid_alias(name: str) -> bool:
    """A quick alias name validness check.

    Parameters
    ----------
    name : str
        The name of the alias to check.

    Returns
    -------
    bool
        True - if the name passed all checks, otherwise False.
    """
    return not bool(re.search(r'\s', name)) and name.isprintable()


async def is_blacklisted(ctx: commands.Context) -> bool:
    """Check whether the message author is in the blacklist.

    Parameters
    ----------
    ctx : commands.Context
        Automatically passed context object.

    Returns
    -------
    bool
        False if the author is blacklisted.
    """
    user = ctx.user_cache[ctx.author.id]
    return not user.get('blacklisted', False)
