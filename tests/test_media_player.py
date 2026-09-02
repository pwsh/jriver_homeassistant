"""Test the JRiver media player."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import (
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_TURN_OFF_BEHAVIOUR,
    DOMAIN,
    SERVICE_ADJUST_VOLUME,
    SERVICE_PLAY_SEARCH,
    SERVICE_SEEK_RELATIVE,
)
from custom_components.jriver.mcws import MCC, PlaybackState, RepeatMode, ShuffleMode
from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_ENQUEUE,
    ATTR_MEDIA_REPEAT,
    ATTR_MEDIA_SHUFFLE,
    DOMAIN as MP_DOMAIN,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOUND_MODE,
    SERVICE_SELECT_SOURCE,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.components.media_player.const import (
    ATTR_GROUP_MEMBERS,
    ATTR_INPUT_SOURCE,
    ATTR_SOUND_MODE,
    SERVICE_JOIN,
    SERVICE_UNJOIN,
)
from homeassistant.const import (
    SERVICE_MEDIA_PLAY,
    SERVICE_REPEAT_SET,
    SERVICE_SHUFFLE_SET,
    SERVICE_TURN_OFF,
    SERVICE_VOLUME_SET,
)
from homeassistant.core import HomeAssistant

from .conftest import (
    FakeMediaServer,
    build_entry,
    make_playback_info,
    setup_integration,
)

ENTITY = "media_player.phosphorus"
ZONE_ENTITY = "media_player.phosphorus_player"
OFFICE_ENTITY = "media_player.phosphorus_office"


async def _call(hass: HomeAssistant, domain: str, service: str, **data) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


@pytest.fixture
async def per_zone(hass: HomeAssistant, mock_media_server: FakeMediaServer):
    """Set up the integration with a device per zone."""
    entry = build_entry(
        options={CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: ["Player", "Office"]}
    )
    await setup_integration(hass, entry)
    return entry


@pytest.mark.parametrize(
    ("playback_state", "expected"),
    [
        (PlaybackState.PLAYING, MediaPlayerState.PLAYING),
        (PlaybackState.PAUSED, MediaPlayerState.PAUSED),
        (PlaybackState.STOPPED, MediaPlayerState.IDLE),
        (PlaybackState.WAITING, MediaPlayerState.IDLE),
    ],
)
async def test_state_mapping(
    hass: HomeAssistant,
    mock_media_server: FakeMediaServer,
    playback_state: PlaybackState,
    expected: MediaPlayerState,
) -> None:
    """Playback states map onto media player states."""
    mock_media_server.playback[10] = make_playback_info(
        mock_media_server.zones[0], state=playback_state
    )
    await setup_integration(hass, build_entry())
    assert hass.states.get(ENTITY).state == expected


async def test_media_attributes(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Track metadata and the extra attributes are exposed."""
    state = hass.states.get(ENTITY)
    assert state.attributes["media_title"] == "Everybody Hertz"
    assert state.attributes["media_artist"] == "Air"
    assert state.attributes["media_album_name"] == "10 000 Hz Legend"
    assert state.attributes["media_duration"] == 300
    assert state.attributes["media_content_id"] == "100"
    assert state.attributes["zone_name"] == "Player"
    assert state.attributes["audio_direct"] is True
    assert state.attributes["next_file_key"] == 101
    assert state.attributes["bitrate"] == 1411


async def test_no_content_id_when_nothing_loaded(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """A file key of -1 is reported as no content."""
    mock_media_server.active_zone_id = 20
    mock_media_server.zones[0].active = False
    mock_media_server.zones[1].active = True
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).attributes.get("media_content_id") is None


async def test_features_single_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Single device mode offers source selection but not grouping."""
    features = hass.states.get(ENTITY).attributes["supported_features"]
    assert features & MediaPlayerEntityFeature.SELECT_SOURCE
    assert not features & MediaPlayerEntityFeature.GROUPING
    assert not features & MediaPlayerEntityFeature.SELECT_SOUND_MODE
    assert hass.states.get(ENTITY).attributes["source_list"] == ["Player", "Office"]
    assert hass.states.get(ENTITY).attributes["source"] == "Player"


async def test_features_per_zone(hass: HomeAssistant, per_zone) -> None:
    """Per zone mode offers grouping but not source selection."""
    features = hass.states.get(ZONE_ENTITY).attributes["supported_features"]
    assert features & MediaPlayerEntityFeature.GROUPING
    assert not features & MediaPlayerEntityFeature.SELECT_SOURCE


async def test_sound_mode_when_presets_configured(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """DSP presets become sound modes."""
    entry = build_entry(options={CONF_DSP_PRESETS: ["Night", "Movie"]})
    await setup_integration(hass, entry)
    state = hass.states.get(ENTITY)
    assert state.attributes["supported_features"] & (MediaPlayerEntityFeature.SELECT_SOUND_MODE)
    assert state.attributes["sound_mode_list"] == ["Night", "Movie"]

    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_SELECT_SOUND_MODE,
        entity_id=ENTITY,
        **{ATTR_SOUND_MODE: "Night"},
    )
    assert mock_media_server.calls_to("load_dsp_preset")[0][0][0] == "Night"


async def test_select_source(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Selecting a source switches the active zone."""
    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        entity_id=ENTITY,
        **{ATTR_INPUT_SOURCE: "Office"},
    )
    assert mock_media_server.calls_to("set_active_zone")[0][0][0] == "Office"


