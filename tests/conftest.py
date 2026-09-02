"""Common fixtures for the JRiver Media Center tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_EXTRA_FIELDS,
    CONF_POLL_INTERVAL,
    CONF_TURN_OFF_BEHAVIOUR,
    CONF_USE_WOL,
    DOMAIN,
    TurnOffBehaviour,
)
from custom_components.jriver.mcws import (
    AudioPath,
    BrowsePath,
    LibraryField,
    MediaServerInfo,
    PlaybackInfo,
    PlaybackState,
    RepeatMode,
    ShuffleMode,
    ViewMode,
    Zone,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

ACCESS_KEY = "abcdef"
DEFAULT_VERSION = "33.0.40"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable the custom integration for every test."""
    return


def make_zone(index: int, zone_id: int, name: str, active_id: int) -> Zone:
    """Build a Zone the way the client would."""
    return Zone(
        {
            f"ZoneID{index}": str(zone_id),
            f"ZoneName{index}": name,
            f"ZoneGUID{index}": f"guid-{zone_id}",
            f"ZoneDLNA{index}": "0",
        },
        index,
        active_id,
    )


def make_playback_info(
    zone: Zone,
    state: PlaybackState = PlaybackState.PLAYING,
    file_key: int = 100,
    change_counter: int = 1,
    extra_fields: list[str] | None = None,
    **overrides: Any,
) -> PlaybackInfo:
    """Build a PlaybackInfo the way the client would."""
    payload: dict[str, str | None] = {
        "ZoneID": str(zone.id),
        "ZoneName": zone.name,
        "State": str(state.value),
        "FileKey": str(file_key),
        "NextFileKey": "101",
        "PositionMS": "1000",
        "DurationMS": "300000",
        "PlayingNowPosition": "0",
        "PlayingNowTracks": "3",
        "PlayingNowChangeCounter": str(change_counter),
        "Volume": "0.5",
        "VolumeDisplay": "50%",
        "ImageURL": "MCWS/v1/File/GetImage?File=100&Token=t",
        "Name": "Everybody Hertz",
        "Artist": "Air",
        "Album": "10 000 Hz Legend",
        "Media Type": "Audio",
        "Media Sub Type": "Music",
        "Bitrate": "1411",
        "SampleRate": "44100",
        "Channels": "2",
        "LinkedZones": "",
    }
    payload.update({k: str(v) for k, v in overrides.items()})
    return PlaybackInfo(payload, extra_fields or [])


