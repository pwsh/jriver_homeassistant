"""Test the JRiver diagnostics."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from homeassistant.core import HomeAssistant


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """Diagnostics describe the server and redact the secrets."""
    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, init_integration)

    assert diagnostics["entry"]["version"] == 2
    assert diagnostics["entry"]["data"]["password"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["username"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["mac"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["host"] == "1.1.1.1"

    assert diagnostics["server"]["name"] == "Phosphorus"
    assert diagnostics["server"]["supports_browse_rules"] is True
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert diagnostics["state"]["active_zone_id"] == 10
    assert diagnostics["state"]["view_mode"] == "STANDARD"
    assert diagnostics["state"]["playlist_lengths"]["10"] == 3
    assert diagnostics["state"]["playback"]["10"]["zone_name"] == "Player"
