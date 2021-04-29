# Should belong to boribay/cogs/
from boribay.core import Boribay

from .ideas import Ideas


def setup(bot: Boribay):
    bot.add_cog(Ideas(bot))
