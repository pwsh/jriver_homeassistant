"""Sensor platform for the JRiver Media Center integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    KIND_ACTIVE_ZONE,
    KIND_PLAYING_NOW,
    KIND_PLAYLIST,
    KIND_UI_MODE,
    KIND_VERSION,
    NEXT_UP_COUNT,
)
from .coordinator import MediaServerUpdateCoordinator
from .entity import MediaServerEntity
from .mcws import ViewMode, Zone
from .models import JRiverConfigEntry

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JRiverConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the JRiver sensor platform."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    entities: list[SensorEntity] = [
        JRiverActiveZoneSensor(coordinator, entry),
        JRiverUiModeSensor(coordinator, entry),
        JRiverVersionSensor(coordinator, entry),
    ]
    for zone in coordinator.data.zones:
        if runtime.zones and zone.name not in runtime.zones:
            continue
        entities.append(JRiverPlayingNowSensor(coordinator, entry, zone))
        entities.append(JRiverPlaylistSensor(coordinator, entry, zone))

    async_add_entities(entities)


class JRiverActiveZoneSensor(MediaServerEntity, SensorEntity):
    """Expose the currently active zone."""

    _attr_translation_key = KIND_ACTIVE_ZONE
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator: MediaServerUpdateCoordinator, entry: JRiverConfigEntry) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, entry, KIND_ACTIVE_ZONE)

    @property
    def options(self) -> list[str]:
        """Return the known zone names."""
        return self.data.zone_names

    @property
    def native_value(self) -> str | None:
        """Return the active zone name."""
        name = self.data.active_zone_name
        return name if name in self.options else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the active zone id."""
        return {"id": self.data.active_zone_id}


class JRiverUiModeSensor(MediaServerEntity, SensorEntity):
    """Expose the Media Center UI mode."""

    _attr_translation_key = KIND_UI_MODE
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = [mode.name.lower() for mode in ViewMode]

    def __init__(self, coordinator: MediaServerUpdateCoordinator, entry: JRiverConfigEntry) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, entry, KIND_UI_MODE)

    @property
    def native_value(self) -> str | None:
        """Return the current UI mode."""
        return self.data.view_mode.name.lower()

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the raw mode id."""
        return {"id": int(self.data.view_mode)}


class JRiverVersionSensor(MediaServerEntity, SensorEntity):
    """Expose the Media Center version."""

    _attr_translation_key = KIND_VERSION
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: MediaServerUpdateCoordinator, entry: JRiverConfigEntry) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, entry, KIND_VERSION)

    @property
    def native_value(self) -> str | None:
        """Return the version string."""
        info = self.data.server_info
        return info.version if info else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the platform and library version."""
        info = self.data.server_info
        if info is None:
            return {}
        return {
            "platform": info.platform,
            "library_version": info.library_version,
            "product_version": info.product_version,
        }


class JRiverPlayingNowSensor(MediaServerEntity, SensorEntity):
    """Expose what is playing in a zone."""

    _attr_translation_key = KIND_PLAYING_NOW

    def __init__(
        self,
        coordinator: MediaServerUpdateCoordinator,
        entry: JRiverConfigEntry,
        zone: Zone,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, entry, KIND_PLAYING_NOW, zone_id=zone.id, zone_name=zone.name)

    @property
    def native_value(self) -> str | None:
        """Return the name of the playing file."""
        info = self.data.playback_info(self._zone_id)
        return info.name if info else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the track metadata, excluding anything that ticks every second."""
        info = self.data.playback_info(self._zone_id)
        if info is None:
            return {}
        attributes = {
            key: value
            for key, value in info.as_dict().items()
            if key not in ("position_ms", "duration_ms", "elapsed_time_display")
        }
        attributes["is_active"] = self.data.active_zone_id == self._zone_id
        return attributes


class JRiverPlaylistSensor(MediaServerEntity, SensorEntity):
    """Expose the size of the playing now list in a zone."""

    _attr_translation_key = KIND_PLAYLIST
    _attr_native_unit_of_measurement = "tracks"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: MediaServerUpdateCoordinator,
        entry: JRiverConfigEntry,
        zone: Zone,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, entry, KIND_PLAYLIST, zone_id=zone.id, zone_name=zone.name)

    @property
    def native_value(self) -> int | None:
        """Return the number of entries in the playing now list."""
        playlist = self.data.playlist(self._zone_id)
        return len(playlist) if playlist is not None else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return a bounded view of the upcoming entries."""
        playlist = self.data.playlist(self._zone_id)
        if not playlist:
            return {"next_up": []}
        info = self.data.playback_info(self._zone_id)
        start = max(0, info.playing_now_position + 1) if info else 0
        next_up = [
            {
                "key": entry.get("Key"),
                "name": entry.get("Name"),
                "artist": entry.get("Artist"),
                "album": entry.get("Album"),
            }
            for entry in playlist[start : start + NEXT_UP_COUNT]
        ]
        return {"next_up": next_up}
