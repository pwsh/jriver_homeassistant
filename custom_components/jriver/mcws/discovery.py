"""Server discovery/bootstrap helpers for the JRiver MCWS interface.

Derived from the ``hamcws`` library (https://github.com/3ll3d00d/hamcws) v0.2.7,
Copyright (c) 3ll3d00d, MIT licensed. See ``__init__.py`` for the full notice.
"""

from __future__ import annotations

import logging
from xml.etree import ElementTree

from aiohttp import ClientSession

from .connection import (
    CannotConnectError,
    InvalidAccessKeyError,
    _request,
    get_mcws_connection,
    read_text,
)
from .models import ServerAddress
from .server import MediaServer

_LOGGER = logging.getLogger(__name__)

__all__ = ["load_media_server", "resolve_access_key", "try_connect"]

ACCESS_KEY_LOOKUP_URL = "http://webplay.jriver.com/libraryserver/lookup"


async def try_connect(
    host: str,
    port: int,
    username: str | None = None,
    password: str | None = None,
    session: ClientSession | None = None,
    ssl: bool = False,
    timeout: float = 5,
    verify_ssl: bool = True,
) -> MediaServer:
    """Try to connect to the given host/port."""
    _LOGGER.debug("Connecting to %s:%s", host, port)
    conn = get_mcws_connection(
        host,
        port,
        username=username,
        password=password,
        ssl=ssl,
        timeout=timeout,
        session=session,
        verify_ssl=verify_ssl,
    )
    ms = MediaServer(conn)
    if not await ms.get_auth_token():
        raise CannotConnectError(f"Unexpected response from {host}:{port}")
    await ms.alive()
    return ms


async def resolve_access_key(
    access_key: str, session: ClientSession | None = None
) -> ServerAddress | None:
    """Resolve an access key into a server address."""
    close_it = False
    if session is None:
        session = ClientSession()
        close_it = True

    def _parse(content: str) -> tuple[bool, dict[str, str | None]]:
        result: dict[str, str | None] = {}
        root = ElementTree.fromstring(content)
        for child in root:
            result[child.tag] = child.text
        return root.attrib.get("Status", "OK") == "OK", result

    try:
        ok, values = await _request(
            session,
            ACCESS_KEY_LOOKUP_URL,
            _parse,
            read_text,
            {"id": access_key},
        )
        return ServerAddress(values) if ok else None
    finally:
        if close_it:
            await session.close()


async def load_media_server(
    access_key: str | None = None,
    host: str | None = None,
    port: int = 0,
    username: str | None = None,
    password: str | None = None,
    use_ssl: bool = False,
    session: ClientSession | None = None,
    timeout: float = 5,
    verify_ssl: bool = True,
) -> tuple[MediaServer, list[str]]:
    """Use the supplied details to obtain a MediaServer connection.

    Returns the connected server and the list of MAC addresses reported by the
    access key lookup (empty when connecting directly to a host).
    """
    close_it = False
    if session is None:
        session = ClientSession()
        close_it = True

    try:
        if access_key:
            _LOGGER.debug("Looking up access key %s", access_key)
            server_info = await resolve_access_key(access_key, session)
            if not server_info:
                raise InvalidAccessKeyError(access_key)
            for ip in server_info.local_ip_list:
                try:
                    ms = await try_connect(
                        ip,
                        server_info.https_port if use_ssl else server_info.http_port,
                        username,
                        password,
                        session,
                        ssl=use_ssl,
                        timeout=timeout,
                        verify_ssl=verify_ssl,
                    )
                except CannotConnectError:
                    continue
                _LOGGER.debug("Access key %s resolved to %s:%s", access_key, ip, server_info.port)
                if close_it:
                    # hand the session to the server rather than closing it here
                    ms.connection.own_session()
                    close_it = False
                return ms, server_info.mac_address_list
            raise CannotConnectError(f"No reachable server for access key {access_key}")
        if not host:
            raise ValueError("host or access_key is required")
        ms = await try_connect(
            host,
            port,
            username,
            password,
            session,
            ssl=use_ssl,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )
        if close_it:
            ms.connection.own_session()
            close_it = False
        return ms, []
    finally:
        if close_it:
            await session.close()
