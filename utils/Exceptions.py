from discord.ext import commands


class TooManyOptions(commands.CommandError):
    pass


class NotEnoughOptions(commands.CommandError):
    pass
