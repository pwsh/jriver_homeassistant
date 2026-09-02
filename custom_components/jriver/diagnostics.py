"""Diagnostics support for the JRiver Media Center integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_MAC, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .models import JRiverConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_MAC}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: JRiverConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    data = coordinator.data
    info = data.server_info

    return {
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "server": {
            "name": info.name if info else None,
            "version": info.version if info else None,
            "platform": info.platform if info else None,
            "library_version": info.library_version if info else None,
            "supports_browse_rules": info.supports_browse_rules if info else None,
            "supports_audio_path_direct": (info.supports_audio_path_direct if info else None),
        },
        "coordinator": {
            "update_interval": (
                coordinator.update_interval.total_seconds() if coordinator.update_interval else None
            ),
            "last_update_success": coordinator.last_update_success,
            "allowed_zones": coordinator.allowed_zones,
        },
        "state": {
            "zones": [
                {
                    "id": zone.id,
                    "name": zone.name,
                    "index": zone.index,
                    "active": zone.active,
                    "dlna": zone.is_dlna,
                }
                for zone in data.zones
            ],
            "active_zone_id": data.active_zone_id,
            "view_mode": data.view_mode.name,
            "playback": {
                zone_id: info.as_dict() for zone_id, info in data.playback_info_by_zone_id.items()
            },
            "audio_path": {
                zone_id: {"is_direct": path.is_direct, "paths": path.paths}
                for zone_id, path in data.audio_path_by_zone_id.items()
            },
            "playlist_lengths": {
                zone_id: len(entries) for zone_id, entries in data.playlist_by_zone_id.items()
            },
            "repeat": {k: str(v) for k, v in data.repeat_by_zone_id.items()},
            "shuffle": {k: str(v) for k, v in data.shuffle_by_zone_id.items()},
            "browse_paths": [str(path.name) for path in data.browse_paths],
        },
    }
