"""Tests for connection bootstrap and access key resolution."""

from __future__ import annotations

from aiohttp import ClientSession
import pytest

from custom_components.jriver.mcws import (
    CannotConnectError,
    InvalidAccessKeyError,
    discovery,
    load_media_server,
    resolve_access_key,
    try_connect,
)

ALIVE = """<Response Status="OK">
<Item Name="ProgramVersion">33.0.33</Item>
<Item Name="FriendlyName">MyServer</Item>
<Item Name="Platform">Linux</Item>
<Item Name="AccessKey">abc123</Item>
</Response>"""

NO_TOKEN = '<Response Status="OK"><Item Name="Token"></Item></Response>'


def _lookup(port: int) -> str:
    return (
        '<Response Status="OK">'
        "<keyid>abc123</keyid>"
        "<ip>1.2.3.4</ip>"
        f"<port>{port}</port>"
        "<localiplist>127.0.0.1,10.0.0.1</localiplist>"
        "<macaddresslist>aa:bb:cc,dd:ee:ff</macaddresslist>"
        "<https_port>1</https_port>"
        "</Response>"
    )


@pytest.fixture
async def server(aiohttp_server, fake):
    """Start the fake server with a working Alive endpoint."""
    fake.set("Alive", ALIVE)
    return await aiohttp_server(fake.app())


async def test_try_connect(server, fake) -> None:
    """try_connect authenticates and calls alive."""
    session = ClientSession()
    try:
        ms = await try_connect("localhost", server.port, session=session)
        assert ms.media_server_info.name == "MyServer"
        assert fake.count("Authenticate") == 1
    finally:
        await session.close()


async def test_try_connect_no_token(server, fake) -> None:
    """An empty token raises CannotConnectError (not NameError)."""
    fake.set("Authenticate", NO_TOKEN)
    session = ClientSession()
    try:
        with pytest.raises(CannotConnectError):
            await try_connect("localhost", server.port, session=session)
    finally:
        await session.close()


async def test_resolve_access_key(server, fake, monkeypatch) -> None:
    """An access key resolves to a ServerAddress."""
    fake.set_lookup(_lookup(server.port))
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    session = ClientSession()
    try:
        addr = await resolve_access_key("abc123", session)
    finally:
        await session.close()
    assert addr is not None
    assert addr.key_id == "abc123"
    assert addr.ip == "1.2.3.4"
    assert addr.local_ip_list == ["127.0.0.1", "10.0.0.1"]
    assert addr.mac_address_list == ["aa:bb:cc", "dd:ee:ff"]
    assert addr.http_port == server.port
    assert addr.https_port == 1
    assert fake.params("lookup") == {"id": "abc123"}


async def test_resolve_access_key_closes_own_session(server, fake, monkeypatch) -> None:
    """A session created internally is awaited closed."""
    fake.set_lookup(_lookup(server.port))
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    created: list[ClientSession] = []
    real_session = ClientSession

    def _track(*args, **kwargs):
        session = real_session(*args, **kwargs)
        created.append(session)
        return session

    monkeypatch.setattr(discovery, "ClientSession", _track)
    assert await resolve_access_key("abc123") is not None
    assert created
    assert all(s.closed for s in created)


async def test_resolve_access_key_failure(server, fake, monkeypatch) -> None:
    """A failed lookup returns None."""
    fake.set_lookup('<Response Status="Failure"/>')
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    session = ClientSession()
    try:
        assert await resolve_access_key("abc123", session) is None
    finally:
        await session.close()


async def test_load_media_server_by_host(server, fake) -> None:
    """A direct host connection returns a usable server with no macs."""
    ms, macs = await load_media_server(host="localhost", port=server.port)
    try:
        assert macs == []
        assert ms.media_server_info.name == "MyServer"
        # the internally created session was handed to the connection
        assert await ms.alive()
    finally:
        await ms.close()


async def test_load_media_server_by_access_key(server, fake, monkeypatch) -> None:
    """An access key resolves and connects to the first working ip."""
    fake.set_lookup(_lookup(server.port))
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    session = ClientSession()
    try:
        ms, macs = await load_media_server(access_key="abc123", session=session)
        assert macs == ["aa:bb:cc", "dd:ee:ff"]
        assert ms.media_server_info.name == "MyServer"
    finally:
        await session.close()


async def test_load_media_server_invalid_access_key(server, fake, monkeypatch) -> None:
    """An unresolvable access key raises InvalidAccessKeyError."""
    fake.set_lookup('<Response Status="Failure"/>')
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    session = ClientSession()
    try:
        with pytest.raises(InvalidAccessKeyError):
            await load_media_server(access_key="abc123", session=session)
    finally:
        await session.close()


async def test_load_media_server_no_reachable_ip(server, fake, monkeypatch) -> None:
    """When no resolved ip connects, CannotConnectError is raised."""
    fake.set_lookup(
        '<Response Status="OK"><keyid>abc123</keyid><port>1</port>'
        "<localiplist>127.0.0.1</localiplist></Response>"
    )
    monkeypatch.setattr(
        discovery,
        "ACCESS_KEY_LOOKUP_URL",
        f"http://localhost:{server.port}/libraryserver/lookup",
    )
    session = ClientSession()
    try:
        with pytest.raises(CannotConnectError):
            await load_media_server(access_key="abc123", session=session, timeout=1)
    finally:
        await session.close()


async def test_load_media_server_requires_host() -> None:
    """Neither host nor access key is an error."""
    session = ClientSession()
    try:
        with pytest.raises(ValueError, match="host or access_key"):
            await load_media_server(session=session)
    finally:
        await session.close()
