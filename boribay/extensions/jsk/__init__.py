from boribay.core import Boribay, Cog
from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES

__all__ = ('Jishaku',)


class Jishaku(Cog, *STANDARD_FEATURES, *OPTIONAL_FEATURES):
    """A simple Jishaku subclass to achieve the help-command style."""
    icon = '⚙'


def setup(bot: Boribay):
    bot.add_cog(Jishaku(bot=bot))
