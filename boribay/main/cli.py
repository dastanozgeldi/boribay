import argparse
import sys


def parse_single_flags(flags: argparse.Namespace) -> None:
    """Here we handle all flags that should be parsed as single.

    Parameters
    ----------
    flags : argparse.Namespace
        The given namespace of parsed arguments.
    """
    if flags.version:
        print("Boribay is running on version: v2")
        sys.exit(0)


def parse_flags(args: argparse.Namespace = None) -> argparse.Namespace:
    """CLI function, the place where all the CLI stuff gets handled.

    Parameters
    ----------
    args : argparse.Namespace, optional
        The list of arguments to parse from, by default None

    Returns
    -------
    argparse.Namespace
        The namespace of the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Boribay - Discord Bot", usage="boribay [arguments]"
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="Specify cogs you want to exclude on startup.",
    )
    parser.add_argument(
        "--token", type=str, help="Specify the token you want to launch the bot with."
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="See Boribay's current version."
    )
    parser.add_argument(
        "-nc",
        "--no-cogs",
        action="store_true",
        help="Runs the bot with no cogs loaded, only the bot itself.",
    )
    parser.add_argument(
        "-d", "--developer", action="store_true", help="Turns on the developer mode."
    )
    return parser.parse_args(args)
