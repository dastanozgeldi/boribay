from discord.ext import commands

__all__ = ('Cog',)


class Cog(commands.Cog):
    """The customized cog instance for Boribay.

    All cogs of this bot will be of this type.

    This class inherits from `discord.ext.commands.Cog`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'{self.icon} {self.__class__.__name__}'
