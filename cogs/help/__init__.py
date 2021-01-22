from utils.CustomCog import Cog
from utils.HelpCommand import MyHelpCommand


class Help(Cog):
    """Subclassed help command."""

    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(command_attrs=dict(hidden=True, aliases=['h']))
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
