"""Support for interfacing with the JRiver MCWS API."""

from __future__ import annotations

from collections.abc import Mapping
import datetime as dt
import logging
from typing import Any

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    BrowseError,
    BrowseMedia,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode as HaRepeatMode,
    async_process_play_media_url,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .browse_media import browse_nodes, media_source_content_filter
from .const import (
    DOMAIN,
    KIND_MEDIA_PLAYER,
    SERVICE_ADD_SEARCH,
    SERVICE_ADJUST_VOLUME,
    SERVICE_PLAY_PLAYLIST,
    SERVICE_PLAY_SEARCH,
    SERVICE_SEEK_RELATIVE,
    TurnOffBehaviour,
)
from .coordinator import MediaServerUpdateCoordinator
from .entity import MediaServerEntity, cmd
from .mcws import (
    MCC,
    BrowsePath,
    PlaybackInfo,
    PlaybackState,
    RepeatMode,
    ShuffleMode,
    Zone,
    parse_browse_paths_from_text,
)
from .media_types import translate_to_media_type
from .models import JRiverConfigEntry
from .services import (
    MC_ADD_SEARCH_SCHEMA,
    MC_ADJUST_VOLUME_SCHEMA,
    MC_PLAY_PLAYLIST_SCHEMA,
    MC_PLAY_SEARCH_SCHEMA,
    MC_SEEK_RELATIVE_SCHEMA,
    PLAY_MODES,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

BASE_FEATURES = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.CLEAR_PLAYLIST
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
)

REPEAT_TO_HA = {
    RepeatMode.OFF: HaRepeatMode.OFF,
    RepeatMode.PLAYLIST: HaRepeatMode.ALL,
    RepeatMode.TRACK: HaRepeatMode.ONE,
    RepeatMode.STOP: HaRepeatMode.OFF,
}

HA_TO_REPEAT = {
    HaRepeatMode.OFF: RepeatMode.OFF,
    HaRepeatMode.ALL: RepeatMode.PLAYLIST,
    HaRepeatMode.ONE: RepeatMode.TRACK,
}

ENQUEUE_TO_PLAY_MODE = {
    MediaPlayerEnqueue.ADD: "Add",
    MediaPlayerEnqueue.NEXT: "NextToPlay",
    MediaPlayerEnqueue.PLAY: "NextToPlay",
    MediaPlayerEnqueue.REPLACE: None,
}

JRIVER_MEDIA_TYPES = {
    MediaType.ARTIST,
    MediaType.ALBUM,
    MediaType.CHANNEL,
    MediaType.COMPOSER,
    MediaType.EPISODE,
    MediaType.GENRE,
    MediaType.IMAGE,
    MediaType.MOVIE,
    MediaType.MUSIC,
    MediaType.PLAYLIST,
    MediaType.SEASON,
    MediaType.TRACK,
    MediaType.TVSHOW,
    MediaType.VIDEO,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JRiverConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the JRiver media player platform."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ADD_SEARCH, MC_ADD_SEARCH_SCHEMA, "async_append_search_results"
    )
    platform.async_register_entity_service(
        SERVICE_PLAY_PLAYLIST, MC_PLAY_PLAYLIST_SCHEMA, "async_play_playlist"
    )
    platform.async_register_entity_service(
        SERVICE_PLAY_SEARCH, MC_PLAY_SEARCH_SCHEMA, "async_play_search"
    )
    platform.async_register_entity_service(
        SERVICE_SEEK_RELATIVE, MC_SEEK_RELATIVE_SCHEMA, "async_seek_relative"
    )
    platform.async_register_entity_service(
        SERVICE_ADJUST_VOLUME, MC_ADJUST_VOLUME_SCHEMA, "async_adjust_volume"
    )

    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if runtime.per_zone:
        zones = [z for z in coordinator.data.zones if not runtime.zones or z.name in runtime.zones]
        async_add_entities(JRiverMediaPlayer(coordinator, entry, zone=z) for z in zones)
    else:
        async_add_entities([JRiverMediaPlayer(coordinator, entry)])


