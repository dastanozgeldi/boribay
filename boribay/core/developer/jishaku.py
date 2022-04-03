from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES

from boribay.core.utils import Cog


class Jishaku(Cog, *OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """A simple Jishaku subclass to achieve the help-command style."""

    icon = "⚙"
