"""Base entity for the JRiver Media Center integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
import logging
from typing import Any, Concatenate

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TRANSIENT_ERRORS, MediaServerData, MediaServerUpdateCoordinator
from .mcws import (
    CannotConnectError,
    InvalidAuthError,
    MediaServer,
    UnsupportedRequestError,
)
from .models import JRiverConfigEntry

_LOGGER = logging.getLogger(__name__)


def entry_unique_id(entry: JRiverConfigEntry) -> str:
    """Return a stable id for the config entry."""
    return entry.unique_id or entry.entry_id


def server_device_id(entry: JRiverConfigEntry) -> str:
    """Return the identifier of the server device."""
    return entry_unique_id(entry)


def zone_device_id(entry: JRiverConfigEntry, zone_id: int) -> str:
    """Return the identifier of a zone device."""
    return f"{entry_unique_id(entry)}_zone_{zone_id}"


def build_unique_id(entry: JRiverConfigEntry, kind: str, zone_id: int | None) -> str:
    """Return the unique id of an entity."""
    if zone_id is None:
        return f"{entry_unique_id(entry)}_{kind}"
    return f"{zone_device_id(entry, zone_id)}_{kind}"


class MediaServerEntity(CoordinatorEntity[MediaServerUpdateCoordinator]):
    """Common behaviour for every JRiver entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MediaServerUpdateCoordinator,
        entry: JRiverConfigEntry,
        kind: str,
        *,
        zone_id: int | None = None,
        zone_name: str | None = None,
    ) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._server_name = entry.runtime_data.server_name
        self._attr_unique_id = build_unique_id(entry, kind, zone_id)

        info = coordinator.data.server_info
        scheme = "https" if entry.data.get(CONF_SSL) else "http"
        server_info = DeviceInfo(
            identifiers={(DOMAIN, server_device_id(entry))},
            manufacturer="JRiver",
            model=f"Media Center ({info.platform if info else 'Unknown'})",
            sw_version=info.version if info else None,
            name=self._server_name,
            configuration_url=(
                f"{scheme}://{entry.data.get(CONF_HOST)}:{entry.data.get(CONF_PORT)}/"
            ),
        )
        if zone_id is None:
            self._attr_device_info = server_info
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, zone_device_id(entry, zone_id))},
                manufacturer="JRiver",
                model="Zone",
                name=f"{self._server_name} {zone_name}",
                via_device=(DOMAIN, server_device_id(entry)),
            )

    @property
    def server(self) -> MediaServer:
        """Return the MCWS client."""
        return self._entry.runtime_data.server

    @property
    def data(self) -> MediaServerData:
        """Return the latest coordinator snapshot."""
        return self.coordinator.data

    @property
    def zone_id(self) -> int | None:
        """Return the zone this entity targets, if any."""
        return self._zone_id

    @property
    def zone(self):
        """Return the Zone object this entity targets, if resolvable."""
        return self.data.zone_for(self._zone_id)

    @property
    def available(self) -> bool:
        """Return True if the coordinator is healthy and the zone still exists."""
        if not super().available:
            return False
        if self._zone_id is None:
            return True
        return self.zone is not None


def cmd[EntityT: MediaServerEntity, **P](
    func: Callable[Concatenate[EntityT, P], Awaitable[Any]],
) -> Callable[Concatenate[EntityT, P], Coroutine[Any, Any, None]]:
    """Map client errors onto HomeAssistantError and refresh afterwards."""

    @wraps(func)
    async def wrapper(obj: EntityT, *args: P.args, **kwargs: P.kwargs) -> None:
        try:
            await func(obj, *args, **kwargs)
        except InvalidAuthError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
                translation_placeholders={"action": func.__name__},
            ) from exc
        except UnsupportedRequestError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported",
                translation_placeholders={"action": func.__name__},
            ) from exc
        except (CannotConnectError, *TRANSIENT_ERRORS) as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"action": func.__name__, "error": str(exc)},
            ) from exc
        await obj.coordinator.async_request_refresh()

    return wrapper
