"""Test setup, unload and migration of the JRiver integration."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver import async_remove_config_entry_device
from custom_components.jriver.const import (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_EXTRA_FIELDS,
    CONF_POLL_INTERVAL,
    CONF_TURN_OFF_BEHAVIOUR,
    DOMAIN,
)
from custom_components.jriver.mcws import CannotConnectError, InvalidAuthError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import ACCESS_KEY, FakeMediaServer, build_entry, setup_integration


async def test_setup_and_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_media_server
) -> None:
    """The entry loads, creates entities and unloads cleanly."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data.server is mock_media_server
    assert hass.states.get("media_player.phosphorus") is not None

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_media_server.closed is True


async def test_server_device_is_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A single server device is registered."""
    devices = dr.async_get(hass)
    device = devices.async_get_device(identifiers={(DOMAIN, ACCESS_KEY)})
    assert device is not None
    assert device.manufacturer == "JRiver"
    assert device.model == "Media Center (Windows)"
    assert device.configuration_url == "http://1.1.1.1:52199/"


async def test_zone_devices_are_created(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Per zone mode creates a device per zone linked to the server."""
    entry = build_entry(
        options={CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: ["Player", "Office"]}
    )
    await setup_integration(hass, entry)

    devices = dr.async_get(hass)
    server = devices.async_get_device(identifiers={(DOMAIN, ACCESS_KEY)})
    zone = devices.async_get_device(identifiers={(DOMAIN, f"{ACCESS_KEY}_zone_10")})
    assert zone is not None
    assert zone.via_device_id == server.id
    assert zone.name == "Phosphorus Player"


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (CannotConnectError("nope"), ConfigEntryState.SETUP_RETRY),
        (InvalidAuthError("nope"), ConfigEntryState.SETUP_ERROR),
    ],
)
async def test_setup_failures(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_media_server: FakeMediaServer,
    error: Exception,
    expected: ConfigEntryState,
) -> None:
    """Connection failures retry, auth failures start a reauth flow."""
    mock_media_server.fail["get_zones"] = error
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is expected


async def test_migration_moves_options(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """A version 1 entry has its option keys moved out of data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCESS_KEY,
        version=1,
        data={
            CONF_NAME: "Phosphorus",
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 52199,
            CONF_MAC: [],
            CONF_BROWSE_PATHS: ["Audio,Album|Album"],
            CONF_DEVICE_PER_ZONE: False,
            CONF_DEVICE_ZONES: [],
            CONF_EXTRA_FIELDS: ["Genre"],
        },
    )
    await setup_integration(hass, entry)

    assert entry.version == 2
    assert CONF_BROWSE_PATHS not in entry.data
    assert entry.options[CONF_BROWSE_PATHS] == ["Audio,Album|Album"]
    assert entry.options[CONF_EXTRA_FIELDS] == ["Genre"]
    assert entry.options[CONF_POLL_INTERVAL] == 2
    assert entry.options[CONF_TURN_OFF_BEHAVIOUR] == "stop"
    assert entry.options[CONF_DSP_PRESETS] == []


async def test_migration_retitles_entry_from_access_key(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """A version 1 entry titled with the access key is retitled to the name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCESS_KEY,
        title=ACCESS_KEY,
        version=1,
        data={
            CONF_API_KEY: ACCESS_KEY,
            CONF_NAME: "Phosphorus",
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 52199,
            CONF_MAC: [],
            CONF_BROWSE_PATHS: [],
            CONF_DEVICE_PER_ZONE: False,
            CONF_DEVICE_ZONES: [],
            CONF_EXTRA_FIELDS: [],
        },
    )
    await setup_integration(hass, entry)

    assert entry.title == "Phosphorus"


