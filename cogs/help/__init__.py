from utils.Cog import Cog
from .Help import MyHelpCommand


class Help(Cog):
    """Subclassed help command."""
    icon = '🆘'
    name = 'Help'

    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(command_attrs=dict(hidden=True, aliases=['h']))
        bot.help_command.cog = self

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