async def test_repeat_and_shuffle(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Repeat and shuffle round trip through the client."""
    assert hass.states.get(ENTITY).attributes["repeat"] == "all"
    assert hass.states.get(ENTITY).attributes["shuffle"] is False

    await _call(hass, MP_DOMAIN, SERVICE_REPEAT_SET, entity_id=ENTITY, **{ATTR_MEDIA_REPEAT: "one"})
    assert mock_media_server.repeat_mode is RepeatMode.TRACK

    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_SHUFFLE_SET,
        entity_id=ENTITY,
        **{ATTR_MEDIA_SHUFFLE: True},
    )
    assert mock_media_server.shuffle_mode is ShuffleMode.ON


async def test_play_is_a_noop_when_playing(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Play does not toggle a playing zone into pause."""
    await _call(hass, MP_DOMAIN, SERVICE_MEDIA_PLAY, entity_id=ENTITY)
    assert not mock_media_server.called("play_pause")
    assert not mock_media_server.called("play")


async def test_play_when_paused(hass: HomeAssistant, mock_media_server: FakeMediaServer) -> None:
    """Play resumes a paused zone with the toggle, which is reliable."""
    mock_media_server.playback[10] = make_playback_info(
        mock_media_server.zones[0], state=PlaybackState.PAUSED
    )
    await setup_integration(hass, build_entry())
    await _call(hass, MP_DOMAIN, SERVICE_MEDIA_PLAY, entity_id=ENTITY)
    assert mock_media_server.called("play_pause")
    assert not mock_media_server.called("play")


@pytest.mark.parametrize("state", [PlaybackState.STOPPED, PlaybackState.WAITING])
async def test_play_when_not_playing(
    hass: HomeAssistant, mock_media_server: FakeMediaServer, state: PlaybackState
) -> None:
    """Play starts a stopped or waiting zone with Playback/Play."""
    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], state=state)
    await setup_integration(hass, build_entry())
    await _call(hass, MP_DOMAIN, SERVICE_MEDIA_PLAY, entity_id=ENTITY)
    assert mock_media_server.called("play")
    assert not mock_media_server.called("play_pause")


@pytest.mark.parametrize(
    ("content_type", "content_id", "expected_call", "expected_first_arg"),
    [
        ("music", "K|123", "play_item", "123"),
        ("music", "N|55|Audio > Album", "play_browse_files", 55),
        ("query", "[Artist]=[Air]", "play_search", "[Artist]=[Air]"),
        ("playlist", "Alarms\\Wakeup", "play_playlist", "Alarms\\Wakeup"),
        ("url", "http://host/file.flac", "play_file", "http://host/file.flac"),
    ],
)
async def test_play_media_dispatch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_media_server: FakeMediaServer,
    content_type: str,
    content_id: str,
    expected_call: str,
    expected_first_arg,
) -> None:
    """play_media routes each content type to the right client call."""
    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        entity_id=ENTITY,
        **{ATTR_MEDIA_CONTENT_TYPE: content_type, ATTR_MEDIA_CONTENT_ID: content_id},
    )
    assert mock_media_server.called("clear_playlist")
    args, _ = mock_media_server.calls_to(expected_call)[0]
    assert args[0] == expected_first_arg


@pytest.mark.parametrize(
    ("enqueue", "expected_mode", "clears"),
    [("add", "Add", False), ("next", "NextToPlay", False), ("replace", None, True)],
)
async def test_play_media_enqueue(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_media_server: FakeMediaServer,
    enqueue: str,
    expected_mode: str | None,
    clears: bool,
) -> None:
    """The enqueue option maps onto the MCWS play mode."""
    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        entity_id=ENTITY,
        **{
            ATTR_MEDIA_CONTENT_TYPE: "music",
            ATTR_MEDIA_CONTENT_ID: "K|123",
            ATTR_MEDIA_ENQUEUE: enqueue,
        },
    )
    _, kwargs = mock_media_server.calls_to("play_item")[0]
    assert kwargs["play_mode"] == expected_mode
    assert mock_media_server.called("clear_playlist") is clears


