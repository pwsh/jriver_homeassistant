"""Tests for the MCWS data models."""

from __future__ import annotations

import datetime

import pytest

from custom_components.jriver.mcws import (
    MediaServerInfo,
    MediaSubType,
    MediaType,
    PlaybackInfo,
    PlaybackState,
    Zone,
)
from custom_components.jriver.mcws.mcc import MCC
from custom_components.jriver.mcws.models import parse_version

ALIVE = {
    "RuntimeGUID": "{123456}",
    "LibraryVersion": "24",
    "ProgramName": "JRiver Media Center",
    "ProgramVersion": "31.0.83",
    "FriendlyName": "MyServer",
    "ProductVersion": "31 Linux",
    "Platform": "Linux",
    "AccessKey": "abc123",
}


def test_media_server_info() -> None:
    """All Alive fields are parsed."""
    info = MediaServerInfo(ALIVE)
    assert info.name == "MyServer"
    assert info.version == "31.0.83"
    assert info.platform == "Linux"
    assert info.access_key == "abc123"
    assert info.runtime_guid == "{123456}"
    assert info.product_version == "31 Linux"
    assert info.library_version == 24
    assert info.program_name == "JRiver Media Center"
    assert info.version_tuple == (31, 0, 83)
    assert str(info) == "MyServer [31.0.83]"
    assert info == MediaServerInfo(ALIVE)
    assert info != "nope"
    assert hash(info) == hash(MediaServerInfo(ALIVE))


def test_media_server_info_updated_at_is_tz_aware() -> None:
    """updated_at is timezone aware (utcnow is deprecated)."""
    info = MediaServerInfo(ALIVE)
    assert info.updated_at.tzinfo is not None
    assert info.updated_at <= datetime.datetime.now(datetime.UTC)


def test_media_server_info_empty() -> None:
    """Missing fields fall back to defaults."""
    info = MediaServerInfo({})
    assert info.name == "Unknown"
    assert info.version_tuple == (0, 0, 0)
    assert info.library_version == -1


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("33.0", (33, 0, 0)),
        ("33", (33, 0, 0)),
        ("33.0.33.4", (33, 0, 33)),
        ("nope", (0, 0, 0)),
        ("", (0, 0, 0)),
    ],
)
def test_parse_version(version: str, expected: tuple[int, int, int]) -> None:
    """Version strings are padded to three elements."""
    assert parse_version(version) == expected


def test_supports_flags_short_version() -> None:
    """A short version does not raise IndexError."""
    info = MediaServerInfo({"ProgramVersion": "33.0"})
    assert info.supports_audio_path_direct is False
    assert info.supports_browse_rules is True
    assert MediaServerInfo({"ProgramVersion": "33.0.33"}).supports_audio_path_direct
    assert MediaServerInfo({"ProgramVersion": "34.0.0"}).supports_audio_path_direct
    assert not MediaServerInfo({"ProgramVersion": "32.0.5"}).supports_browse_rules
    assert MediaServerInfo({"ProgramVersion": "32.0.6"}).supports_browse_rules


@pytest.mark.parametrize(
    ("platform", "attr"),
    [
        ("Windows", "is_windows"),
        ("Linux", "is_linux"),
        ("Mac", "is_mac"),
    ],
)
def test_platform_flags(platform: str, attr: str) -> None:
    """The platform flags reflect the reported platform."""
    info = MediaServerInfo({"Platform": platform})
    assert getattr(info, attr) is True


def test_playback_info_defaults() -> None:
    """An empty response yields sensible defaults."""
    info = PlaybackInfo({})
    assert info.zone_id == -1
    assert info.state is PlaybackState.UNKNOWN
    assert info.playback_info == ""
    assert info.linked_zones == []
    assert info.media_type is MediaType.NOT_AVAILABLE
    assert info.media_sub_type is MediaSubType.NOT_AVAILABLE
    assert str(info) == "[ : UNKNOWN]"


