import argparse

__all__ = ('parse_flags',)


def parse_flags(args: list = None) -> argparse.Namespace:
    """CLI function, the place where all the CLI stuff gets handled.

    Parameters
    ----------
    args : list, optional
        The list of arguments to parse from, by default None

    Returns
    -------
    argparse.Namespace
        The namespace of the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Boribay - Discord Bot',
        usage='boribay <instance> [arguments]'
    )

    parser.add_argument(
        '--exclude',
        '-e',
        nargs='+',
        help="Specify cogs you want to exclude on startup."
    )

    parser.add_argument(
        '--token',
        type=str,
        help='Specify the token you want to launch the bot with.'
    )

    parser.add_argument(
        '--version',
        '-V',
        action='store_true',
        help="See Boribay's current version."
    )

    parser.add_argument(
        '--news',
        action='store_true',
        help="See Boribay's news for the current version."
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
        help='Turns on the developer mode.'
    )

    return parser.parse_args(args)
