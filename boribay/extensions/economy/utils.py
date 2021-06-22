import re
from typing import Union

from boribay.core.exceptions import NotAnInteger, NotEnough, PastMinimum
from discord.ext import commands


def get_number(
    argument: str.lower,
    *,
    integer: bool = True
) -> Union[int, float]:
    """Sometimes not all users want to specify exact numbers on their bets.

    Arguments like `5k` could lead to the RuntimeError and we want to handle
    those arguments consequently.

    This method parses those arguments into usual numbers, like `5k -> 5000`.

    Parameters
    ----------
    argument : str.lower
        Amount of the bet, e.g 1.6k
    integer : bool, optional
        Whether to return as integer, by default True

    Returns
    -------
    Union[int, float]
        The number parsed from the argument, either int or float according
        to the `bool:integer` parameter.

    Raises
    ------
    ValueError
        If the argument does not look like a number at all.
    """
    if not (argument := argument.replace(',', '').replace('+', '').strip()):
        raise ValueError()

    if argument.endswith('k'):
        argument = str(float(argument.rstrip('k')) * 1_000)

    elif argument.endswith('m'):
        argument = str(float(argument.rstrip('m')) * 1_000_000)

    elif argument.endswith('b'):
        argument = str(float(argument.rstrip('b')) * 1_000_000_000)

    if re.match(r'\de\d+', argument):
        number, expression = argument.split('e')
        number, expression = float(number), round(float(expression))
        argument = float(f'{number}e{expression}') if expression < 24 else 1e24

    argument = float(argument)
    return argument if not integer else round(argument)


def get_amount(_all: float, minimum: int, maximum: int, argument):
    """Similar to the `get_number` method, but this one parses arguments like:

    `all`, `half` and `x%`.
    As you could see it returns a piece of a number (bet) according to the parsed argument.
    """
    argument = argument.lower().strip()

    if argument in ('all'):
        amount = round(_all)

    elif argument in ('half'):
        amount = round(_all / 2)

    elif argument.endswith('%'):
        percent = argument.rstrip('%')
        try:
            percent = float(percent) / 100

        except (TypeError, ValueError):
            raise NotAnInteger(argument)

        else:
            amount = round(_all * percent)

    else:
        try:
            amount = get_number(argument)

        except ValueError:
            raise NotAnInteger(argument)

    if amount > _all:
        raise NotEnough(argument)

    if amount <= 0:
        raise NotAnInteger(argument)

    if minimum <= amount <= maximum:
        return amount

    if amount > maximum:
        return maximum

    raise PastMinimum(minimum)


def CasinoConverter(minimum: int = 100, maximum: int = 100_000):
    class _Wrapper(commands.Converter, int):
        async def convert(self, ctx, argument):
            _all = await ctx.bot.pool.fetchval(
                'SELECT wallet FROM users WHERE user_id = $1',
                ctx.author.id
            )
            amount = get_amount(_all, minimum, maximum, argument)
            return amount

    return _Wrapper
