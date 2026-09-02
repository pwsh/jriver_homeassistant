"""Service handlers for the JRiver Media Center integration."""

from __future__ import annotations

import asyncio
import logging
import re

import voluptuous as vol

from homeassistant.components.wake_on_lan import (
    DOMAIN as WOL_DOMAIN,
    SERVICE_SEND_MAGIC_PACKET,
)
from homeassistant.const import ATTR_DEVICE_ID, ATTR_ENTITY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.typing import VolDictType

from .const import (
    ATTR_CURRENT,
    ATTR_DELTA,
    ATTR_FIELDS,
    ATTR_LIMIT,
    ATTR_MCC_BLOCK,
    ATTR_MCC_COMMAND,
    ATTR_MCC_PARAMETER,
    ATTR_MINUTES,
    ATTR_PLAY_MODE,
    ATTR_PLAYLIST_PATH,
    ATTR_PRESET,
    ATTR_QUERY,
    ATTR_SEEK_DURATION,
    ATTR_TRACKS,
    ATTR_ZONE_NAME,
    DOMAIN,
    MAX_PLAYLIST_ENTRIES,
    PLAYLIST_FIELDS,
    SERVICE_GET_PLAYLIST,
    SERVICE_SEARCH,
    SERVICE_WAKE,
)
from .mcws import MediaServerError
from .models import JRiverConfigEntry

_LOGGER = logging.getLogger(__name__)

ZONE_UNIQUE_ID = re.compile(r"_zone_(?P<zone_id>-?\d+)_")

PLAY_MODES: dict[str, str | None] = {
    "replace": None,
    "add": "Add",
    "next": "NextToPlay",
}

# entity service schemas, registered by the platforms
MC_ADD_SEARCH_SCHEMA: VolDictType = {vol.Required(ATTR_QUERY): cv.string}
MC_PLAY_PLAYLIST_SCHEMA: VolDictType = {vol.Required(ATTR_PLAYLIST_PATH): cv.string}
MC_PLAY_SEARCH_SCHEMA: VolDictType = {
    vol.Required(ATTR_QUERY): cv.string,
    vol.Optional(ATTR_PLAY_MODE, default="replace"): vol.In(list(PLAY_MODES)),
}
MC_SEEK_RELATIVE_SCHEMA: VolDictType = {vol.Required(ATTR_SEEK_DURATION): vol.Coerce(float)}
MC_ADJUST_VOLUME_SCHEMA: VolDictType = {
    vol.Required(ATTR_DELTA): vol.All(vol.Coerce(int), vol.Range(min=-100, max=100))
}
MC_ACTIVATE_ZONE_SCHEMA: VolDictType = {vol.Required(ATTR_ZONE_NAME): cv.string}
MC_SEND_MCC_SCHEMA: VolDictType = {
    vol.Required(ATTR_MCC_COMMAND): vol.All(vol.Coerce(int), vol.Range(min=10000, max=40000)),
    vol.Optional(ATTR_MCC_PARAMETER): vol.Coerce(int),
    vol.Optional(ATTR_MCC_BLOCK, default=True): cv.boolean,
    vol.Optional(ATTR_ZONE_NAME): cv.string,
}
MC_STOP_AFTER_SCHEMA: VolDictType = {
    vol.Exclusive(ATTR_MINUTES, "stop_after"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Exclusive(ATTR_TRACKS, "stop_after"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Exclusive(ATTR_CURRENT, "stop_after"): cv.boolean,
}
MC_LOAD_DSP_PRESET_SCHEMA: VolDictType = {
    vol.Required(ATTR_PRESET): cv.string,
    vol.Optional(ATTR_ZONE_NAME): cv.string,
}

# domain service schemas
WAKE_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        },
        cv.has_at_least_one_key(ATTR_ENTITY_ID, ATTR_DEVICE_ID),
    )
)
GET_PLAYLIST_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id})
SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_QUERY): cv.string,
        vol.Optional(ATTR_FIELDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_LIMIT, default=100): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=MAX_PLAYLIST_ENTRIES)
        ),
    }
)


def _loaded_entry(hass: HomeAssistant, entry_id: str | None) -> JRiverConfigEntry | None:
    """Return a loaded JRiver config entry with runtime data attached."""
    if not entry_id:
        return None
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        return None
    if getattr(entry, "runtime_data", None) is None:
        return None
    return entry


