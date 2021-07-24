from boribay.core.utils import Cog

from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES


class Jishaku(Cog, *OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """A simple Jishaku subclass to achieve the help-command style."""

    icon = '⚙'
