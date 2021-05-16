from boribay.core import Cog

from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES


class Jishaku(Cog, *STANDARD_FEATURES, *OPTIONAL_FEATURES):
    """A simple Jishaku subclass to achieve the help-command style."""
    icon = '⚙'
