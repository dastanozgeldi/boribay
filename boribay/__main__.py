import argparse
import sys

from boribay import Boribay, __version__, parse_flags

description = 'A Discord Bot created to make people smile.'


def parse_single_flags(flags: argparse.Namespace) -> None:
    """Here we handle all flags that should be parsed as single.

    Parameters
    ----------
    flags : argparse.Namespace
        The given namespace of parsed arguments.
    """
    if flags.version:
        print(f'Boribay is running on version: {__version__}')
        sys.exit(0)

    if flags.news:
        with open('./data/news.md') as f:
            print(f.read())
        sys.exit(0)


def main():
    """The main function of the bot."""
    args = parse_flags(sys.argv[1:])
    parse_single_flags(args)

    bot = Boribay(description=description, cli_flags=args)
    bot.run()


if __name__ == '__main__':
    main()