async def test_migration_keeps_custom_title(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """A version 1 entry with a custom title keeps it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCESS_KEY,
        title="Downstairs stack",
        version=1,
        data={
            CONF_API_KEY: ACCESS_KEY,
            CONF_NAME: "Phosphorus",
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 52199,
            CONF_MAC: [],
            CONF_BROWSE_PATHS: [],
            CONF_DEVICE_PER_ZONE: False,
            CONF_DEVICE_ZONES: [],
            CONF_EXTRA_FIELDS: [],
        },
    )
    await setup_integration(hass, entry)

    assert entry.title == "Downstairs stack"


async def test_migration_rewrites_unique_ids(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Old unique ids are rewritten so entity ids and history survive."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ACCESS_KEY,
        version=1,
        data={
            CONF_NAME: "Phosphorus",
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 52199,
            CONF_MAC: [],
            CONF_BROWSE_PATHS: [],
            CONF_DEVICE_PER_ZONE: True,
            CONF_DEVICE_ZONES: ["Player"],
            CONF_EXTRA_FIELDS: [],
        },
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = {
        ("sensor", f"{ACCESS_KEY}_activezone"),
        ("sensor", f"{ACCESS_KEY}_uimode"),
        ("media_player", f"{ACCESS_KEY}_player-Player"),
        ("sensor", f"{ACCESS_KEY}_Player_playingnow"),
        ("sensor", f"{ACCESS_KEY}_Player_playlist"),
        ("sensor", f"{ACCESS_KEY}_Player_audiodirect"),
        ("remote", f"{ACCESS_KEY}_remote"),
    }
    for domain, unique_id in old:
        registry.async_get_or_create(
            domain, DOMAIN, unique_id, config_entry=entry, suggested_object_id=unique_id
        )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    unique_ids = {e.unique_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert f"{ACCESS_KEY}_active_zone" in unique_ids
    assert f"{ACCESS_KEY}_ui_mode" in unique_ids
    assert f"{ACCESS_KEY}_zone_10_media_player" in unique_ids
    assert f"{ACCESS_KEY}_zone_10_playing_now" in unique_ids
    assert f"{ACCESS_KEY}_zone_10_playlist" in unique_ids
    assert f"{ACCESS_KEY}_remote" in unique_ids
    # the sensor flavour of audio direct is dropped in favour of a binary_sensor
    assert f"{ACCESS_KEY}_Player_audiodirect" not in unique_ids
    assert f"{ACCESS_KEY}_zone_10_audio_direct" in unique_ids


async def test_options_update_reloads(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Changing the options reloads the entry."""
    hass.config_entries.async_update_entry(
        init_integration,
        options={**init_integration.options, CONF_POLL_INTERVAL: 5},
    )
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.LOADED
    assert init_integration.runtime_data.coordinator._poll_interval == 5


async def test_stale_devices_are_removed(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """0.4.x per entity devices and devices for removed zones are cleaned up."""
    entry = build_entry(
        options={CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: ["Player", "Office"]}
    )
    entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    legacy = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{ACCESS_KEY}_player")},
        manufacturer="JRiver",
        model="Media Server - media_player",
        name="Phosphorus",
    )
    gone = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{ACCESS_KEY}_zone_99")},
        manufacturer="JRiver",
        model="Zone",
        name="Phosphorus Deleted",
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert devices.async_get(legacy.id) is None
    assert devices.async_get(gone.id) is None
    assert devices.async_get_device(identifiers={(DOMAIN, ACCESS_KEY)}) is not None
    for zone_id in (10, 20):
        assert (
            devices.async_get_device(identifiers={(DOMAIN, f"{ACCESS_KEY}_zone_{zone_id}")})
            is not None
        )


async def test_remove_config_entry_device(
    hass: HomeAssistant, mock_media_server: FakeMediaServer
) -> None:
    """Live devices cannot be deleted from the UI, stale ones can."""
    entry = build_entry(
        options={CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: ["Player", "Office"]}
    )
    await setup_integration(hass, entry)

    devices = dr.async_get(hass)
    server = devices.async_get_device(identifiers={(DOMAIN, ACCESS_KEY)})
    zone = devices.async_get_device(identifiers={(DOMAIN, f"{ACCESS_KEY}_zone_10")})
    assert await async_remove_config_entry_device(hass, entry, server) is False
    assert await async_remove_config_entry_device(hass, entry, zone) is False

    stale = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{ACCESS_KEY}_zone_99")},
        name="Phosphorus Deleted",
    )
    assert await async_remove_config_entry_device(hass, entry, stale) is True
