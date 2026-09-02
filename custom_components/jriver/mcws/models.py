"""Data models for the JRiver Media Center MCWS interface.

Derived from the ``hamcws`` library (https://github.com/3ll3d00d/hamcws) v0.2.7,
Copyright (c) 3ll3d00d, MIT licensed. See ``__init__.py`` for the full notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from enum import Enum, IntEnum, StrEnum
import logging

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "AudioPath",
    "KeyCommand",
    "LibraryField",
    "MediaServerInfo",
    "MediaSubType",
    "MediaType",
    "PlayMode",
    "PlaybackInfo",
    "PlaybackState",
    "Playlist",
    "RepeatMode",
    "ServerAddress",
    "ShuffleMode",
    "ViewMode",
    "Zone",
]


class PlaybackState(Enum):
    """The playback state of a zone."""

    UNKNOWN = -1
    STOPPED = 0
    PAUSED = 1
    PLAYING = 2
    WAITING = 3


class MediaType(StrEnum):
    """A JRiver library ``Media Type``."""

    NOT_AVAILABLE = ""
    VIDEO = "Video"
    AUDIO = "Audio"
    DATA = "Data"
    IMAGE = "Image"
    TV = "TV"
    PLAYLIST = "Playlist"


class MediaSubType(StrEnum):
    """A JRiver library ``Media Sub Type``."""

    NOT_AVAILABLE = ""
    ADULT = "Adult"
    ANIMATION = "Animation"
    AUDIOBOOK = "Audiobook"
    BOOK = "Book"
    CONCERT = "Concert"
    EDUCATIONAL = "Educational"
    ENTERTAINMENT = "Entertainment"
    EXTRAS = "Extras"
    HOME_VIDEO = "Home Video"
    KARAOKE = "Karaoke"
    MOVIE = "Movie"
    MUSIC = "Music"
    MUSIC_VIDEO = "Music Video"
    OTHER = "Other"
    PHOTO = "Photo"
    PODCAST = "Podcast"
    RADIO = "Radio"
    RINGTONE = "Ringtone"
    SHORT = "Short"
    SINGLE = "Single"
    SPORTS = "Sports"
    STOCK = "Stock"
    SYSTEM = "System"
    TEST_CLIP = "Test Clip"
    TRAILER = "Trailer"
    TV_SHOW = "TV Show"
    WORKOUT = "Workout"


class KeyCommand(StrEnum):
    """A key that can be sent via ``Control/Key``."""

    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"
    ENTER = "Enter"
    HOME = "Home"
    END = "End"
    PAGE_UP = "Page Up"
    PAGE_DOWN = "Page Down"
    CTRL = "Ctrl"
    SHIFT = "Shift"
    ALT = "Alt"
    INSERT = "Insert"
    MENU = "Menu"
    DELETE = "Delete"
    PLUS = "+"
    MINUS = "-"
    BACKSPACE = "Backspace"
    ESCAPE = "Escape"
    APPS = "Apps"
    SPACE = "Space"
    PRINT_SCREEN = "Print Screen"
    TAB = "Tab"


class ViewMode(IntEnum):
    """UI mode, from https://wiki.jriver.com/index.php/Media_Center_Core_Commands."""

    UNKNOWN = -2000
    NO_UI = -1000
    STANDARD = 0
    MINI = 1
    DISPLAY = 2
    THEATER = 3
    COVER = 4
    COUNT = 5


class RepeatMode(StrEnum):
    """Repeat mode as accepted/reported by ``Playback/Repeat``."""

    UNKNOWN = "Unknown"
    OFF = "Off"
    PLAYLIST = "Playlist"
    TRACK = "Track"
    STOP = "Stop"


class ShuffleMode(StrEnum):
    """Shuffle mode as accepted/reported by ``Playback/Shuffle``."""

    UNKNOWN = "Unknown"
    OFF = "Off"
    ON = "On"
    RESHUFFLE = "Reshuffle"
    TOGGLE = "Toggle"


class PlayMode(StrEnum):
    """How files should be added to the playing now list."""

    ADD = "Add"
    NEXT_TO_PLAY = "NextToPlay"


def _as_int(value: str | int | None, default: int = 0) -> int:
    """Coerce a MCWS value to an int, falling back to ``default``."""
    if value is None or value == "":
        return default
    try:
        return int(str(value).strip())
    except ValueError:
        _LOGGER.debug("Unable to parse %r as int", value)
        return default