class FakeMediaServer:
    """An in-memory stand in for the MCWS client."""

    def __init__(self, version: str = DEFAULT_VERSION) -> None:
        """Initialise with two zones, one active and playing."""
        self.media_server_info = MediaServerInfo(
            {
                "ProgramVersion": version,
                "FriendlyName": "Phosphorus",
                "Platform": "Windows",
                "AccessKey": ACCESS_KEY,
                "LibraryVersion": "24",
                "ProductVersion": "Media Center 33",
            }
        )
        self.host = "1.1.1.1"
        self.port = 52199
        self.active_zone_id = 10
        self.zones = [
            make_zone(0, 10, "Player", self.active_zone_id),
            make_zone(1, 20, "Office", self.active_zone_id),
        ]
        self.playback: dict[int, PlaybackInfo] = {
            10: make_playback_info(self.zones[0]),
            20: make_playback_info(self.zones[1], state=PlaybackState.STOPPED, file_key=-1),
        }
        self.view_mode = ViewMode.STANDARD
        self.audio_paths = {
            10: AudioPath(is_direct=True, paths=[]),
            20: AudioPath(is_direct=False, paths=["Convert 2 to 2 channels"]),
        }
        self.playlists = {
            10: [
                {"Key": "100", "Name": "Everybody Hertz", "Artist": "Air"},
                {"Key": "101", "Name": "Radian", "Artist": "Air"},
                {"Key": "102", "Name": "Lucky and Unhappy", "Artist": "Air"},
            ],
            20: [],
        }
        self.repeat_mode = RepeatMode.PLAYLIST
        self.shuffle_mode = ShuffleMode.OFF
        self.library_fields = [
            LibraryField("Genre", "String", "Standard", "Genre"),
            LibraryField("Track #", "Integer", "Standard", "Track #"),
        ]
        self.browse_rules: list[Any] = []
        self.browse_paths = [BrowsePath("Audio")]
        self.browse_nodes: dict[int, dict[str, str | None]] = {
            -1: {"Audio": "1", "Video": "2"},
            1: {"Album": "3"},
            3: {},
        }
        self.browse_file_lists: dict[int, list[dict]] = {
            3: [
                {
                    "Key": "100",
                    "Name": "Radian",
                    "Media Type": "Audio",
                    "Media Sub Type": "Music",
                    "Track #": "2",
                }
            ]
        }
        self.calls: list[tuple[str, tuple, dict]] = []
        self.fail: dict[str, BaseException] = {}
        self.closed = False

    # -- helpers -----------------------------------------------------

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))
        if name in self.fail:
            raise self.fail[name]

    def calls_to(self, name: str) -> list[tuple[tuple, dict]]:
        """Return the arguments of every call made to the given method."""
        return [(args, kwargs) for called, args, kwargs in self.calls if called == name]

    def called(self, name: str) -> bool:
        """Return True if the named method was called."""
        return any(called == name for called, _, _ in self.calls)

    def _zone_id(self, zone: Zone | str | None) -> int:
        if zone is None:
            return self.active_zone_id
        if isinstance(zone, Zone):
            return zone.id
        match = next((z for z in self.zones if z.name == zone), None)
        return match.id if match else self.active_zone_id

    # -- client surface ----------------------------------------------

    async def alive(self) -> MediaServerInfo:
        """Return the server info."""
        self._record("alive")
        return self.media_server_info

    async def get_auth_token(self) -> str:
        """Return a token."""
        self._record("get_auth_token")
        return "token"

    async def get_zones(self) -> list[Zone]:
        """Return the zones."""
        self._record("get_zones")
        return self.zones

    async def get_view_mode(self) -> ViewMode:
        """Return the UI mode."""
        self._record("get_view_mode")
        return self.view_mode

    async def get_library_fields(self) -> list[LibraryField]:
        """Return the library fields."""
        self._record("get_library_fields")
        return self.library_fields

    async def get_playback_info(
        self, zone: Zone | str | None = None, extra_fields: list[str] | None = None
    ) -> PlaybackInfo:
        """Return the playback info for a zone."""
        self._record("get_playback_info", zone, extra_fields=extra_fields)
        return self.playback[self._zone_id(zone)]

    async def get_audio_path(self, zone: Zone | str | None = None) -> AudioPath:
        """Return the audio path for a zone."""
        self._record("get_audio_path", zone)
        return self.audio_paths[self._zone_id(zone)]

    async def get_current_playlist(
        self, fields: list[str] | None = None, zone: Zone | str | None = None
    ) -> list[dict]:
        """Return the playing now list for a zone."""
        self._record("get_current_playlist", fields=fields, zone=zone)
        return self.playlists[self._zone_id(zone)]

    async def get_repeat(self, zone: Zone | str | None = None) -> RepeatMode:
        """Return the repeat mode."""
        self._record("get_repeat", zone)
        return self.repeat_mode

    async def set_repeat(self, mode: RepeatMode, zone: Zone | str | None = None) -> bool:
        """Set the repeat mode."""
        self._record("set_repeat", mode, zone)
        self.repeat_mode = mode
        return True

    async def get_shuffle(self, zone: Zone | str | None = None) -> ShuffleMode:
        """Return the shuffle mode."""
        self._record("get_shuffle", zone)
        return self.shuffle_mode

    async def set_shuffle(self, shuffle: bool, zone: Zone | str | None = None) -> bool:
        """Set the shuffle mode."""
        self._record("set_shuffle", shuffle, zone)
        self.shuffle_mode = ShuffleMode.ON if shuffle else ShuffleMode.OFF
        return True

    async def get_browse_rules(self) -> list[Any]:
        """Return the browse rules."""
        self._record("get_browse_rules")
        return self.browse_rules

    async def browse_children(self, base_id: int = -1) -> dict[str, str | None]:
        """Return the child nodes of a browse node."""
        self._record("browse_children", base_id)
        return self.browse_nodes.get(base_id, {})

    async def browse_files(self, base_id: int = -1, fields: list[str] | None = None) -> list[dict]:
        """Return the files under a browse node."""
        self._record("browse_files", base_id, fields=fields)
        return self.browse_file_lists.get(base_id, [])

    async def get_browse_thumbnail_url(self, base_id: int = -1) -> str:
        """Return a thumbnail URL for a browse node."""
        self._record("get_browse_thumbnail_url", base_id)
        return f"http://thumb/{base_id}"

    async def get_file_image_url(self, file_key: int, **kwargs: Any) -> str:
        """Return an image URL for a file."""
        self._record("get_file_image_url", file_key)
        return f"http://image/{file_key}"

    def make_url(self, path: str) -> str:
        """Build an absolute URL."""
        return f"http://{self.host}:{self.port}/{path}"

    async def close(self) -> None:
        """Close the connection."""
        self.closed = True

    def __getattr__(self, name: str):
        """Record any other client call and return True."""
        if name.startswith("_"):
            raise AttributeError(name)

        async def _call(*args: Any, **kwargs: Any) -> bool:
            self._record(name, *args, **kwargs)
            return True

        return _call


@pytest.fixture
def fake_server() -> FakeMediaServer:
    """Return an in-memory media server."""
    return FakeMediaServer()


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Stop the integration from actually setting up."""
    with patch("custom_components.jriver.async_setup_entry", return_value=True) as mocked:
        yield mocked


@pytest.fixture
def mock_media_server(fake_server: FakeMediaServer) -> Generator[FakeMediaServer]:
    """Replace the client built during setup with the fake."""
    with patch("custom_components.jriver._build_media_server", return_value=fake_server):
        yield fake_server


def build_entry(**kwargs: Any) -> MockConfigEntry:
    """Build a version 2 config entry."""
    options = {
        CONF_BROWSE_PATHS: [],
        CONF_DEVICE_PER_ZONE: False,
        CONF_DEVICE_ZONES: [],
        CONF_EXTRA_FIELDS: [],
        CONF_USE_WOL: True,
        CONF_POLL_INTERVAL: 2,
        CONF_TURN_OFF_BEHAVIOUR: TurnOffBehaviour.STOP.value,
        CONF_DSP_PRESETS: [],
    }
    options.update(kwargs.pop("options", {}))
    data = {
        CONF_API_KEY: ACCESS_KEY,
        CONF_NAME: "Phosphorus",
        CONF_HOST: "1.1.1.1",
        CONF_PORT: 52199,
        CONF_MAC: ["aa:bb:cc:dd:ee:ff"],
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_SSL: False,
        CONF_TIMEOUT: 10,
    }
    data.update(kwargs.pop("data", {}))
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCESS_KEY,
        title="Phosphorus",
        data=data,
        options=options,
        version=kwargs.pop("version", 2),
        **kwargs,
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a version 2 config entry."""
    return build_entry()


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    """Add and set up a config entry."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_media_server
) -> MockConfigEntry:
    """Set up the integration with a fake media server."""
    return await setup_integration(hass, mock_config_entry)
