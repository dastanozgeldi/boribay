from boribay.core import Boribay, Cog

from .paginators import MyHelpCommand


class Help(Cog):
    """Subclassed help command."""
    icon = '🆘'

    def __init__(self, bot: Boribay):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command
