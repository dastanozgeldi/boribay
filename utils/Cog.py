from discord.ext import commands


class Cog(commands.Cog):
    '''A Custom Cog with one extra feature lol.'''

    def __init__(self, bot, name):
        super().__init__()
        self.bot = bot
        self.name = name
