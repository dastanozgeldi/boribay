from typing import Any
from aiohttp.client import ClientSession, _RequestContextManager


class ProxiedClientSession:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.proxy_url = kwargs.pop('proxy_url')

        self.permanent_headers = {
            'Proxy-Authorization-Key': kwargs.pop('authorization'),
            'Accept': 'application/json'
        }
        self.session = ClientSession(*args, **kwargs)

    def get(self, url: str, *args: Any, **kwargs: Any) -> _RequestContextManager:
        headers = kwargs.pop('headers', {})
        headers.update(self.permanent_headers)
        headers['Requested-URI'] = url
        return self._session.get(self.proxy_url, headers=headers, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> _RequestContextManager:
        headers = kwargs.pop('headers', {})
        headers.update(self.permanent_headers)
        headers['Requested-URI'] = url
        return self._session.get(self.proxy_url, headers=headers, *args, **kwargs)