def resolve_entity(hass: HomeAssistant, entity_id: str) -> tuple[JRiverConfigEntry, int | None]:
    """Resolve an entity id to its config entry and target zone id."""
    registry = er.async_get(hass)
    entity = registry.async_get(entity_id)
    if entity is None or entity.platform != DOMAIN:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_entity",
            translation_placeholders={"entity_id": entity_id},
        )
    entry = _loaded_entry(hass, entity.config_entry_id)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"entity_id": entity_id},
        )
    zone_id: int | None = None
    if entity.unique_id and (match := ZONE_UNIQUE_ID.search(entity.unique_id)):
        zone_id = int(match.group("zone_id"))
    return entry, zone_id


def _resolve_wake_targets(hass: HomeAssistant, call: ServiceCall) -> list[JRiverConfigEntry]:
    """Resolve the entities/devices in a wake call to config entries."""
    entries: dict[str, JRiverConfigEntry] = {}
    registry = er.async_get(hass)
    for entity_id in call.data.get(ATTR_ENTITY_ID, []):
        entity = registry.async_get(entity_id)
        if entity is None or entity.platform != DOMAIN:
            continue
        if entry := _loaded_entry(hass, entity.config_entry_id):
            entries[entry.entry_id] = entry

    devices = dr.async_get(hass)
    for device_id in call.data.get(ATTR_DEVICE_ID, []):
        device = devices.async_get(device_id)
        if device is None:
            continue
        for entry_id in device.config_entries:
            if entry := _loaded_entry(hass, entry_id):
                entries[entry.entry_id] = entry

    return list(entries.values())


async def _async_wake(call: ServiceCall) -> None:
    """Send a WOL magic packet to the configured MAC addresses."""
    hass = call.hass
    entries = _resolve_wake_targets(hass, call)
    if not entries:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_wake_target")

    if not hass.services.has_service(WOL_DOMAIN, SERVICE_SEND_MAGIC_PACKET):
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="wol_unavailable")

    macs = {mac for entry in entries for mac in entry.runtime_data.mac_addresses if mac}
    if not macs:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_mac_addresses")

    _LOGGER.debug("Sending WOL to %s", sorted(macs))
    await asyncio.gather(
        *(
            hass.services.async_call(
                WOL_DOMAIN, SERVICE_SEND_MAGIC_PACKET, service_data={"mac": mac}
            )
            for mac in sorted(macs)
        )
    )


async def _async_get_playlist(call: ServiceCall) -> ServiceResponse:
    """Return the playing now list for the targeted zone."""
    entry, zone_id = resolve_entity(call.hass, call.data[ATTR_ENTITY_ID])
    coordinator = entry.runtime_data.coordinator
    zone = coordinator.data.zone_for(zone_id)
    try:
        entries = await entry.runtime_data.server.get_current_playlist(
            fields=PLAYLIST_FIELDS, zone=zone
        )
    except MediaServerError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"action": SERVICE_GET_PLAYLIST, "error": str(err)},
        ) from err
    return {
        "zone": zone.name if zone else None,
        "entries": list(entries)[:MAX_PLAYLIST_ENTRIES],
    }


async def _async_search(call: ServiceCall) -> ServiceResponse:
    """Search the library and return the matching files."""
    entry, _ = resolve_entity(call.hass, call.data[ATTR_ENTITY_ID])
    try:
        results = await entry.runtime_data.server.search_files(
            call.data[ATTR_QUERY],
            fields=call.data.get(ATTR_FIELDS) or PLAYLIST_FIELDS,
            limit=call.data[ATTR_LIMIT],
        )
    except MediaServerError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"action": SERVICE_SEARCH, "error": str(err)},
        ) from err
    return {"results": list(results)}


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register the domain level services, once per HA start."""
    if hass.services.has_service(DOMAIN, SERVICE_WAKE):
        return

    hass.services.async_register(DOMAIN, SERVICE_WAKE, _async_wake, schema=WAKE_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PLAYLIST,
        _async_get_playlist,
        schema=GET_PLAYLIST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH,
        _async_search,
        schema=SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