async def test_play_media_media_source(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """A media source id is resolved before being played."""
    with patch(
        "homeassistant.components.media_source.async_resolve_media",
    ) as resolve:
        resolve.return_value.url = "/local/test.mp3"
        await _call(
            hass,
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            entity_id=ENTITY,
            **{
                ATTR_MEDIA_CONTENT_TYPE: "music",
                ATTR_MEDIA_CONTENT_ID: "media-source://media_source/local/test.mp3",
            },
        )
    assert resolve.called
    args, _ = mock_media_server.calls_to("play_file")[0]
    assert "/local/test.mp3" in args[0]


async def test_seek_relative(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Relative seek is applied to the current position and clamped."""
    await _call(hass, DOMAIN, SERVICE_SEEK_RELATIVE, entity_id=ENTITY, seek_duration=5)
    assert mock_media_server.calls_to("media_seek")[0][0][0] == 6000

    await _call(hass, DOMAIN, SERVICE_SEEK_RELATIVE, entity_id=ENTITY, seek_duration=-30)
    assert mock_media_server.calls_to("media_seek")[1][0][0] == 0

    await _call(hass, DOMAIN, SERVICE_SEEK_RELATIVE, entity_id=ENTITY, seek_duration=9999)
    assert mock_media_server.calls_to("media_seek")[2][0][0] == 300000


@pytest.mark.parametrize("delta", [5, -5])
async def test_adjust_volume(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_media_server: FakeMediaServer,
    delta: int,
) -> None:
    """A signed volume delta is sent as a single relative call."""
    await _call(hass, DOMAIN, SERVICE_ADJUST_VOLUME, entity_id=ENTITY, delta=delta)
    args, _ = mock_media_server.calls_to("set_volume_relative")[0]
    assert args[0] == pytest.approx(delta / 100)


async def test_play_search_service(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """play_search honours the play mode."""
    await _call(
        hass,
        DOMAIN,
        SERVICE_PLAY_SEARCH,
        entity_id=ENTITY,
        query="[Artist]=[Air]",
        play_mode="add",
    )
    _, kwargs = mock_media_server.calls_to("play_search")[0]
    assert kwargs["play_mode"] == "Add"
    assert not mock_media_server.called("clear_playlist")


async def test_volume_set(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Volume set passes through."""
    await _call(hass, MP_DOMAIN, SERVICE_VOLUME_SET, entity_id=ENTITY, volume_level=0.25)
    assert mock_media_server.calls_to("set_volume_level")[0][0][0] == 0.25


async def test_grouping(hass: HomeAssistant, per_zone, mock_media_server) -> None:
    """Joining and unjoining maps onto zone linking."""
    await _call(
        hass,
        MP_DOMAIN,
        SERVICE_JOIN,
        entity_id=ZONE_ENTITY,
        **{ATTR_GROUP_MEMBERS: [OFFICE_ENTITY]},
    )
    args, _ = mock_media_server.calls_to("link_zones")[0]
    assert args[0].id == 10
    assert args[1].id == 20

    await _call(hass, MP_DOMAIN, SERVICE_UNJOIN, entity_id=ZONE_ENTITY)
    assert mock_media_server.calls_to("unlink_zone")[0][0][0].id == 10


async def test_group_members_from_linked_zones(
    hass: HomeAssistant, per_zone, mock_media_server: FakeMediaServer
) -> None:
    """Linked zones are reported as group members."""
    mock_media_server.playback[10] = make_playback_info(
        mock_media_server.zones[0], LinkedZones="Player;Office"
    )
    await per_zone.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ZONE_ENTITY).attributes[ATTR_GROUP_MEMBERS] == [
        ZONE_ENTITY,
        OFFICE_ENTITY,
    ]


async def test_zone_name_falls_back_to_the_zone(
    hass: HomeAssistant, per_zone, mock_media_server: FakeMediaServer
) -> None:
    """Playback/Info omits ZoneName for the local zone so the zone is used instead."""
    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], ZoneName="")
    await per_zone.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ZONE_ENTITY).attributes["zone_name"] == "Player"


async def test_idle_zone_with_no_file_reports_no_media(
    hass: HomeAssistant, per_zone, mock_media_server: FakeMediaServer
) -> None:
    """A zone with no file reports a stale DurationMS which must not be surfaced."""
    state = hass.states.get(OFFICE_ENTITY)
    assert "media_duration" not in state.attributes
    assert "media_position" not in state.attributes
    assert "media_title" not in state.attributes
    assert "media_content_type" not in state.attributes
    assert "entity_picture" not in state.attributes


async def test_stopped_zone_with_a_file_still_reports_media(
    hass: HomeAssistant, per_zone, mock_media_server: FakeMediaServer
) -> None:
    """A stopped zone that still holds a file key keeps its metadata."""
    mock_media_server.playback[20] = make_playback_info(
        mock_media_server.zones[1], state=PlaybackState.STOPPED, file_key=960
    )
    await per_zone.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(OFFICE_ENTITY)
    assert state.attributes["media_title"] == "Everybody Hertz"
    assert state.attributes["media_duration"] == 300


async def test_turn_off_stops_only_by_default(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The default turn off behaviour never closes Media Center."""
    await _call(hass, MP_DOMAIN, SERVICE_TURN_OFF, entity_id=ENTITY)
    assert mock_media_server.called("stop_all")
    assert not mock_media_server.called("send_mcc")


async def test_turn_off_can_close_program(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Closing Media Center is opt in."""
    entry = build_entry(options={CONF_TURN_OFF_BEHAVIOUR: "close_program"})
    await setup_integration(hass, entry)
    await _call(hass, MP_DOMAIN, SERVICE_TURN_OFF, entity_id=ENTITY)
    assert mock_media_server.calls_to("send_mcc")[0][0][0] is MCC.CLOSE_PROGRAM
