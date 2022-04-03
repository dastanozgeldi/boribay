import logging

from boribay.core.bot import Boribay
from boribay.main.cli import parse_flags, parse_single_flags

log = logging.getLogger('bot.main')


def main() -> None:
    """The main function of the bot that exactly manages the Boribay app."""
    args = parse_flags()
    parse_single_flags(args)
    bot = Boribay(cli_flags=args)
    bot.run()


if __name__ == '__main__':
    main()
