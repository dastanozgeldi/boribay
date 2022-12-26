import asyncio
import logging
from dotenv import load_dotenv

from boribay.core.bot import Boribay
from boribay.main.cli import parse_flags, parse_single_flags

load_dotenv()
log = logging.getLogger("bot.main")


async def main() -> None:
    """The main function of the bot that exactly manages the Boribay app."""
    args = parse_flags()
    parse_single_flags(args)
    bot = Boribay(cli_flags=args)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
