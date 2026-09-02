"""The JRiver Media Center (https://jriver.com/) integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_EXTRA_FIELDS,
    CONF_POLL_INTERVAL,
    CONF_TURN_OFF_BEHAVIOUR,
    CONF_USE_WOL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_TURN_OFF_BEHAVIOUR,
    DOMAIN,
    KIND_ACTIVE_ZONE,
    KIND_MEDIA_PLAYER,
    KIND_PLAYING_NOW,
    KIND_PLAYLIST,
    KIND_UI_MODE,
    TurnOffBehaviour,
)
from .coordinator import MediaServerUpdateCoordinator
from .mcws import MediaServer, get_mcws_connection
from .models import JRiverConfigEntry, JRiverRuntimeData
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

#: option keys that used to live in ``entry.data``
MIGRATED_OPTION_KEYS = (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_EXTRA_FIELDS,
    CONF_USE_WOL,
)


def get_option(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Read an option, falling back to entry data then the given default."""
    if key in entry.options:
        return entry.options[key]
    if key in entry.data:
        return entry.data[key]
    return default


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the JRiver Media Center component."""
    async_register_services(hass)
    return True


def _build_media_server(hass: HomeAssistant, entry: JRiverConfigEntry) -> MediaServer:
    """Create a MediaServer client from the config entry."""
    connection = get_mcws_connection(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
        ssl=entry.data.get(CONF_SSL, False),
        timeout=entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        session=async_get_clientsession(hass),
    )
    return MediaServer(connection)


async def async_setup_entry(hass: HomeAssistant, entry: JRiverConfigEntry) -> bool:
    """Set up JRiver Media Center from a config entry."""
    server = _build_media_server(hass, entry)

    zones: list[str] = get_option(entry, CONF_DEVICE_ZONES) or []
    per_zone: bool = bool(get_option(entry, CONF_DEVICE_PER_ZONE, False))
    extra_fields: list[str] = get_option(entry, CONF_EXTRA_FIELDS) or []
    browse_paths: list[str] = get_option(entry, CONF_BROWSE_PATHS) or []
    mac_addresses: list[str] = get_option(entry, CONF_MAC) or []
    if not get_option(entry, CONF_USE_WOL, bool(mac_addresses)):
        mac_addresses = []
    poll_interval = int(get_option(entry, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))
    try:
        turn_off_behaviour = TurnOffBehaviour(
            get_option(entry, CONF_TURN_OFF_BEHAVIOUR, DEFAULT_TURN_OFF_BEHAVIOUR)
        )
    except ValueError:
        turn_off_behaviour = DEFAULT_TURN_OFF_BEHAVIOUR

    coordinator = MediaServerUpdateCoordinator(
        hass,
        entry,
        server,
        extra_fields=extra_fields,
        allowed_zones=zones,
        poll_interval=poll_interval,
    )

    entry.runtime_data = JRiverRuntimeData(
        server=server,
        coordinator=coordinator,
        server_name=entry.data.get(CONF_NAME) or entry.data.get(CONF_HOST, "JRiver"),
        zones=zones,
        browse_paths=browse_paths,
        extra_fields=extra_fields,
        mac_addresses=mac_addresses,
        per_zone=per_zone,
        turn_off_behaviour=turn_off_behaviour,
        dsp_presets=list(get_option(entry, CONF_DSP_PRESETS) or []),
    )

    async def _close(_event) -> None:
        await server.close()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close))
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await coordinator.async_config_entry_first_refresh()
    await _async_migrate_zone_unique_ids(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JRiverConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.server.close()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: JRiverConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an old config entry."""
    if entry.version > 2:
        return False

    if entry.version == 1:
        _LOGGER.debug("Migrating %s from version 1 to 2", entry.entry_id)
        data = dict(entry.data)
        options = dict(entry.options)
        for key in MIGRATED_OPTION_KEYS:
            value = data.pop(key, None)
            if key not in options and value is not None:
                options[key] = value
        options.setdefault(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        options.setdefault(CONF_TURN_OFF_BEHAVIOUR, DEFAULT_TURN_OFF_BEHAVIOUR.value)
        options.setdefault(CONF_DSP_PRESETS, [])
        data.setdefault(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        data.setdefault(CONF_API_KEY, "")

        await _async_migrate_server_unique_ids(hass, entry)

        hass.config_entries.async_update_entry(entry, data=data, options=options, version=2)

    return True


def _uid(entry: ConfigEntry) -> str:
    return entry.unique_id or entry.entry_id


async def _async_migrate_server_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rewrite the unique ids that do not depend on knowing the zone ids."""
    prefix = _uid(entry)
    mapping = {
        f"{prefix}_player": f"{prefix}_{KIND_MEDIA_PLAYER}",
        f"{prefix}_activezone": f"{prefix}_{KIND_ACTIVE_ZONE}",
        f"{prefix}_uimode": f"{prefix}_{KIND_UI_MODE}",
    }

    @callback
    def _migrate(entity: er.RegistryEntry) -> dict[str, Any] | None:
        if (new_id := mapping.get(entity.unique_id)) and new_id != entity.unique_id:
            _LOGGER.debug("Migrating %s to %s", entity.unique_id, new_id)
            return {"new_unique_id": new_id}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)


async def _async_migrate_zone_unique_ids(hass: HomeAssistant, entry: JRiverConfigEntry) -> None:
    """Rewrite zone name based unique ids now that the zone ids are known."""
    zones = entry.runtime_data.coordinator.data.zones
    if not zones:
        return

    prefix = _uid(entry)
    mapping: dict[str, str] = {}
    remove: set[str] = set()
    for zone in zones:
        mapping[f"{prefix}_player-{zone.name}"] = f"{prefix}_zone_{zone.id}_{KIND_MEDIA_PLAYER}"
        mapping[f"{prefix}_{zone.name}_playingnow"] = f"{prefix}_zone_{zone.id}_{KIND_PLAYING_NOW}"
        mapping[f"{prefix}_{zone.name}_playlist"] = f"{prefix}_zone_{zone.id}_{KIND_PLAYLIST}"
        # the audio direct entity moved from sensor to binary_sensor so the old
        # registry entry cannot be reused, drop it instead
        remove.add(f"{prefix}_{zone.name}_audiodirect")

    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id in remove and entity.domain == "sensor":
            _LOGGER.debug("Removing obsolete entity %s", entity.entity_id)
            registry.async_remove(entity.entity_id)

    @callback
    def _migrate(entity: er.RegistryEntry) -> dict[str, Any] | None:
        if new_id := mapping.get(entity.unique_id):
            if new_id != entity.unique_id and not registry.async_get_entity_id(
                entity.domain, DOMAIN, new_id
            ):
                _LOGGER.debug("Migrating %s to %s", entity.unique_id, new_id)
                return {"new_unique_id": new_id}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)
