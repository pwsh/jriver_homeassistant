"""A DataUpdateCoordinator for JRiver Media Center."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import datetime as dt
import logging

import aiohttp

from homeassistant.components.media_player import MediaType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ALIVE_REFRESH_INTERVAL,
    BROWSE_PATHS_REFRESH_INTERVAL,
    DOMAIN,
    IDLE_POLL_MULTIPLIER,
    MAX_PLAYLIST_ENTRIES,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    PLAYLIST_FIELDS,
)
from .mcws import (
    AudioPath,
    BrowsePath,
    CannotConnectError,
    InvalidAuthError,
    InvalidRequestError,
    MediaServer,
    MediaServerError,
    MediaServerInfo,
    PlaybackInfo,
    PlaybackState,
    RepeatMode,
    ShuffleMode,
    UnsupportedRequestError,
    ViewMode,
    Zone,
    convert_browse_rules,
)

_LOGGER = logging.getLogger(__name__)

#: errors that mean "the server is temporarily unusable"
TRANSIENT_ERRORS = (
    CannotConnectError,
    InvalidRequestError,
    MediaServerError,
    TimeoutError,
    aiohttp.ClientError,
    ValueError,
)


@dataclass(frozen=True, kw_only=True)
class MediaServerData:
    """An immutable snapshot of the state of a Media Center instance."""

    server_info: MediaServerInfo | None = None
    zones: list[Zone] = field(default_factory=list)
    active_zone_id: int | None = None
    playback_info_by_zone_id: dict[int, PlaybackInfo] = field(default_factory=dict)
    audio_path_by_zone_id: dict[int, AudioPath] = field(default_factory=dict)
    playlist_by_zone_id: dict[int, list[dict]] = field(default_factory=dict)
    position_updated_at_by_zone_id: dict[int, dt.datetime] = field(default_factory=dict)
    repeat_by_zone_id: dict[int, RepeatMode] = field(default_factory=dict)
    shuffle_by_zone_id: dict[int, ShuffleMode] = field(default_factory=dict)
    view_mode: ViewMode = ViewMode.UNKNOWN
    browse_paths: list[BrowsePath] = field(default_factory=list)

    @property
    def zone_names(self) -> list[str]:
        """Return the names of every known zone."""
        return [z.name for z in self.zones]

    @property
    def active_zone(self) -> Zone | None:
        """Return the active zone, if known."""
        return self.zone_for(None)

    @property
    def active_zone_name(self) -> str | None:
        """Return the name of the active zone, if known."""
        zone = self.active_zone
        return zone.name if zone else None

    def zone_for(self, target: int | None) -> Zone | None:
        """Return the zone with the given id, or the active zone if none is given."""
        if target is not None:
            return next((z for z in self.zones if z.id == target), None)
        if self.active_zone_id is not None:
            zone = next((z for z in self.zones if z.id == self.active_zone_id), None)
            if zone:
                return zone
        return self.zones[0] if self.zones else None

    def _zone_id(self, target: int | None) -> int | None:
        zone = self.zone_for(target)
        return zone.id if zone else None

    def playback_info(self, target: int | None = None) -> PlaybackInfo | None:
        """Return playback info for the given (or active) zone."""
        return self._lookup(self.playback_info_by_zone_id, target)

    def audio_path(self, target: int | None = None) -> AudioPath | None:
        """Return the audio path for the given (or active) zone."""
        return self._lookup(self.audio_path_by_zone_id, target)

    def playlist(self, target: int | None = None) -> list[dict] | None:
        """Return the playing now list for the given (or active) zone."""
        return self._lookup(self.playlist_by_zone_id, target)

    def position_updated_at(self, target: int | None = None) -> dt.datetime | None:
        """Return when the position was last refreshed for the given (or active) zone."""
        return self._lookup(self.position_updated_at_by_zone_id, target)

    def repeat(self, target: int | None = None) -> RepeatMode | None:
        """Return the repeat mode for the given (or active) zone."""
        return self._lookup(self.repeat_by_zone_id, target)

    def shuffle(self, target: int | None = None) -> ShuffleMode | None:
        """Return the shuffle mode for the given (or active) zone."""
        return self._lookup(self.shuffle_by_zone_id, target)

    def _lookup(self, values: dict[int, object], target: int | None):
        zone_id = self._zone_id(target)
        return values.get(zone_id) if zone_id is not None else None


class MediaServerUpdateCoordinator(DataUpdateCoordinator[MediaServerData]):
    """Polls a Media Center instance and publishes an immutable snapshot."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        media_server: MediaServer,
        *,
        extra_fields: list[str] | None = None,
        allowed_zones: list[str] | None = None,
        poll_interval: int = 2,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=dt.timedelta(seconds=poll_interval),
        )
        self._media_server = media_server
        self._extra_fields = extra_fields or []
        self._allowed_zones = allowed_zones or []
        self._poll_interval = poll_interval
        self.data = MediaServerData()
        self._last_alive: dt.datetime | None = None
        self._last_path_refresh: dt.datetime | None = None
        self._supports_repeat = True
        self._supports_shuffle = True

    @property
    def media_server(self) -> MediaServer:
        """Return the underlying client."""
        return self._media_server

    @property
    def allowed_zones(self) -> list[str]:
        """Return the configured zone allowlist (empty means all zones)."""
        return self._allowed_zones

    def set_poll_interval(self, poll_interval: int) -> None:
        """Change the base poll interval."""
        self._poll_interval = poll_interval

    def is_polled(self, zone: Zone) -> bool:
        """Return True if the zone should be polled."""
        if not self._allowed_zones:
            return True
        return zone.name in self._allowed_zones or zone.active

    async def _async_update_data(self) -> MediaServerData:
        """Fetch the latest state, cheap tier first."""
        previous = self.data
        try:
            server_info = await self._async_alive(previous)
            zones, view_mode = await asyncio.gather(
                self._media_server.get_zones(),
                self._media_server.get_view_mode(),
            )
        except InvalidAuthError as err:
            raise ConfigEntryAuthFailed("Media Center rejected the stored credentials") from err
        except TRANSIENT_ERRORS as err:
            self._last_alive = None
            raise UpdateFailed(f"{type(err).__name__}: {err}") from err

        polled = [z for z in zones if self.is_polled(z)]
        playback_info_by_zone_id, refresh_zones = await self._async_playback_info(previous, polled)

        data = MediaServerData(
            server_info=server_info,
            zones=zones,
            active_zone_id=next((z.id for z in zones if z.active), None),
            playback_info_by_zone_id=playback_info_by_zone_id,
            position_updated_at_by_zone_id=self._position_updated_at(
                previous, playback_info_by_zone_id
            ),
            view_mode=view_mode,
            browse_paths=await self._async_browse_paths(previous, server_info),
            **await self._async_expensive(previous, polled, refresh_zones),
        )
        self._update_interval_for(data)
        return data

    async def _async_alive(self, previous: MediaServerData) -> MediaServerInfo:
        """Call Alive, but only occasionally."""
        now = dt_util.utcnow()
        if (
            previous.server_info is not None
            and self._last_alive is not None
            and (now - self._last_alive).total_seconds() < ALIVE_REFRESH_INTERVAL
        ):
            return previous.server_info
        server_info = await self._media_server.alive()
        self._last_alive = now
        return server_info

    async def _async_playback_info(
        self, previous: MediaServerData, polled: list[Zone]
    ) -> tuple[dict[int, PlaybackInfo], set[int]]:
        """Fetch playback info for every polled zone, isolating failures."""
        results = await asyncio.gather(
            *(
                self._media_server.get_playback_info(zone, extra_fields=self._extra_fields)
                for zone in polled
            ),
            return_exceptions=True,
        )

        playback_info_by_zone_id: dict[int, PlaybackInfo] = {}
        refresh_zones: set[int] = set()
        for zone, result in zip(polled, results, strict=True):
            if isinstance(result, BaseException):
                _LOGGER.debug("Unable to refresh playback info for zone %s: %r", zone.name, result)
                last = previous.playback_info_by_zone_id.get(zone.id)
                if last is not None:
                    playback_info_by_zone_id[zone.id] = last
                continue

            playback_info_by_zone_id[zone.id] = result
            last = previous.playback_info_by_zone_id.get(zone.id)
            if last is None:
                refresh_zones.add(zone.id)
            elif last.file_key != result.file_key:
                refresh_zones.add(zone.id)
            elif last.playing_now_change_counter != result.playing_now_change_counter:
                refresh_zones.add(zone.id)

        return playback_info_by_zone_id, refresh_zones

    @staticmethod
    def _position_updated_at(
        previous: MediaServerData, playback_info_by_zone_id: dict[int, PlaybackInfo]
    ) -> dict[int, dt.datetime]:
        """Stamp the time each zone's position was observed."""
        now = dt_util.utcnow()
        updated: dict[int, dt.datetime] = {}
        for zone_id, info in playback_info_by_zone_id.items():
            if info.state == PlaybackState.PLAYING:
                updated[zone_id] = now
            else:
                updated[zone_id] = previous.position_updated_at_by_zone_id.get(zone_id, now)
        return updated

    async def _async_expensive(
        self, previous: MediaServerData, polled: list[Zone], refresh_zones: set[int]
    ) -> dict:
        """Refresh audio path, playlist, repeat and shuffle for changed zones."""
        polled_ids = {z.id for z in polled}
        audio_path = {k: v for k, v in previous.audio_path_by_zone_id.items() if k in polled_ids}
        playlist = {k: v for k, v in previous.playlist_by_zone_id.items() if k in polled_ids}
        repeat = {k: v for k, v in previous.repeat_by_zone_id.items() if k in polled_ids}
        shuffle = {k: v for k, v in previous.shuffle_by_zone_id.items() if k in polled_ids}

        for zone in polled:
            if zone.id not in refresh_zones:
                continue
            _LOGGER.debug("Refreshing derived state for zone %s", zone.name)
            wanted_repeat = self._supports_repeat
            wanted_shuffle = self._supports_shuffle
            calls = [
                self._async_call(self._media_server.get_audio_path(zone)),
                self._async_call(
                    self._media_server.get_current_playlist(fields=PLAYLIST_FIELDS, zone=zone)
                ),
            ]
            if wanted_repeat:
                calls.append(
                    self._async_call(self._media_server.get_repeat(zone), feature="repeat")
                )
            if wanted_shuffle:
                calls.append(
                    self._async_call(self._media_server.get_shuffle(zone), feature="shuffle")
                )
            results = list(await asyncio.gather(*calls))

            value = results.pop(0)
            if value is not None:
                audio_path[zone.id] = value
            value = results.pop(0)
            if value is not None:
                playlist[zone.id] = list(value)[:MAX_PLAYLIST_ENTRIES]
            if wanted_repeat:
                value = results.pop(0)
                if value is not None:
                    repeat[zone.id] = value
                elif not self._supports_repeat:
                    repeat.clear()
            if wanted_shuffle:
                value = results.pop(0)
                if value is not None:
                    shuffle[zone.id] = value
                elif not self._supports_shuffle:
                    shuffle.clear()

        return {
            "audio_path_by_zone_id": audio_path,
            "playlist_by_zone_id": playlist,
            "repeat_by_zone_id": repeat,
            "shuffle_by_zone_id": shuffle,
        }

    async def _async_call(self, coro, feature: str | None = None):
        """Await a per-zone call, swallowing failures so one zone can't fail the tick."""
        try:
            return await coro
        except UnsupportedRequestError:
            if feature:
                _LOGGER.debug("Media Center does not support %s, will not ask again", feature)
                setattr(self, f"_supports_{feature}", False)
            return None
        except (InvalidAuthError, *TRANSIENT_ERRORS) as err:
            _LOGGER.debug("Optional refresh failed: %r", err)
            return None

    async def _async_browse_paths(
        self, previous: MediaServerData, server_info: MediaServerInfo
    ) -> list[BrowsePath]:
        """Reload the browse rules when stale or when the server version changed."""
        if not server_info.supports_browse_rules:
            return []

        stale = (
            not previous.browse_paths
            or self._last_path_refresh is None
            or (dt_util.utcnow() - self._last_path_refresh).total_seconds()
            >= BROWSE_PATHS_REFRESH_INTERVAL
            or previous.server_info is None
            or previous.server_info.version != server_info.version
        )
        if not stale:
            return previous.browse_paths

        try:
            rules = await self._media_server.get_browse_rules()
        except (InvalidAuthError, UnsupportedRequestError, *TRANSIENT_ERRORS) as err:
            _LOGGER.debug("Unable to refresh browse rules: %r", err)
            return previous.browse_paths

        paths = convert_browse_rules(rules)
        for name in ("Playlists", "Playing Now"):
            extra = BrowsePath(name)
            extra.media_types.append(MediaType.PLAYLIST)
            paths.append(extra)
        self._last_path_refresh = dt_util.utcnow()
        return paths

    def _update_interval_for(self, data: MediaServerData) -> None:
        """Poll quickly while something is playing, slowly otherwise."""
        playing = any(
            info.state == PlaybackState.PLAYING for info in data.playback_info_by_zone_id.values()
        )
        seconds = self._poll_interval
        if not playing:
            seconds = self._poll_interval * IDLE_POLL_MULTIPLIER
        seconds = max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, seconds))
        self.update_interval = dt.timedelta(seconds=seconds)
