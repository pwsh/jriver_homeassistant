"""Fixtures for the vendored MCWS client tests.

These tests exercise pure aiohttp code and deliberately shadow the Home
Assistant oriented autouse fixtures defined in ``tests/conftest.py``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from aiohttp import web
import pytest

from custom_components.jriver.mcws import MediaServer, get_mcws_connection

AUTHENTICATE_OK = """<Response Status="OK">
<Item Name="Token">1234567</Item>
<Item Name="ReadOnly">0</Item>
<Item Name="PreLicensed">0</Item>
</Response>"""

OK = '<Response Status="OK"/>'
FAILURE = '<Response Status="Failure"/>'
NOT_FOUND = '<Response Status="Failure" Information="Function \'Playback/Foo\' not found."/>'


@pytest.fixture(autouse=True)
def enable_sockets(socket_enabled):
    """Allow the local aiohttp test server to bind a socket."""
    yield


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations():
    """Shadow the HA fixture; these tests do not need HA."""
    yield


@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Shadow the HA fixture; these tests do not need HA."""
    yield


class FakeMediaServer:
    """A canned-response MCWS server."""

    def __init__(self) -> None:
        """Start with only ``Authenticate`` configured."""
        self.responses: dict[str, tuple[str, str, int]] = {
            "Authenticate": (AUTHENTICATE_OK, "text/xml", 200)
        }
        self.requests: list[tuple[str, dict[str, str]]] = []
        self.lookup: tuple[str, str, int] | None = None

    def set(
        self,
        path: str,
        text: str,
        content_type: str = "text/xml",
        status: int = 200,
    ) -> None:
        """Register the response for an MCWS function."""
        self.responses[path] = (text, content_type, status)

    def set_lookup(self, text: str, status: int = 200) -> None:
        """Register the response for the access key lookup endpoint."""
        self.lookup = (text, "text/xml", status)

    def params(self, path: str) -> dict[str, str]:
        """Return the query params of the last request to ``path``."""
        for recorded_path, params in reversed(self.requests):
            if recorded_path == path:
                return params
        raise AssertionError(f"no request recorded for {path}")

    def count(self, path: str) -> int:
        """Return how many requests were made to ``path``."""
        return sum(1 for recorded, _ in self.requests if recorded == path)

    def app(self) -> web.Application:
        """Build the aiohttp application."""
        app = web.Application()
        app.add_routes(
            [
                web.get("/MCWS/v1/{tail:.*}", self._handle),
                web.get("/libraryserver/lookup", self._handle_lookup),
            ]
        )
        return app

    async def _handle(self, request: web.Request) -> web.Response:
        path = request.match_info["tail"]
        self.requests.append((path, dict(request.query)))
        if path not in self.responses:
            return web.Response(
                text=NOT_FOUND, content_type="text/xml", status=500, charset="utf-8"
            )
        text, content_type, status = self.responses[path]
        return web.Response(text=text, content_type=content_type, status=status, charset="utf-8")

    async def _handle_lookup(self, request: web.Request) -> web.Response:
        self.requests.append(("lookup", dict(request.query)))
        assert self.lookup is not None
        text, content_type, status = self.lookup
        return web.Response(text=text, content_type=content_type, status=status, charset="utf-8")


@pytest.fixture
def fake() -> FakeMediaServer:
    """A canned-response MCWS server."""
    return FakeMediaServer()


@pytest.fixture
async def make_server(aiohttp_server, fake: FakeMediaServer) -> AsyncIterator[Callable[[], object]]:
    """Return a factory that starts the fake server and yields a MediaServer."""
    created: list[MediaServer] = []

    async def _make() -> MediaServer:
        server = await aiohttp_server(fake.app())
        ms = MediaServer(get_mcws_connection("localhost", server.port))
        created.append(ms)
        return ms

    yield _make
    for ms in created:
        await ms.close()
