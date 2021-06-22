import logging
import sys

from boribay.cli import parse_flags, parse_single_flags
from boribay.core.bot import Boribay
from boribay.log import init_logging

log = logging.getLogger('bot.main')


def main() -> None:
    """The main function of the bot."""
    # Setting up logging features.
    init_logging(level=logging.INFO)

    # Beforehand flag-parsing.
    args = parse_flags(sys.argv[1:])
    parse_single_flags(args)

    # Initializing the bot class, starting.
    bot = Boribay(cli_flags=args)
    bot.run()


if __name__ == '__main__':
    main()