class JRiverMediaPlayer(MediaServerEntity, MediaPlayerEntity):
    """A JRiver Media Center zone."""

    _attr_name = None
    _attr_media_image_remotely_accessible = False

    def __init__(
        self,
        coordinator: MediaServerUpdateCoordinator,
        entry: JRiverConfigEntry,
        zone: Zone | None = None,
    ) -> None:
        """Initialise the media player."""
        super().__init__(
            coordinator,
            entry,
            KIND_MEDIA_PLAYER,
            zone_id=zone.id if zone else None,
            zone_name=zone.name if zone else None,
        )
        runtime = entry.runtime_data
        self._configured_browse_paths: list[BrowsePath] = (
            parse_browse_paths_from_text(runtime.browse_paths) if runtime.browse_paths else []
        )
        self._per_zone = runtime.per_zone
        self._dsp_presets = runtime.dsp_presets
        self._turn_off_behaviour = runtime.turn_off_behaviour
        self._attr_sound_mode: str | None = None

    # -- helpers ---------------------------------------------------------

    @property
    def _info(self) -> PlaybackInfo | None:
        return self.data.playback_info(self._zone_id)

    @property
    def _target(self) -> Zone | None:
        return self.zone

    @property
    def _browse_paths(self) -> list[BrowsePath]:
        return self.data.browse_paths or self._configured_browse_paths

    # -- state -----------------------------------------------------------

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the features this zone supports right now."""
        features = BASE_FEATURES
        if self._per_zone:
            features |= MediaPlayerEntityFeature.GROUPING
        else:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._dsp_presets:
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        return features

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the zone."""
        info = self._info
        if info is None:
            return MediaPlayerState.OFF
        if info.state in (PlaybackState.STOPPED, PlaybackState.WAITING):
            return MediaPlayerState.IDLE
        if info.state == PlaybackState.PAUSED:
            return MediaPlayerState.PAUSED
        if info.state == PlaybackState.PLAYING:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def volume_level(self) -> float | None:
        """Return the volume level."""
        return self._info.volume if self._info else None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return True if muted."""
        return self._info.muted if self._info else None

    @property
    def media_content_id(self) -> str | None:
        """Return the key of the playing file."""
        info = self._info
        if info is None or info.file_key == -1:
            return None
        return str(info.file_key)

    @property
    def media_content_type(self) -> MediaType | str | None:
        """Return the type of the playing file."""
        info = self._info
        if info is None:
            return None
        return translate_to_media_type(info.media_type, info.media_sub_type, single=True)

    @property
    def media_duration(self) -> int | None:
        """Return the duration in seconds."""
        info = self._info
        if info is None or info.live_input or not info.duration_ms:
            return None
        return round(info.duration_ms / 1000) if info.duration_ms > 0 else None

    @property
    def media_position(self) -> int | None:
        """Return the position in seconds."""
        info = self._info
        if info is None or info.live_input or info.position_ms is None:
            return None
        return round(info.position_ms / 1000) if info.position_ms >= 0 else None

    @property
    def media_position_updated_at(self) -> dt.datetime | None:
        """Return when the position was last observed."""
        return self.data.position_updated_at(self._zone_id)

    @property
    def media_image_url(self) -> str | None:
        """Return the artwork url."""
        info = self._info
        if info is None or not info.image_url:
            return None
        return self.server.make_url(info.image_url)

    @property
    def media_title(self) -> str | None:
        """Return the title."""
        return self._info.name if self._info else None

    @property
    def media_artist(self) -> str | None:
        """Return the artist."""
        return self._info.artist if self._info else None

    @property
    def media_album_name(self) -> str | None:
        """Return the album."""
        return self._info.album if self._info else None

    @property
    def media_album_artist(self) -> str | None:
        """Return the album artist."""
        return self._info.album_artist if self._info else None

    @property
    def media_series_title(self) -> str | None:
        """Return the series title."""
        return self._info.series if self._info else None

    @property
    def media_season(self) -> str | None:
        """Return the season."""
        return self._info.season if self._info else None

    @property
    def media_episode(self) -> str | None:
        """Return the episode."""
        return self._info.episode if self._info else None

    @property
    def repeat(self) -> HaRepeatMode | None:
        """Return the repeat mode."""
        mode = self.data.repeat(self._zone_id)
        return REPEAT_TO_HA.get(mode) if mode else None

    @property
    def shuffle(self) -> bool | None:
        """Return True if shuffle is on."""
        mode = self.data.shuffle(self._zone_id)
        if mode is None:
            return None
        return mode in (ShuffleMode.ON, ShuffleMode.RESHUFFLE)

    @property
    def source(self) -> str | None:
        """Return the active zone name (single device mode only)."""
        if self._per_zone:
            return None
        return self.data.active_zone_name

    @property
    def source_list(self) -> list[str] | None:
        """Return the list of zones (single device mode only)."""
        if self._per_zone:
            return None
        return self.data.zone_names

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return the configured DSP presets."""
        return self._dsp_presets or None

    @property
    def group_members(self) -> list[str] | None:
        """Return the entity ids of the zones linked to this one."""
        if not self._per_zone:
            return None
        info = self._info
        if info is None:
            return None
        members = [self.entity_id]
        for zone_id in info.linked_zones:
            if zone_id == self._zone_id:
                continue
            if entity_id := self._entity_id_for_zone(zone_id):
                members.append(entity_id)
        return members

    def _entity_id_for_zone(self, zone_id: int) -> str | None:
        """Map a zone id to the media player entity id representing it."""
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(self.hass)
        return registry.async_get_entity_id(
            "media_player",
            DOMAIN,
            f"{self._entry.unique_id or self._entry.entry_id}_zone_{zone_id}_{KIND_MEDIA_PLAYER}",
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Expose the zone details that have no first class attribute."""
        info = self._info
        if info is None:
            return None
        audio_path = self.data.audio_path(self._zone_id)
        attributes: dict[str, Any] = {
            "zone_name": info.zone_name,
            "zone_id": info.zone_id,
            "linked_zones": info.linked_zones,
            "playing_now_position": info.playing_now_position,
            "playing_now_tracks": info.playing_now_tracks,
            "next_file_key": info.next_file_key if info.next_file_key != -1 else None,
            "live_input": info.live_input,
        }
        if audio_path is not None:
            attributes["audio_direct"] = audio_path.is_direct
            attributes["audio_path"] = audio_path.paths
        for key in ("bitrate", "sample_rate", "bitdepth", "channels"):
            value = getattr(info, key, None)
            if value:
                attributes[key] = value
        attributes.update(info.extra_fields)
        return attributes

    async def async_get_media_image(self) -> tuple[bytes | None, str | None]:
        """Fetch the artwork through the authenticated MCWS session."""
        url = self.media_image_url
        if not url:
            return None, None
        if "Token=" not in url:
            try:
                token = await self.server.get_auth_token()
            except Exception as err:  # noqa: BLE001 - artwork is best effort
                _LOGGER.debug("Unable to obtain an auth token: %r", err)
                token = None
            if token:
                url = f"{url}{'&' if '?' in url else '?'}Token={token}"
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                content_type = response.headers.get("Content-Type")
        except Exception as err:  # noqa: BLE001 - artwork is best effort
            _LOGGER.debug("Unable to fetch artwork from %s: %r", url, err)
            return None, None
        return content, content_type

    # -- commands --------------------------------------------------------

    @cmd
    async def async_volume_up(self) -> None:
        """Turn the volume up."""
        await self.server.volume_up(zone=self._target)

    @cmd
    async def async_volume_down(self) -> None:
        """Turn the volume down."""
        await self.server.volume_down(zone=self._target)

    @cmd
    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level."""
        await self.server.set_volume_level(volume, zone=self._target)

    @cmd
    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute."""
        await self.server.mute(mute, zone=self._target)

    @cmd
    async def async_media_play(self) -> None:
        """Start playback."""
        info = self._info
        state = info.state if info is not None else None
        if state == PlaybackState.PLAYING:
            return
        if state == PlaybackState.PAUSED:
            # Playback/Play is a no-op on some builds when resuming, the toggle is reliable.
            await self.server.play_pause(zone=self._target)
            return
        await self.server.play(zone=self._target)

    @cmd
    async def async_media_pause(self) -> None:
        """Pause playback."""
        await self.server.pause(zone=self._target)

    @cmd
    async def async_media_play_pause(self) -> None:
        """Toggle playback."""
        await self.server.play_pause(zone=self._target)

    @cmd
    async def async_media_stop(self) -> None:
        """Stop playback."""
        await self.server.stop(zone=self._target)

    @cmd
    async def async_media_next_track(self) -> None:
        """Skip to the next track."""
        await self.server.next_track(zone=self._target)

    @cmd
    async def async_media_previous_track(self) -> None:
        """Skip to the previous track."""
        await self.server.previous_track(zone=self._target)

    @cmd
    async def async_media_seek(self, position: float) -> None:
        """Seek to an absolute position in seconds."""
        await self.server.media_seek(int(position * 1000), zone=self._target)

    @cmd
    async def async_seek_relative(self, seek_duration: float) -> None:
        """Seek forwards or backwards by the given number of seconds."""
        info = self._info
        if info is None:
            raise HomeAssistantError("Nothing is loaded in this zone")
        position = max(0, info.position_ms + int(seek_duration * 1000))
        if info.duration_ms and info.duration_ms > 0:
            position = min(position, info.duration_ms)
        await self.server.media_seek(position, zone=self._target)

    @cmd
    async def async_adjust_volume(self, delta: int) -> None:
        """Change the volume by a signed percentage."""
        await self.server.set_volume_relative(delta / 100, zone=self._target)

    @cmd
    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Turn shuffle on or off."""
        await self.server.set_shuffle(shuffle, zone=self._target)

    @cmd
    async def async_set_repeat(self, repeat: HaRepeatMode) -> None:
        """Set the repeat mode."""
        await self.server.set_repeat(HA_TO_REPEAT.get(repeat, RepeatMode.OFF), zone=self._target)

    @cmd
    async def async_clear_playlist(self) -> None:
        """Clear the playing now list."""
        await self.server.clear_playlist(zone=self._target)

    @cmd
    async def async_select_source(self, source: str) -> None:
        """Change the active zone."""
        if source not in self.data.zone_names:
            raise ServiceValidationError(f"Unknown zone {source}")
        await self.server.set_active_zone(source)

    @cmd
    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Load a DSP preset."""
        if sound_mode not in self._dsp_presets:
            raise ServiceValidationError(f"Unknown DSP preset {sound_mode}")
        await self.server.load_dsp_preset(sound_mode, zone=self._target)
        self._attr_sound_mode = sound_mode

    @cmd
    async def async_join_players(self, group_members: list[str]) -> None:
        """Link the given zones to this one."""
        for entity_id in group_members:
            zone = self._zone_for_entity_id(entity_id)
            if zone is None or zone.id == self._zone_id:
                continue
            await self.server.link_zones(self._target, zone)

    @cmd
    async def async_unjoin_player(self) -> None:
        """Unlink this zone."""
        await self.server.unlink_zone(self._target)

    def _zone_for_entity_id(self, entity_id: str) -> Zone | None:
        """Resolve another JRiver media player entity to a zone."""
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(self.hass)
        entity = registry.async_get(entity_id)
        if entity is None or not entity.unique_id:
            return None
        prefix = f"{self._entry.unique_id or self._entry.entry_id}_zone_"
        if not entity.unique_id.startswith(prefix):
            return None
        try:
            zone_id = int(entity.unique_id[len(prefix) :].split("_", 1)[0])
        except ValueError:
            return None
        return self.data.zone_for(zone_id)

    @cmd
    async def async_append_search_results(self, query: str) -> None:
        """Append the results of a search to the playing now list."""
        await self.server.play_search(query, zone=self._target, play_mode="Add")

    @cmd
    async def async_play_search(self, query: str, play_mode: str = "replace") -> None:
        """Play the results of a search."""
        mode = PLAY_MODES.get(play_mode)
        if mode is None:
            await self.server.clear_playlist(zone=self._target)
        await self.server.play_search(query, zone=self._target, play_mode=mode)

    @cmd
    async def async_play_playlist(self, playlist_path: str) -> None:
        """Play a stored playlist."""
        path = (playlist_path or "").strip()
        if not path:
            raise ServiceValidationError("playlist_path must not be empty")
        await self.server.play_playlist(path, zone=self._target)

    @cmd
    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        enqueue: MediaPlayerEnqueue | None = None,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Play, enqueue or queue-next the given media."""
        play_mode = ENQUEUE_TO_PLAY_MODE.get(enqueue) if enqueue else None
        replace = play_mode is None

        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            media_id = async_process_play_media_url(self.hass, play_item.url)
            media_type = MediaType.URL

        if replace:
            await self.server.clear_playlist(zone=self._target)

        media_type_lower = str(media_type).lower()

        if media_id.startswith("N|"):
            _, node_id, _ = media_id.split("|", 2)
            await self.server.play_browse_files(
                int(node_id), zone=self._target, play_mode=play_mode
            )
        elif media_id.startswith("K|"):
            await self.server.play_item(media_id[2:], zone=self._target, play_mode=play_mode)
        elif media_type_lower in ("query", "search"):
            await self.server.play_search(media_id, zone=self._target, play_mode=play_mode)
        elif media_type_lower == MediaType.PLAYLIST:
            await self.server.play_playlist(media_id, zone=self._target, play_mode=play_mode)
        elif media_type_lower in JRIVER_MEDIA_TYPES:
            raise ServiceValidationError(f"Unable to play {media_type} content id {media_id}")
        else:
            await self.server.play_file(
                async_process_play_media_url(self.hass, media_id),
                zone=self._target,
                play_mode=play_mode,
            )

        if enqueue == MediaPlayerEnqueue.PLAY:
            await self.server.next_track(zone=self._target)

    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Browse the Media Center library and any HA media sources."""
        if media_content_id and media_source.is_media_source_id(media_content_id):
            return await media_source.async_browse_media(
                self.hass,
                media_content_id,
                content_filter=media_source_content_filter,
            )

        if not self._browse_paths:
            raise BrowseError("No browse paths are configured, add them in the integration options")

        card, has_nodes = await browse_nodes(
            self.hass,
            self.server,
            self._browse_paths,
            parent_content_type=media_content_type,
            parent_id=media_content_id or "-1",
        )
        if not media_content_type or has_nodes:
            return card
        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")

    @cmd
    async def async_turn_on(self) -> None:
        """Show the standard view."""
        await self.server.send_mcc(MCC.SET_MODE, param=0, block=True)

    @cmd
    async def async_turn_off(self) -> None:
        """Stop playback and, if configured, close Media Center."""
        await self.server.stop_all()
        if self._turn_off_behaviour == TurnOffBehaviour.CLOSE_PROGRAM:
            await self.server.send_mcc(MCC.CLOSE_PROGRAM, param=0, block=False)
