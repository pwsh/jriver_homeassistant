"""Tests for the MCWS transport layer."""

from __future__ import annotations

from aiohttp import ClientSession
import pytest

from custom_components.jriver.mcws import (
    CannotConnectError,
    InvalidAuthError,
    InvalidRequestError,
    MediaServerError,
    UnsupportedRequestError,
    get_mcws_connection,
)
from custom_components.jriver.mcws.connection import (
    parse_json,
    to_dict,
    to_list,
)

from .conftest import FAILURE, OK


def test_to_dict_without_status() -> None:
    """A root without a Status attribute is treated as OK."""
    ok, values = to_dict('<Fields><Field Name="a">b</Field></Fields>')
    assert ok is True
    assert values == {"a": "b"}


def test_to_dict_skips_unnamed_children() -> None:
    """Children with no Name attribute are ignored."""
    ok, values = to_dict('<Response Status="OK"><Item>x</Item></Response>')
    assert ok is True
    assert values == {}


def test_to_dict_failure() -> None:
    """A Failure status is reported."""
    ok, values = to_dict(FAILURE)
    assert ok is False
    assert values == {}


def test_to_list() -> None:
    """Unnamed items are collected as a list."""
    ok, values = to_list('<Response Status="OK"><Item>a</Item><Item>b</Item></Response>')
    assert ok is True
    assert values == ["a", "b"]


def test_parse_json_tolerates_control_chars() -> None:
    """Raw control characters inside strings do not break parsing."""
    assert parse_json('[{"Name": "a\x01b"}]') == [{"Name": "ab"}]


async def test_connection_urls() -> None:
    """URL helpers and properties."""
    conn = get_mcws_connection("h", 52199, ssl=True)
    assert conn.host == "h"
    assert conn.port == 52199
    assert isinstance(conn.port, int)
    assert conn.host_url == "https://h:52199"
    assert conn.get_url("x") == "https://h:52199/x"
    assert conn.get_mcws_url("Alive") == "https://h:52199/MCWS/v1/Alive"


async def test_connection_auth_username_only() -> None:
    """A username with no password is accepted."""
    conn = get_mcws_connection("h", 1, username="u")
    assert conn._auth is not None
    assert conn._auth.login == "u"
    assert conn._auth.password == ""


async def test_connection_auth_password_only() -> None:
    """A password with no username disables auth rather than raising."""
    conn = get_mcws_connection("h", 1, password="p")
    assert conn._auth is None


async def test_provided_session_not_closed() -> None:
    """A caller supplied session survives connection close."""
    session = ClientSession()
    conn = get_mcws_connection("h", 1, session=session)
    await conn.close()
    assert not session.closed
    conn.own_session()
    await conn.close()
    assert session.closed


async def test_owned_session_closed() -> None:
    """A connection created session is closed."""
    conn = get_mcws_connection("h", 1)
    session = conn._session
    await conn.close()
    assert session.closed


async def test_unauthorised(fake, make_server) -> None:
    """A 401 maps to InvalidAuthError."""
    fake.set("Alive", "nope", status=401)
    ms = await make_server()
    with pytest.raises(InvalidAuthError):
        await ms.alive()


async def test_bad_request(fake, make_server) -> None:
    """A 400 maps to InvalidRequestError."""
    fake.set("Alive", "nope", status=400)
    ms = await make_server()
    with pytest.raises(InvalidRequestError):
        await ms.alive()


async def test_server_error(fake, make_server) -> None:
    """A 500 with an Information attribute maps to MediaServerError."""
    fake.set(
        "Alive",
        '<Response Status="Failure" Information="it broke"/>',
        status=500,
    )
    ms = await make_server()
    with pytest.raises(MediaServerError, match="it broke"):
        await ms.alive()


async def test_server_error_unparseable(fake, make_server) -> None:
    """A 500 with a non-XML body still maps to MediaServerError."""
    fake.set("Alive", "kaboom", content_type="text/plain", status=500)
    ms = await make_server()
    with pytest.raises(MediaServerError):
        await ms.alive()


async def test_unknown_function(fake, make_server) -> None:
    """A 'Function not found' failure maps to UnsupportedRequestError."""
    ms = await make_server()
    with pytest.raises(UnsupportedRequestError):
        await ms.get_repeat()


async def test_other_status(fake, make_server) -> None:
    """Any other error status maps to CannotConnectError."""
    fake.set("Alive", "gone", status=404)
    ms = await make_server()
    with pytest.raises(CannotConnectError):
        await ms.alive()


async def test_cannot_connect() -> None:
    """A refused connection maps to CannotConnectError."""
    conn = get_mcws_connection("127.0.0.1", 1, timeout=1)
    try:
        with pytest.raises(CannotConnectError):
            await conn.get_as_dict("Alive")
    finally:
        await conn.close()


async def test_json_dict(fake, make_server) -> None:
    """A JSON dict response is returned as is."""
    fake.set("Foo", '{"a": 1}', content_type="application/json")
    ms = await make_server()
    ok, resp = await ms.connection.get_as_json_dict("Foo")
    assert ok is True
    assert resp == {"a": 1}


async def test_get_as_list(fake, make_server) -> None:
    """A list response is returned as a list of text values."""
    fake.set("Foo", '<Response Status="OK"><Item>a</Item></Response>')
    ms = await make_server()
    ok, resp = await ms.connection.get_as_list("Foo")
    assert ok is True
    assert resp == ["a"]


async def test_verify_ssl_flag() -> None:
    """verify_ssl is accepted and stored."""
    conn = get_mcws_connection("h", 1, verify_ssl=False)
    assert conn._verify_ssl is False
    await conn.close()


async def test_ok_response(fake, make_server) -> None:
    """A bare OK response parses."""
    fake.set("Foo", OK)
    ms = await make_server()
    ok, resp = await ms.connection.get_as_dict("Foo")
    assert ok is True
    assert resp == {}
