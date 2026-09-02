"""Remote platform for the JRiver Media Center integration."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    KIND_REMOTE,
    SERVICE_ACTIVATE_ZONE,
    SERVICE_LOAD_DSP_PRESET,
    SERVICE_SEND_MCC,
    SERVICE_STOP_AFTER,
    TurnOffBehaviour,
)
from .coordinator import MediaServerUpdateCoordinator
from .entity import MediaServerEntity, cmd
from .mcws import MCC, KeyCommand, ViewMode
from .models import JRiverConfigEntry
from .services import (
    MC_ACTIVATE_ZONE_SCHEMA,
    MC_LOAD_DSP_PRESET_SCHEMA,
    MC_SEND_MCC_SCHEMA,
    MC_STOP_AFTER_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JRiverConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the JRiver remote platform."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ACTIVATE_ZONE, MC_ACTIVATE_ZONE_SCHEMA, "async_activate_zone"
    )
    platform.async_register_entity_service(SERVICE_SEND_MCC, MC_SEND_MCC_SCHEMA, "async_send_mcc")
    platform.async_register_entity_service(
        SERVICE_STOP_AFTER, MC_STOP_AFTER_SCHEMA, "async_stop_after"
    )
    platform.async_register_entity_service(
        SERVICE_LOAD_DSP_PRESET, MC_LOAD_DSP_PRESET_SCHEMA, "async_load_dsp_preset"
    )

    async_add_entities([JRiverRemote(entry.runtime_data.coordinator, entry)])


class JRiverRemote(MediaServerEntity, RemoteEntity):
    """Control the Media Center user interface."""

    _attr_name = None

    def __init__(self, coordinator: MediaServerUpdateCoordinator, entry: JRiverConfigEntry) -> None:
        """Initialise the remote."""
        super().__init__(coordinator, entry, KIND_REMOTE)
        self._key_commands = {e.name: e for e in KeyCommand}
        self._key_values = {e.value: e for e in KeyCommand}
        self._turn_off_behaviour = entry.runtime_data.turn_off_behaviour

    @property
    def is_on(self) -> bool:
        """Return True if a Media Center window is visible."""
        return self.data.view_mode > ViewMode.NO_UI

    @cmd
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Show the standard view."""
        await self.server.send_mcc(MCC.SET_MODE, param=0, block=True)

    @cmd
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop playback and, if configured, close Media Center."""
        await self.server.stop_all()
        if self._turn_off_behaviour == TurnOffBehaviour.CLOSE_PROGRAM:
            await self.server.send_mcc(MCC.CLOSE_PROGRAM, param=0, block=False)

    @cmd
    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send one or more key presses."""
        keys: list[KeyCommand | str] = []
        for value in command:
            if value in self._key_commands:
                keys.append(self._key_commands[value])
            elif value in self._key_values:
                keys.append(self._key_values[value])
            else:
                keys.append(value)
        await self.server.send_key_presses(keys)

    @cmd
    async def async_activate_zone(self, zone_name: str) -> None:
        """Make the named zone active."""
        if zone_name not in self.data.zone_names:
            raise ServiceValidationError(f"Unknown zone {zone_name}")
        await self.server.set_active_zone(zone_name)

    @cmd
    async def async_send_mcc(
        self,
        command: int,
        parameter: int | None = None,
        block: bool = True,
        zone_name: str | None = None,
    ) -> None:
        """Send a raw MCC command."""
        await self.server.send_mcc(command, param=parameter, block=block, zone=zone_name)

    @cmd
    async def async_stop_after(
        self,
        minutes: int | None = None,
        tracks: int | None = None,
        current: bool | None = None,
    ) -> None:
        """Schedule playback to stop."""
        zone = self.data.active_zone
        if minutes is not None:
            await self.server.stop_after_delay(minutes, zone=zone)
        elif tracks is not None:
            await self.server.send_mcc(MCC.STOP_AFTER_TRACKS, param=tracks, block=True, zone=zone)
        elif current:
            await self.server.stop_after_current(zone=zone)
        else:
            raise ServiceValidationError("One of minutes, tracks or current must be supplied")

    @cmd
    async def async_load_dsp_preset(self, preset: str, zone_name: str | None = None) -> None:
        """Load a DSP preset by name."""
        await self.server.load_dsp_preset(preset, zone=zone_name)
