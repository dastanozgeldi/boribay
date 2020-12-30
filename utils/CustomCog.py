from discord.ext import commands


class Cog(commands.Cog):
    '''Custom Cog'''
    def __init__(self, bot, name):
        super().__init__()
        self.bot = bot
        self.name = name
