import asyncio
import logging

from boribay.core.bot import Boribay

from .cli import parse_flags, parse_single_flags

log = logging.getLogger('bot.main')


async def main() -> None:
    """The main function of the bot that exactly manages the Boribay app."""
    args = parse_flags()
    parse_single_flags(args)

    # Running the bot.
    bot = Boribay(cli_flags=args)
    await bot.start()


if __name__ == '__main__':
    # TODO: Avoid asyncio.run in the future.
    asyncio.run(main())
