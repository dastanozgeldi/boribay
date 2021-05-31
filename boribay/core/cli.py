import argparse

__all__ = ('parse_flags',)


# Use those args somewhere.
def parse_flags(args):
    parser = argparse.ArgumentParser(
        description='Boribay - Discord Bot',
        usage='boribay <instance> [arguments]'
    )

    parser.add_argument(
        '--version',
        '-V',
        action='store_true',
        help='See Boribay\'s current version.'
    )

    parser.add_argument(
        '--no-cogs',
        '-nc',
        action='store_true',
        help='Runs the bot with no cogs loaded, only the bot itself.'
    )

    parser.add_argument(
        '--developer',
        '-D',
        action='store_true',
        help='Turns on the developer mode'
    )

    return parser.parse_args(args)
