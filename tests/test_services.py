"""Test the JRiver domain level services."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import (
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_USE_WOL,
    DOMAIN,
    SERVICE_GET_PLAYLIST,
    SERVICE_SEARCH,
    SERVICE_WAKE,
)
from homeassistant.components.wake_on_lan import (
    DOMAIN as WOL_DOMAIN,
    SERVICE_SEND_MAGIC_PACKET,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr

from .conftest import ACCESS_KEY, FakeMediaServer, build_entry, setup_integration


@pytest.fixture
def wol_calls(hass: HomeAssistant):
    """Register a stub wake on LAN service and capture its calls."""
    calls = []

    async def _handler(call):
        calls.append(call.data)

    hass.services.async_register(WOL_DOMAIN, SERVICE_SEND_MAGIC_PACKET, _handler)
    return calls


async def test_wake_resolves_via_entity_registry(
    hass: HomeAssistant, init_integration: MockConfigEntry, wol_calls
) -> None:
    """The wake action resolves an entity id to the owning config entry."""
    await hass.services.async_call(
        DOMAIN, SERVICE_WAKE, {"entity_id": "remote.phosphorus"}, blocking=True
    )
    assert wol_calls == [{"mac": "aa:bb:cc:dd:ee:ff"}]


async def test_wake_resolves_via_device_registry(
    hass: HomeAssistant, init_integration: MockConfigEntry, wol_calls
) -> None:
    """The wake action also accepts a device id."""
    devices = dr.async_get(hass)
    device = devices.async_get_device(identifiers={(DOMAIN, ACCESS_KEY)})
    await hass.services.async_call(DOMAIN, SERVICE_WAKE, {"device_id": device.id}, blocking=True)
    assert wol_calls == [{"mac": "aa:bb:cc:dd:ee:ff"}]


async def test_wake_without_target(
    hass: HomeAssistant, init_integration: MockConfigEntry, wol_calls
) -> None:
    """An unknown entity is rejected rather than silently logged."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, SERVICE_WAKE, {"entity_id": "remote.nope"}, blocking=True
        )


async def test_wake_without_wol_integration(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A missing wake on LAN integration raises."""
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, SERVICE_WAKE, {"entity_id": "remote.phosphorus"}, blocking=True
        )


async def test_wake_without_mac_addresses(
    hass: HomeAssistant, mock_media_server: FakeMediaServer, wol_calls
) -> None:
    """No configured MACs is a validation error."""
    await setup_integration(hass, build_entry(options={CONF_USE_WOL: False}))
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, SERVICE_WAKE, {"entity_id": "remote.phosphorus"}, blocking=True
        )


async def test_get_playlist_response(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """get_playlist returns the full playing now list."""
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_PLAYLIST,
        {"entity_id": "media_player.phosphorus"},
        blocking=True,
        return_response=True,
    )
    assert response["zone"] == "Player"
    assert len(response["entries"]) == 3


async def test_get_playlist_uses_the_entity_zone(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """A per zone media player resolves to its own zone."""
    await setup_integration(
        hass,
        build_entry(
            options={
                CONF_DEVICE_PER_ZONE: True,
                CONF_DEVICE_ZONES: ["Player", "Office"],
            }
        ),
    )
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_PLAYLIST,
        {"entity_id": "media_player.phosphorus_office"},
        blocking=True,
        return_response=True,
    )
    assert response["zone"] == "Office"
    assert response["entries"] == []


async def test_search_response(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """search returns whatever the client found."""

    async def _search(query, fields=None, limit=None):
        mock_media_server.calls.append(("search_files", (query,), {"limit": limit}))
        return [{"Key": "1", "Name": "Radian"}]

    mock_media_server.search_files = _search
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_SEARCH,
        {"entity_id": "media_player.phosphorus", "query": "[Artist]=[Air]"},
        blocking=True,
        return_response=True,
    )
    assert response == {"results": [{"Key": "1", "Name": "Radian"}]}
    assert mock_media_server.calls_to("search_files")[0][1]["limit"] == 100


async def test_services_are_registered_once(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """All domain services are available."""
    for service in (SERVICE_WAKE, SERVICE_GET_PLAYLIST, SERVICE_SEARCH):
        assert hass.services.has_service(DOMAIN, service)
