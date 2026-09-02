"""Test the JRiver coordinator."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import CONF_DEVICE_ZONES
from custom_components.jriver.mcws import (
    CannotConnectError,
    PlaybackState,
    RepeatMode,
    UnsupportedRequestError,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .conftest import FakeMediaServer, build_entry, make_playback_info, setup_integration


async def _refresh(entry: MockConfigEntry) -> None:
    await entry.runtime_data.coordinator.async_refresh()


async def test_first_tick_populates_everything(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The first tick fetches the cheap and the expensive tier."""
    data = init_integration.runtime_data.coordinator.data
    assert data.server_info.name == "Phosphorus"
    assert [z.id for z in data.zones] == [10, 20]
    assert data.active_zone_id == 10
    assert set(data.playback_info_by_zone_id) == {10, 20}
    assert data.audio_path(10).is_direct is True
    assert len(data.playlist(10)) == 3
    assert data.repeat(10) is RepeatMode.PLAYLIST


async def test_alive_is_not_called_every_tick(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Alive is only refreshed occasionally."""
    assert len(mock_media_server.calls_to("alive")) == 1
    await _refresh(init_integration)
    assert len(mock_media_server.calls_to("alive")) == 1
    assert len(mock_media_server.calls_to("get_zones")) == 2


async def test_expensive_tier_only_runs_on_change(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Playlists are not refetched on a play/pause transition."""
    before = len(mock_media_server.calls_to("get_current_playlist"))

    zone = mock_media_server.zones[0]
    mock_media_server.playback[10] = make_playback_info(zone, state=PlaybackState.PAUSED)
    await _refresh(init_integration)
    assert len(mock_media_server.calls_to("get_current_playlist")) == before

    mock_media_server.playback[10] = make_playback_info(
        zone, state=PlaybackState.PLAYING, file_key=999
    )
    await _refresh(init_integration)
    assert len(mock_media_server.calls_to("get_current_playlist")) == before + 1

    mock_media_server.playback[10] = make_playback_info(
        zone, state=PlaybackState.PLAYING, file_key=999, change_counter=7
    )
    await _refresh(init_integration)
    assert len(mock_media_server.calls_to("get_current_playlist")) == before + 2


async def test_adaptive_interval(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The interval slows down when nothing is playing."""
    coordinator = init_integration.runtime_data.coordinator
    assert coordinator.update_interval == timedelta(seconds=2)

    for zone_id, zone in ((10, mock_media_server.zones[0]), (20, mock_media_server.zones[1])):
        mock_media_server.playback[zone_id] = make_playback_info(zone, state=PlaybackState.STOPPED)
    await _refresh(init_integration)
    assert coordinator.update_interval == timedelta(seconds=6)


async def test_zone_failure_is_isolated(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """A failing per zone call keeps the previous value and does not fail the tick."""
    coordinator = init_integration.runtime_data.coordinator
    mock_media_server.fail["get_current_playlist"] = ValueError("bad json")
    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], file_key=555)

    await _refresh(init_integration)

    assert coordinator.last_update_success is True
    assert len(coordinator.data.playlist(10)) == 3
    assert coordinator.data.playback_info(10).file_key == 555


async def test_cheap_tier_failure_raises_update_failed(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """A failure of the cheap tier marks the coordinator as failed."""
    coordinator = init_integration.runtime_data.coordinator
    mock_media_server.fail["get_zones"] = CannotConnectError("boom")

    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)


async def test_unsupported_repeat_is_not_asked_for_again(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """An unsupported endpoint is only tried once."""
    coordinator = init_integration.runtime_data.coordinator
    mock_media_server.fail["get_repeat"] = UnsupportedRequestError("nope")
    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], file_key=321)
    await _refresh(init_integration)
    before = len(mock_media_server.calls_to("get_repeat"))
    assert coordinator.data.repeat(10) is None

    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], file_key=322)
    await _refresh(init_integration)
    assert len(mock_media_server.calls_to("get_repeat")) == before


async def test_only_allowed_zones_are_polled(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Zones outside the allowlist are not polled, bar the active zone."""
    mock_media_server.active_zone_id = 20
    mock_media_server.zones[0].active = False
    mock_media_server.zones[1].active = True
    entry = build_entry(options={CONF_DEVICE_ZONES: ["Player"]})
    await setup_integration(hass, entry)

    polled = {args[0].name for args, _ in mock_media_server.calls_to("get_playback_info")}
    assert polled == {"Player", "Office"}

    mock_media_server.active_zone_id = 10
    mock_media_server.zones[0].active = True
    mock_media_server.zones[1].active = False
    mock_media_server.calls.clear()
    await _refresh(entry)
    polled = {args[0].name for args, _ in mock_media_server.calls_to("get_playback_info")}
    assert polled == {"Player"}


@pytest.mark.parametrize("removed_zone_id", [20])
async def test_removed_zones_are_pruned(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_media_server: FakeMediaServer,
    removed_zone_id: int,
) -> None:
    """State for a zone that disappears is dropped."""
    coordinator = init_integration.runtime_data.coordinator
    assert coordinator.data.audio_path(removed_zone_id) is not None

    mock_media_server.zones = [mock_media_server.zones[0]]
    await _refresh(init_integration)

    assert removed_zone_id not in coordinator.data.audio_path_by_zone_id
    assert removed_zone_id not in coordinator.data.playback_info_by_zone_id