def _as_float(value: str | float | None, default: float = 0.0) -> float:
    """Coerce a MCWS value to a float, falling back to ``default``."""
    if value is None or value == "":
        return default
    try:
        return float(str(value).strip())
    except ValueError:
        _LOGGER.debug("Unable to parse %r as float", value)
        return default


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a MC version string into a 3 element tuple, padding as required."""
    tokens: list[int] = []
    for token in version.split(".")[:3]:
        try:
            tokens.append(int(token))
        except ValueError:
            _LOGGER.debug("Unparseable version token %r in %r", token, version)
            tokens.append(0)
    while len(tokens) < 3:
        tokens.append(0)
    return tokens[0], tokens[1], tokens[2]


class MediaServerInfo:
    """Information about a Media Center instance, from ``Alive``."""

    def __init__(self, resp_dict: dict[str, str | None]) -> None:
        """Populate from the parsed ``Alive`` response."""
        self.version: str = resp_dict.get("ProgramVersion") or "Unknown"
        self.name: str = resp_dict.get("FriendlyName") or "Unknown"
        self.platform: str = resp_dict.get("Platform") or "Unknown"
        self.access_key: str = resp_dict.get("AccessKey") or ""
        self.runtime_guid: str = resp_dict.get("RuntimeGUID") or ""
        self.product_version: str = resp_dict.get("ProductVersion") or ""
        self.library_version: int = _as_int(resp_dict.get("LibraryVersion"), -1)
        self.program_name: str = resp_dict.get("ProgramName") or ""
        self.updated_at: datetime.datetime = datetime.datetime.now(datetime.UTC)
        self.version_tuple: tuple[int, int, int] = parse_version(self.version)

    def __str__(self) -> str:
        """Render as ``name [version]``."""
        return f"{self.name} [{self.version}]"

    def __eq__(self, other: object) -> bool:
        """Compare on name and version only."""
        if isinstance(other, MediaServerInfo):
            return self.name == other.name and self.version == other.version
        return NotImplemented

    def __hash__(self) -> int:
        """Hash on name and version only."""
        return hash((self.name, self.version))

    @property
    def supports_audio_path_direct(self) -> bool:
        """Whether ``Playback/AudioPathDirect`` is available (MC 33.0.33+)."""
        return self.version_tuple >= (33, 0, 33)

    @property
    def supports_browse_rules(self) -> bool:
        """Whether ``Browse/Rules`` is available (MC 32.0.6+)."""
        return self.version_tuple >= (32, 0, 6)

    @property
    def is_windows(self) -> bool:
        """Whether the server runs on Windows."""
        return self.platform.lower().startswith("win")

    @property
    def is_linux(self) -> bool:
        """Whether the server runs on Linux."""
        return self.platform.lower().startswith("linux")

    @property
    def is_mac(self) -> bool:
        """Whether the server runs on macOS."""
        return self.platform.lower().startswith(("mac", "osx", "os x"))


class PlaybackInfo:
    """The state of playback in a zone, from ``Playback/Info``."""

    def __init__(
        self, resp_info: dict[str, str | None], extra_fields: list[str] | None = None
    ) -> None:
        """Populate from the parsed ``Playback/Info`` response."""
        extra_fields = extra_fields or []
        self.zone_id: int = _as_int(resp_info.get("ZoneID"), -1)
        self.zone_name: str = resp_info.get("ZoneName") or ""
        self.state: PlaybackState = _safe_enum(
            PlaybackState, _as_int(resp_info.get("State"), -1), PlaybackState.UNKNOWN
        )
        self.status: str = resp_info.get("Status") or ""
        self.file_key: int = _as_int(resp_info.get("FileKey"), -1)
        self.next_file_key: int = _as_int(resp_info.get("NextFileKey"), -1)
        self.position_ms: int = _as_int(resp_info.get("PositionMS"), 0)
        self.duration_ms: int = _as_int(resp_info.get("DurationMS"), 0)
        self.elapsed_time_display: str = resp_info.get("ElapsedTimeDisplay") or ""
        self.total_time_display: str = resp_info.get("TotalTimeDisplay") or ""
        self.playing_now_position: int = _as_int(resp_info.get("PlayingNowPosition"), -1)
        self.playing_now_tracks: int = _as_int(resp_info.get("PlayingNowTracks"), 0)
        self.playing_now_change_counter: int = _as_int(resp_info.get("PlayingNowChangeCounter"), 0)
        self.bitrate: int = _as_int(resp_info.get("Bitrate"), 0)
        self.bitdepth: int = _as_int(resp_info.get("Bitdepth"), 0)
        self.sample_rate: int = _as_int(resp_info.get("SampleRate"), 0)
        self.channels: int = _as_int(resp_info.get("Channels"), 0)
        self.chapter: int = _as_int(resp_info.get("Chapter"), 0)
        self.volume: float = _as_float(resp_info.get("Volume"), 0.0)
        self.volume_display: str = resp_info.get("VolumeDisplay") or ""
        self.muted: bool = self.volume_display == "Muted"
        self.image_url: str = resp_info.get("ImageURL") or ""
        self.name: str = resp_info.get("Name") or ""
        self.live_input: bool = self.name == "Ipc"
        self.linked_zones: list[int] = [
            zone_id
            for zone_id in (
                _as_int(token, -1)
                for token in (resp_info.get("LinkedZones") or "").split(",")
                if token.strip()
            )
            if zone_id != -1
        ]
        # music only
        self.artist: str = resp_info.get("Artist") or ""
        self.album: str = resp_info.get("Album") or ""
        self.album_artist: str = resp_info.get("Album Artist (auto)") or ""
        # TV only
        self.series: str = resp_info.get("Series") or ""
        self.season: str = resp_info.get("Season") or ""
        self.episode: str = resp_info.get("Episode") or ""
        # custom fields
        self.extra_fields: dict[str, str] = {f: (resp_info.get(f) or "") for f in extra_fields}
        self.media_type: MediaType = _safe_enum(
            MediaType, resp_info.get("Media Type"), MediaType.NOT_AVAILABLE
        )
        self.media_sub_type: MediaSubType = _safe_enum(
            MediaSubType, resp_info.get("Media Sub Type"), MediaSubType.NOT_AVAILABLE
        )
        # always defined, unlike hamcws where it was set conditionally
        self.playback_info: str = resp_info.get("Playback Info") or ""

    def as_dict(self) -> dict:
        """Convert the available info to a dict suitable for HA attributes."""
        return {
            "name": self.name,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "playback_state": self.state.name,
            "position_ms": self.position_ms,
            "duration_ms": self.duration_ms,
            "volume": self.volume,
            "muted": self.muted,
            "live_input": self.live_input,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "series": self.series,
            "season": self.season,
            "episode": self.episode,
            "media_type": self.media_type.name,
            "media_sub_type": self.media_sub_type.name,
            "elapsed_time_display": self.elapsed_time_display,
            "total_time_display": self.total_time_display,
            "volume_display": self.volume_display,
            "playing_now_position": self.playing_now_position,
            "playing_now_tracks": self.playing_now_tracks,
            "bitrate": self.bitrate,
            "bitdepth": self.bitdepth,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chapter": self.chapter,
            "linked_zones": self.linked_zones,
            **self.extra_fields,
        }

    def __str__(self) -> str:
        """Render a short summary."""
        val = f"[{self.zone_name} : {self.state.name}]"
        if self.file_key != -1:
            val = f"{val} {self.file_key} ({self.media_type.name} / {self.media_sub_type.name})"
        return val


def _safe_enum(enum_cls, value, fallback):
    """Convert to an enum member, logging and falling back on failure."""
    if value is None:
        return fallback
    try:
        return enum_cls(value)
    except ValueError:
        _LOGGER.debug("Unknown %s value %r", enum_cls.__name__, value)
        return fallback


class ServerAddress:
    """A server location, as resolved from an access key."""

    def __init__(self, content: dict[str, str | None]) -> None:
        """Populate from the parsed jriver.com lookup response."""
        self.key_id = content.get("keyid")
        self.ip = content.get("ip")
        self.port = _as_int(content.get("port"), -1)
        self.local_ip_list = [ip for ip in (content.get("localiplist") or "").split(",") if ip]
        self.remote_ip = content.get("ip")
        self.http_port = _as_int(content.get("port"), -1)
        self.https_port = _as_int(content.get("https_port"), -1)
        self.mac_address_list = [
            mac for mac in (content.get("macaddresslist") or "").split(",") if mac
        ]


class Zone:
    """A playback zone."""

    def __init__(
        self, content: dict[str, str | None], zone_index: int, active_zone_id: int
    ) -> None:
        """Populate zone ``zone_index`` from a ``Playback/Zones`` response."""
        self.index = zone_index
        self.id = _as_int(content.get(f"ZoneID{zone_index}"), -1)
        self.name = content.get(f"ZoneName{zone_index}") or ""
        self.guid = content.get(f"ZoneGUID{zone_index}") or ""
        self.is_dlna = content.get(f"ZoneDLNA{zone_index}", "0") == "1"
        self.active = self.id == active_zone_id

    def as_query_params(self) -> dict[str, str | int]:
        """Return the query params that address this zone (always by ID)."""
        return {"Zone": self.id, "ZoneType": "ID"}

    def __str__(self) -> str:
        """Return the zone name."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Compare on id, name and index."""
        if isinstance(other, Zone):
            return self.id == other.id and self.name == other.name and self.index == other.index
        return NotImplemented

    def __hash__(self) -> int:
        """Hash on id, name and index."""
        return hash((self.id, self.name, self.index))


@dataclass
class LibraryField:
    """A field defined in the MC library."""

    name: str
    data_type: str
    edit_type: str
    display_name: str


@dataclass
class AudioPath:
    """The DSP audio path applied in a zone."""

    is_direct: bool = False
    paths: list[str] = field(default_factory=list)


@dataclass
class Playlist:
    """A stored playlist."""

    id: str
    name: str
    path: str = ""
    type: str = ""
