"""Runtime data model for the JRiver Media Center integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_TURN_OFF_BEHAVIOUR, TurnOffBehaviour
from .coordinator import MediaServerUpdateCoordinator
from .mcws import MediaServer


@dataclass
class JRiverRuntimeData:
    """Everything a platform needs, hung off the config entry."""

    server: MediaServer
    coordinator: MediaServerUpdateCoordinator
    server_name: str
    zones: list[str] = field(default_factory=list)
    browse_paths: list[str] = field(default_factory=list)
    extra_fields: list[str] = field(default_factory=list)
    mac_addresses: list[str] = field(default_factory=list)
    per_zone: bool = False
    turn_off_behaviour: TurnOffBehaviour = DEFAULT_TURN_OFF_BEHAVIOUR
    dsp_presets: list[str] = field(default_factory=list)


type JRiverConfigEntry = ConfigEntry[JRiverRuntimeData]
