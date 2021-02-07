from discord.ext.commands import Cog as C


class Cog(C):
    '''A Custom Cog with one extra feature lol.'''

    def __init__(self, bot, name):
        super().__init__()
        self.bot = bot
        self.name = name
