import asyncio
from io import BytesIO
from typing import Any, Optional

import aiohttp
import nextcord


class BaseWrapper:
    """The base class for all following wrappers that must subclass this instance."""

    BASE_URL: str

    def __init__(
        self,
        token: str,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None
    ) -> None:
        self.token = token
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(loop=loop)

    def make_image(self, path: str, filename: Optional[str] = None) -> nextcord.File:
        # Should be overridden.
        raise NotImplementedError


class AlexFlipnoteWrapper(BaseWrapper):
    BASE_URL = 'https://api.alexflipnote.dev/'

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    def make_image(self, path: str, filename: Optional[str] = None) -> nextcord.File:
        resp = await self.session.get(
            self.BASE_URL + path,
            headers={'Authorization': self.token}
        )
        if not resp.status != 200:
            ...  # Raise something good

        fp = BytesIO(await resp.read())
        return nextcord.File(fp, filename or 'alexflipnote.png')


class DagpiWrapper(BaseWrapper):
    BASE_URL = 'https://beta.dagpi.xyz/image/'

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    def make_image(self, path: str, filename: Optional[str] = None) -> nextcord.File:
        resp = await self.session.get(
            self.BASE_URL + path,
            headers={'Authorization': self.token}
        )
        if not resp.status != 200:
            ...

        fp = BytesIO(await resp.read())
        return nextcord.File(fp, filename or 'dagpi.png')
