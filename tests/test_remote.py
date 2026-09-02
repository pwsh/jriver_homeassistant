"""Test the JRiver remote."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import (
    DOMAIN,
    SERVICE_ACTIVATE_ZONE,
    SERVICE_LOAD_DSP_PRESET,
    SERVICE_SEND_MCC,
    SERVICE_STOP_AFTER,
)
from custom_components.jriver.mcws import MCC, CannotConnectError, KeyCommand, ViewMode
from homeassistant.components.remote import DOMAIN as REMOTE_DOMAIN, SERVICE_SEND_COMMAND
from homeassistant.const import SERVICE_TURN_ON, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

ENTITY = "remote.phosphorus"


async def _call(hass: HomeAssistant, domain: str, service: str, **data) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


async def test_is_on(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """The remote is on when a UI is shown."""
    assert hass.states.get(ENTITY).state == STATE_ON

    mock_media_server.view_mode = ViewMode.NO_UI
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == STATE_OFF


async def test_turn_on_shows_standard_view(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Turning on sets the standard view mode."""
    await _call(hass, REMOTE_DOMAIN, SERVICE_TURN_ON, entity_id=ENTITY)
    args, kwargs = mock_media_server.calls_to("send_mcc")[0]
    assert args[0] is MCC.SET_MODE
    assert kwargs["param"] == 0


async def test_send_command_maps_key_names(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Key names, key values and raw strings are all accepted."""
    await _call(
        hass,
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        entity_id=ENTITY,
        command=["UP", "Down", "hello"],
    )
    keys = mock_media_server.calls_to("send_key_presses")[0][0][0]
    assert keys == [KeyCommand.UP, KeyCommand.DOWN, "hello"]


async def test_activate_zone(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Activating a known zone passes the name through."""
    await _call(hass, DOMAIN, SERVICE_ACTIVATE_ZONE, entity_id=ENTITY, zone_name="Office")
    assert mock_media_server.calls_to("set_active_zone")[0][0][0] == "Office"


async def test_activate_unknown_zone(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """An unknown zone is rejected."""
    with pytest.raises(ServiceValidationError):
        await _call(hass, DOMAIN, SERVICE_ACTIVATE_ZONE, entity_id=ENTITY, zone_name="Nope")


async def test_send_mcc(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Raw MCC commands pass through with their parameters."""
    await _call(
        hass,
        DOMAIN,
        SERVICE_SEND_MCC,
        entity_id=ENTITY,
        command=22000,
        parameter=2,
        block=False,
    )
    args, kwargs = mock_media_server.calls_to("send_mcc")[0]
    assert args[0] == 22000
    assert kwargs["param"] == 2
    assert kwargs["block"] is False


@pytest.mark.parametrize(
    ("payload", "expected_call"),
    [
        ({"minutes": 30}, "stop_after_delay"),
        ({"current": True}, "stop_after_current"),
        ({"tracks": 2}, "send_mcc"),
    ],
)
async def test_stop_after(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_media_server,
    payload: dict,
    expected_call: str,
) -> None:
    """Each stop after flavour reaches the right client call."""
    await _call(hass, DOMAIN, SERVICE_STOP_AFTER, entity_id=ENTITY, **payload)
    assert mock_media_server.called(expected_call)


async def test_stop_after_requires_an_argument(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Calling stop_after with nothing is rejected."""
    with pytest.raises(ServiceValidationError):
        await _call(hass, DOMAIN, SERVICE_STOP_AFTER, entity_id=ENTITY)


async def test_load_dsp_preset(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """DSP presets can be loaded from the remote."""
    await _call(hass, DOMAIN, SERVICE_LOAD_DSP_PRESET, entity_id=ENTITY, preset="Night")
    assert mock_media_server.calls_to("load_dsp_preset")[0][0][0] == "Night"


async def test_command_errors_become_home_assistant_errors(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Client errors surface as HomeAssistantError rather than being swallowed."""
    mock_media_server.fail["set_active_zone"] = CannotConnectError("boom")
    with pytest.raises(HomeAssistantError):
        await _call(hass, DOMAIN, SERVICE_ACTIVATE_ZONE, entity_id=ENTITY, zone_name="Office")