def test_playback_info_parsing() -> None:
    """All the extended fields are parsed."""
    info = PlaybackInfo(
        {
            "ZoneID": "10081",
            "ZoneName": "Player",
            "State": "2",
            "Status": "Playing",
            "FileKey": "123",
            "NextFileKey": "124",
            "PositionMS": "500",
            "DurationMS": "1000",
            "ElapsedTimeDisplay": "0:00",
            "TotalTimeDisplay": "Live",
            "PlayingNowPosition": "1",
            "PlayingNowTracks": "5",
            "PlayingNowChangeCounter": "2",
            "Bitrate": "1752",
            "Bitdepth": "24",
            "SampleRate": "44100",
            "Channels": "2",
            "Chapter": "3",
            "Volume": "0.45",
            "VolumeDisplay": "45% (-27.5 dB)",
            "ImageURL": "MCWS/v1/File/GetImage?File=1",
            "Name": "A Track",
            "LinkedZones": "10074,10087,",
            "Media Type": "Audio",
            "Media Sub Type": "Music",
            "Artist": "An Artist",
            "Album": "An Album",
            "Album Artist (auto)": "An Album Artist",
            "Series": "S",
            "Season": "1",
            "Episode": "2",
            "Playback Info": "raw",
            "Rating": "5",
        },
        ["Rating"],
    )
    assert info.state is PlaybackState.PLAYING
    assert info.status == "Playing"
    assert info.next_file_key == 124
    assert info.linked_zones == [10074, 10087]
    assert info.bitrate == 1752
    assert info.bitdepth == 24
    assert info.sample_rate == 44100
    assert info.channels == 2
    assert info.chapter == 3
    assert info.playing_now_position == 1
    assert info.playing_now_tracks == 5
    assert info.playing_now_change_counter == 2
    assert info.playback_info == "raw"
    assert info.media_type is MediaType.AUDIO
    assert info.media_sub_type is MediaSubType.MUSIC
    assert info.extra_fields == {"Rating": "5"}
    assert not info.muted
    assert str(info) == "[Player : PLAYING] 123 (AUDIO / MUSIC)"

    as_dict = info.as_dict()
    assert as_dict["zone_id"] == 10081
    assert as_dict["playback_state"] == "PLAYING"
    assert as_dict["media_sub_type"] == "MUSIC"
    assert as_dict["linked_zones"] == [10074, 10087]
    assert as_dict["Rating"] == "5"


def test_playback_info_muted_and_live() -> None:
    """Muted and live input derive from other fields."""
    info = PlaybackInfo({"VolumeDisplay": "Muted", "Name": "Ipc"})
    assert info.muted is True
    assert info.live_input is True


def test_playback_info_unknown_enum_values() -> None:
    """Unknown enum values fall back rather than raising."""
    info = PlaybackInfo({"Media Type": "Hologram", "Media Sub Type": "Nope"})
    assert info.media_type is MediaType.NOT_AVAILABLE
    assert info.media_sub_type is MediaSubType.NOT_AVAILABLE


def test_playback_info_garbage_numbers() -> None:
    """Non numeric values fall back to defaults."""
    info = PlaybackInfo({"PositionMS": "x", "Volume": "y", "State": "z"})
    assert info.position_ms == 0
    assert info.volume == 0.0
    assert info.state is PlaybackState.UNKNOWN


def test_zone_addressing() -> None:
    """Zones are always addressed by ID."""
    resp = {
        "ZoneID0": "10081",
        "ZoneName0": "Player",
        "ZoneGUID0": "{x}",
        "ZoneDLNA0": "0",
    }
    zone = Zone(resp, 0, 10081)
    assert zone.id == 10081
    assert zone.name == "Player"
    assert zone.index == 0
    assert not zone.is_dlna
    assert zone.active
    assert zone.as_query_params() == {"Zone": 10081, "ZoneType": "ID"}
    assert str(zone) == "Player"
    assert zone == Zone(resp, 0, 10081)
    assert zone != Zone({"ZoneID0": "999"}, 0, 1)
    assert zone != "nope"
    assert hash(zone) == hash(Zone(resp, 0, 10081))


def test_zone_missing_fields() -> None:
    """A zone with no name still parses."""
    zone = Zone({"ZoneID0": "10081"}, 0, 1)
    assert zone.name == ""
    assert zone.id == 10081
    assert not zone.active


def test_mcc_constants() -> None:
    """A few MCC ids are as documented."""
    assert MCC.PLAY_PAUSE == 10000
    assert MCC.SHUFFLE == 10005
    assert MCC.STOP_AFTER_CURRENT_FILE == 10036
    assert MCC.STOP_AFTER_DELAY == 10067
    assert MCC.SET_MODE == 22009
