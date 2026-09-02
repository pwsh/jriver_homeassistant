"""Low level HTTP transport for the JRiver MCWS interface.

Derived from the ``hamcws`` library (https://github.com/3ll3d00d/hamcws) v0.2.7,
Copyright (c) 3ll3d00d, MIT licensed. See ``__init__.py`` for the full notice.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import json
import logging
import re
from typing import Any
from xml.etree import ElementTree

from aiohttp import (
    BasicAuth,
    ClientError,
    ClientResponse,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
)

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "CannotConnectError",
    "InvalidAccessKeyError",
    "InvalidAuthError",
    "InvalidRequestError",
    "MediaServerConnection",
    "MediaServerError",
    "UnsupportedRequestError",
    "get_mcws_connection",
    "parse_json",
    "read_json",
    "read_text",
    "to_dict",
    "to_list",
]

_FUNCTION_NOT_FOUND = re.compile(r"Function '.*' not found")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

type Parser[T] = Callable[[Any], tuple[bool, T]]
type Reader = Callable[[ClientResponse], Awaitable[Any]]


class CannotConnectError(Exception):
    """Exception to indicate an error in connection."""


class InvalidAuthError(Exception):
    """Exception to indicate an error in authentication."""


class MediaServerError(Exception):
    """Exception to indicate a failure internal to the server."""


class InvalidRequestError(Exception):
    """Exception to indicate a malformed request."""


class InvalidAccessKeyError(Exception):
    """Exception to indicate the access key is invalid."""


class UnsupportedRequestError(MediaServerError):
    """Exception to indicate a request for an MCWS function the server lacks."""


async def read_text(resp: ClientResponse) -> str:
    """Read a response body as text regardless of the declared content type."""
    return await resp.text()


def parse_json(text: str) -> Any:
    """Parse JSON emitted by MCWS.

    MC occasionally emits raw control characters inside JSON string values, which
    the standard strict decoder rejects, so they are stripped and the tolerant
    decoder is used.
    """
    return json.loads(_CONTROL_CHARS.sub("", text), strict=False)


async def read_json(resp: ClientResponse) -> Any:
    """Read a response body as (tolerantly parsed) JSON."""
    return parse_json(await resp.text())


def _status_ok(root: ElementTree.Element) -> bool:
    """Return whether the response root reports success.

    Some responses (e.g. ``Library/Fields`` on older MC builds) have no ``Status``
    attribute at all; those are treated as OK so the children are still parsed.
    """
    return root.attrib.get("Status", "OK") == "OK"


def to_dict(content: str) -> tuple[bool, dict[str, str | None]]:
    """Parse an MCWS ``Item`` list into a dict keyed by the ``Name`` attribute."""
    result: dict[str, str | None] = {}
    root = ElementTree.fromstring(content)
    for child in root:
        name = child.attrib.get("Name")
        if name is not None:
            result[name] = child.text
    return _status_ok(root), result


def to_list(content: str) -> tuple[bool, list[str | None]]:
    """Parse an MCWS ``Item`` list into a list of the element text values."""
    root = ElementTree.fromstring(content)
    return _status_ok(root), [child.text for child in root]


def _extract_error(text: str) -> str | None:
    """Extract the ``Information`` attribute from an MCWS failure response."""
    if not text:
        return None
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        _LOGGER.debug("Unparseable error response: %r", text)
        return None
    return root.attrib.get("Information")


async def _request[T](
    session: ClientSession,
    url: str,
    parser: Parser[T],
    reader: Reader = read_text,
    params: dict | None = None,
    timeout: ClientTimeout | None = None,
    auth: BasicAuth | None = None,
    verify_ssl: bool = True,
) -> tuple[bool, T]:
    """Issue a GET and map transport/server failures onto typed exceptions."""
    kwargs: dict[str, Any] = {}
    if not verify_ssl:
        kwargs["ssl"] = False
    try:
        async with session.get(url, params=params, timeout=timeout, auth=auth, **kwargs) as resp:
            try:
                err_text = ""
                if resp.status >= 400:
                    try:
                        err_text = await resp.text()
                    except (ClientError, UnicodeDecodeError):  # pragma: no cover
                        pass
                resp.raise_for_status()
                return parser(await reader(resp))
            except ClientResponseError as e:
                raise _map_response_error(e, url, err_text) from e
    except (ClientError, TimeoutError) as e:
        raise CannotConnectError(f"{url} - {e}") from e


def _map_response_error(e: ClientResponseError, url: str, err_text: str) -> Exception:
    """Map an HTTP error status onto the appropriate exception instance."""
    if e.status == 401:
        return InvalidAuthError(url)
    if e.status == 400:
        return InvalidRequestError(url)
    if e.status == 500:
        info = _extract_error(err_text)
        if info:
            if _FUNCTION_NOT_FOUND.search(info):
                return UnsupportedRequestError(f"{url} - {info}")
            return MediaServerError(f"{url} - {info}")
        return MediaServerError(f"{url} produces {err_text}")
    return CannotConnectError(f"{e.message} - {url}")


class MediaServerConnection:
    """A connection to MCWS."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        ssl: bool = False,
        timeout: float = 5,
        session: ClientSession | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Create a connection.

        Basic auth is enabled when ``username`` is supplied; ``password`` alone is
        ignored as MCWS has no notion of a passwordless user name.
        """
        self._session = session
        self._close_session_on_exit = False
        if self._session is None:
            self._session = ClientSession()
            self._close_session_on_exit = True

        self._timeout = ClientTimeout(total=timeout)
        self._auth = BasicAuth(username, password or "") if username is not None else None
        self._verify_ssl = verify_ssl
        self._protocol = f"http{'s' if ssl else ''}"
        self._host = host
        self._port = port
        self._host_port = f"{host}:{port}"
        self._host_url = f"{self._protocol}://{self._host_port}"
        self._base_url = f"{self._host_url}/MCWS/v1"

    @property
    def host(self) -> str:
        """The server host."""
        return self._host

    @property
    def port(self) -> int:
        """The server port."""
        return self._port

    @property
    def host_url(self) -> str:
        """The scheme://host:port prefix."""
        return self._host_url

    async def get[T](
        self,
        path: str,
        parser: Parser[T],
        reader: Reader = read_text,
        params: dict | None = None,
    ) -> tuple[bool, T]:
        """Issue a GET against MCWS, parsing the content with ``parser``."""
        return await _request(
            self._session,
            self.get_mcws_url(path),
            parser,
            reader,
            params,
            timeout=self._timeout,
            auth=self._auth,
            verify_ssl=self._verify_ssl,
        )

    async def get_as_dict(
        self, path: str, params: dict | None = None
    ) -> tuple[bool, dict[str, str | None]]:
        """Parse an MCWS ``Item`` list into a dict keyed by the Name attribute."""
        return await self.get(path, to_dict, read_text, params)

    async def get_as_list(
        self, path: str, params: dict | None = None
    ) -> tuple[bool, list[str | None]]:
        """Parse an MCWS ``Item`` list into a list of element text values."""
        return await self.get(path, to_list, read_text, params)

    async def get_as_json_list(
        self, path: str, params: dict | None = None
    ) -> tuple[bool, list[dict]]:
        """Return a JSON list response as is."""
        return await self.get(path, lambda d: (True, d), read_json, params)

    async def get_as_json_dict(self, path: str, params: dict | None = None) -> tuple[bool, dict]:
        """Return a JSON dict response as is."""
        return await self.get(path, lambda d: (True, d), read_json, params)

    def get_url(self, path: str) -> str:
        """Build a URL relative to the server root."""
        return f"{self._host_url}/{path}"

    def get_mcws_url(self, path: str) -> str:
        """Build a URL relative to the MCWS v1 root."""
        return f"{self._base_url}/{path}"

    def own_session(self) -> None:
        """Take responsibility for closing the session this connection uses."""
        self._close_session_on_exit = True

    async def close(self) -> None:
        """Close the session if this connection created it."""
        if self._close_session_on_exit and self._session is not None:
            await self._session.close()
            self._close_session_on_exit = False


def get_mcws_connection(
    host: str,
    port: int,
    username: str | None = None,
    password: str | None = None,
    ssl: bool = False,
    timeout: float = 5,
    session: ClientSession | None = None,
    verify_ssl: bool = True,
) -> MediaServerConnection:
    """Return a MCWS connection."""
    return MediaServerConnection(host, port, username, password, ssl, timeout, session, verify_ssl)
