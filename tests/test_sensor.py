"""Test the JRiver sensors."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import CONF_DEVICE_ZONES
from custom_components.jriver.mcws import ViewMode
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import FakeMediaServer, build_entry, make_playback_info, setup_integration


async def test_active_zone_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """The active zone is exposed as an enum with the zone names as options."""
    state = hass.states.get("sensor.phosphorus_active_zone")
    assert state.state == "Player"
    assert state.attributes["options"] == ["Player", "Office"]
    assert state.attributes["id"] == 10
    assert state.attributes["device_class"] == "enum"


async def test_ui_mode_sensor(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The UI mode is exposed as a translated enum."""
    state = hass.states.get("sensor.phosphorus_ui_mode")
    assert state.state == "standard"
    assert "theater" in state.attributes["options"]

    mock_media_server.view_mode = ViewMode.THEATER
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.phosphorus_ui_mode").state == "theater"


async def test_version_sensor_is_disabled_by_default(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The version sensor exists but is not enabled."""
    registry = er.async_get(hass)
    entry = registry.async_get("sensor.phosphorus_version")
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get("sensor.phosphorus_version") is None


async def test_playing_now_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Playing now exposes the track name and bounded attributes."""
    state = hass.states.get("sensor.phosphorus_player_playing_now")
    assert state.state == "Everybody Hertz"
    assert state.attributes["artist"] == "Air"
    assert state.attributes["is_active"] is True
    # position churns every second so is deliberately not an attribute
    assert "position_ms" not in state.attributes
    assert "duration_ms" not in state.attributes


async def test_playlist_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """The playlist sensor counts tracks and lists only the next few."""
    state = hass.states.get("sensor.phosphorus_player_playing_now_list")
    assert state.state == "3"
    assert state.attributes["unit_of_measurement"] == "tracks"
    next_up = state.attributes["next_up"]
    assert [entry["name"] for entry in next_up] == ["Radian", "Lucky and Unhappy"]


async def test_zone_sensors_follow_the_allowlist(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Only the configured zones get zone sensors."""
    await setup_integration(hass, build_entry(options={CONF_DEVICE_ZONES: ["Player"]}))
    assert hass.states.get("sensor.phosphorus_player_playing_now") is not None
    assert hass.states.get("sensor.phosphorus_office_playing_now") is None


async def test_sensor_unavailable_when_update_fails(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Entities go unavailable when the coordinator cannot reach the server."""
    from custom_components.jriver.mcws import CannotConnectError

    mock_media_server.fail["get_zones"] = CannotConnectError("boom")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.phosphorus_active_zone").state == STATE_UNAVAILABLE


async def test_playing_now_includes_extra_fields(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Extra library fields become attributes."""
    mock_media_server.playback[10] = make_playback_info(
        mock_media_server.zones[0], extra_fields=["Genre"], Genre="Electronic"
    )
    from custom_components.jriver.const import CONF_EXTRA_FIELDS

    await setup_integration(hass, build_entry(options={CONF_EXTRA_FIELDS: ["Genre"]}))
    state = hass.states.get("sensor.phosphorus_player_playing_now")
    assert state.attributes["Genre"] == "Electronic"
