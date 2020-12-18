from utils.HelpCommand import BaseCog, MyHelpCommand


class Help(BaseCog):
    """Subclassed help command."""

    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(
            command_attrs=dict(
                hidden=True,
                aliases=['h'],
                brief='Basically shows the message you currently looking at.'
            )
        )
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
