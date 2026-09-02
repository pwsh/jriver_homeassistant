"""Binary sensor platform for the JRiver Media Center integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import KIND_AUDIO_DIRECT
from .coordinator import MediaServerUpdateCoordinator
from .entity import MediaServerEntity
from .mcws import Zone
from .models import JRiverConfigEntry

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JRiverConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the JRiver binary sensor platform."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    async_add_entities(
        JRiverAudioDirectSensor(coordinator, entry, zone)
        for zone in coordinator.data.zones
        if not runtime.zones or zone.name in runtime.zones
    )


class JRiverAudioDirectSensor(MediaServerEntity, BinarySensorEntity):
    """Report whether a zone is playing without DSP."""

    _attr_translation_key = KIND_AUDIO_DIRECT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: MediaServerUpdateCoordinator,
        entry: JRiverConfigEntry,
        zone: Zone,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(
            coordinator, entry, KIND_AUDIO_DIRECT, zone_id=zone.id, zone_name=zone.name
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if the audio path is direct."""
        audio_path = self.data.audio_path(self._zone_id)
        return audio_path.is_direct if audio_path else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the DSP chain."""
        audio_path = self.data.audio_path(self._zone_id)
        return {"audio_path": audio_path.paths if audio_path else []}
