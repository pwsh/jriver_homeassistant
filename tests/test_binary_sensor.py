"""Test the JRiver binary sensors."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import CONF_DEVICE_ZONES
from custom_components.jriver.mcws import AudioPath
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import FakeMediaServer, build_entry, make_playback_info, setup_integration


async def test_audio_direct(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Audio direct reflects the audio path and lists the DSP chain."""
    assert hass.states.get("binary_sensor.phosphorus_player_audio_direct").state == (STATE_ON)
    office = hass.states.get("binary_sensor.phosphorus_office_audio_direct")
    assert office.state == STATE_OFF
    assert office.attributes["audio_path"] == ["Convert 2 to 2 channels"]


async def test_audio_direct_is_diagnostic(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Audio direct is a diagnostic entity."""
    registry = er.async_get(hass)
    entity = registry.async_get("binary_sensor.phosphorus_player_audio_direct")
    assert entity.entity_category is er.EntityCategory.DIAGNOSTIC


async def test_audio_direct_updates(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The value follows the audio path on a track change."""
    mock_media_server.audio_paths[10] = AudioPath(is_direct=False, paths=["Upmix"])
    mock_media_server.playback[10] = make_playback_info(mock_media_server.zones[0], file_key=777)
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.phosphorus_player_audio_direct").state == (STATE_OFF)


async def test_allowlist(hass: HomeAssistant, mock_media_server: FakeMediaServer) -> None:
    """Only allowed zones get a binary sensor."""
    await setup_integration(hass, build_entry(options={CONF_DEVICE_ZONES: ["Office"]}))
    assert hass.states.get("binary_sensor.phosphorus_office_audio_direct") is not None
    assert hass.states.get("binary_sensor.phosphorus_player_audio_direct") is None
