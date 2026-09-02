"""High level MCWS client for JRiver Media Center.

Derived from the ``hamcws`` library (https://github.com/3ll3d00d/hamcws) v0.2.7,
Copyright (c) 3ll3d00d, MIT licensed. See ``__init__.py`` for the full notice.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
import logging
import time
from xml.etree import ElementTree

from .browse import BrowseRule
from .connection import (
    MediaServerConnection,
    UnsupportedRequestError,
    to_dict,
)
from .mcc import MCC
from .models import (
    AudioPath,
    KeyCommand,
    LibraryField,
    MediaServerInfo,
    PlaybackInfo,
    Playlist,
    PlayMode,
    RepeatMode,
    ShuffleMode,
    ViewMode,
    Zone,
    _as_int,
    _safe_enum,
)

_LOGGER = logging.getLogger(__name__)

__all__ = ["MediaServer"]

ONE_DAY_IN_SECONDS = 60 * 60 * 24

DEFAULT_PLAYBACK_FIELDS = [
    "Media Type",
    "Media Sub Type",
    "Series",
    "Season",
    "Episode",
    "Album Artist (auto)",
]

DEFAULT_FILE_FIELDS = [
    "Key",
    "Name",
    "Media Type",
    "Media Sub Type",
    "Series",
    "Season",
    "Episode",
    "Artist",
    "Album",
    "Track #",
    "Dimensions",
    "HDR Format",
    "Duration",
]


class MediaServer:
    """A high level interface for MCWS."""

    def __init__(self, connection: MediaServerConnection) -> None:
        """Wrap the supplied connection."""
        self._conn = connection
        self._token: str | None = None
        self._token_obtained_at: float = 0
        self._media_server_info: MediaServerInfo | None = None

    @property
    def media_server_info(self) -> MediaServerInfo | None:
        """The info returned by the last ``alive`` call, if any."""
        return self._media_server_info

    @property
    def host(self) -> str:
        """The server host."""
        return self._conn.host

    @property
    def port(self) -> int:
        """The server port."""
        return self._conn.port

    @property
    def connection(self) -> MediaServerConnection:
        """The underlying connection."""
        return self._conn

    async def close(self) -> None:
        """Close the underlying connection."""
        await self._conn.close()

    def make_url(self, path: str) -> str:
        """Build a URL relative to the server root."""
        return self._conn.get_url(path)

    # ------------------------------------------------------------------
    # auth & urls
    # ------------------------------------------------------------------

    async def get_auth_token(self) -> str:
        """Get an authenticated token."""
        _, resp = await self._conn.get_as_dict("Authenticate")
        self._token = resp.get("Token") or ""
        self._token_obtained_at = time.time()
        return self._token

    async def _ensure_token(self) -> None:
        """Refresh the auth token if it is missing or stale."""
        now = time.time()
        if now - self._token_obtained_at > ONE_DAY_IN_SECONDS:
            await self.get_auth_token()

    def _file_image_url(self, file_key: int, thumbnail_size: str, image_format: str) -> str:
        """Build a file image URL using the currently held token."""
        params = (
            f"File={file_key}&Type=Thumbnail&ThumbnailSize={thumbnail_size}"
            f"&Format={image_format}&Token={self._token}"
        )
        return f"{self._conn.get_mcws_url('File/GetImage')}?{params}"

    async def get_file_image_url(
        self,
        file_key: int,
        thumbnail_size: str = "Large",
        format: str = "png",
    ) -> str:
        """Get the image URL for a file given its key."""
        await self._ensure_token()
        return self._file_image_url(file_key, thumbnail_size, format)

    async def get_browse_thumbnail_url(self, base_id: int = -1) -> str:
        """Get the image thumbnail URL for the given browse node id."""
        await self._ensure_token()
        return (
            f"{self._conn.get_mcws_url('Browse/Image')}"
            f"?UseStackedImages=1&Format=jpg&ID={base_id}&Token={self._token}"
        )

    # ------------------------------------------------------------------
    # server info
    # ------------------------------------------------------------------

    async def alive(self) -> MediaServerInfo:
        """Return info about the instance, no authentication required."""
        _, resp = await self._conn.get_as_dict("Alive")
        self._media_server_info = MediaServerInfo(resp)
        return self._media_server_info

    async def get_zones(self) -> list[Zone]:
        """All known zones."""
        _, resp = await self._conn.get_as_dict("Playback/Zones")
        num_zones = int(resp.get("NumberZones") or 0)
        active_zone_id = int(resp.get("CurrentZoneID") or -1)
        return [Zone(resp, i, active_zone_id) for i in range(num_zones)]

    async def get_library_fields(self) -> list[LibraryField]:
        """The fields defined in the library."""

        def _parse(text: str) -> tuple[bool, list[LibraryField]]:
            root = ElementTree.fromstring(text)
            if root.attrib.get("Status", "OK") != "OK":
                return False, []
            fields_el = (
                root if root.tag == "Fields" else next((c for c in root if c.tag == "Fields"), None)
            )
            if fields_el is None:
                return True, []
            return True, [
                LibraryField(
                    child.attrib.get("Name", ""),
                    child.attrib.get("DataType", ""),
                    child.attrib.get("EditType", ""),
                    child.attrib.get("DisplayName", ""),
                )
                for child in fields_el
            ]

        ok, resp = await self._conn.get("Library/Fields", _parse)
        return resp if ok else []

    async def get_ui_info(self) -> tuple[ViewMode, dict[str, str | None]]:
        """The current UI mode plus the raw ``UserInterface/Info`` response."""
        _, resp = await self._conn.get_as_dict("UserInterface/Info")
        mode = ViewMode.UNKNOWN
        raw_mode = resp.get("Mode")
        if raw_mode is not None:
            try:
                mode = ViewMode(int(raw_mode))
            except ValueError:
                _LOGGER.debug("Unknown ViewMode %r", raw_mode)
        return mode, resp

    async def get_view_mode(self) -> ViewMode:
        """Get the current UI mode."""
        mode, _ = await self.get_ui_info()
        return mode

    # ------------------------------------------------------------------
    # zone addressing
    # ------------------------------------------------------------------

    @staticmethod
    def _zone_params(zone: Zone | str | None = None) -> dict:
        """Build the query params that address the given zone."""
        if isinstance(zone, Zone):
            return zone.as_query_params()
        if isinstance(zone, str):
            return {"Zone": zone, "ZoneType": "Name"}
        return {}

    @staticmethod
    def _zone_value(zone: Zone | str | int) -> str | int:
        """Return the raw identifier (id or name) for a zone."""
        if isinstance(zone, Zone):
            return zone.id
        return zone

    async def set_active_zone(self, zone: Zone | str) -> bool:
        """Set the active zone."""
        if not zone:
            raise ValueError("zone is required")
        ok, _ = await self._conn.get_as_dict("Playback/SetZone", params=self._zone_params(zone))
        return ok

    async def link_zones(self, zone_a: Zone | str | int, zone_b: Zone | str | int) -> bool:
        """Link two zones together."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/LinkZones",
            params={
                "Zone1": self._zone_value(zone_a),
                "Zone2": self._zone_value(zone_b),
            },
        )
        return ok

    async def unlink_zone(self, zone: Zone | str | int) -> bool:
        """Unlink the given zone from any zone it is linked to."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/UnlinkZones", params={"Zone": self._zone_value(zone)}
        )
        return ok

    # ------------------------------------------------------------------
    # playback state
    # ------------------------------------------------------------------

    async def get_playback_info(
        self,
        zone: Zone | str | None = None,
        extra_fields: list[str] | None = None,
    ) -> PlaybackInfo:
        """Info about the current state of playback in the specified zone."""
        params = self._zone_params(zone)
        extra_fields = extra_fields or []
        params["Fields"] = ";".join(set(extra_fields + DEFAULT_PLAYBACK_FIELDS))
        _, resp = await self._conn.get_as_dict("Playback/Info", params=params)
        info = PlaybackInfo(resp, extra_fields)
        if info.image_url:
            await self._ensure_token()
            if self._token:
                info.image_url = f"{info.image_url}&Token={self._token}"
        return info

    async def play_pause(self, zone: Zone | str | None = None) -> bool:
        """Send play/pause command."""
        ok, _ = await self._conn.get_as_dict("Playback/PlayPause", params=self._zone_params(zone))
        return ok

    async def play(self, zone: Zone | str | None = None) -> bool:
        """Send play command."""
        ok, _ = await self._conn.get_as_dict("Playback/Play", params=self._zone_params(zone))
        return ok

    async def pause(self, zone: Zone | str | None = None) -> bool:
        """Send pause command."""
        ok, _ = await self._conn.get_as_dict("Playback/Pause", params=self._zone_params(zone))
        return ok

    async def stop(self, zone: Zone | str | None = None) -> bool:
        """Send stop command."""
        ok, _ = await self._conn.get_as_dict("Playback/Stop", params=self._zone_params(zone))
        return ok

    async def stop_all(self) -> bool:
        """Send stopAll command."""
        ok, _ = await self._conn.get_as_dict("Playback/StopAll")
        return ok

    async def next_track(self, zone: Zone | str | None = None) -> bool:
        """Send next track command."""
        ok, _ = await self._conn.get_as_dict("Playback/Next", params=self._zone_params(zone))
        return ok

    async def previous_track(self, zone: Zone | str | None = None) -> bool:
        """Send previous track command."""
        ok, _ = await self._conn.get_as_dict("Playback/Previous", params=self._zone_params(zone))
        return ok

    async def stop_after_current(self, zone: Zone | str | None = None) -> bool:
        """Stop playback once the current file completes."""
        return await self.send_mcc(MCC.STOP_AFTER_CURRENT_FILE, zone=zone)

    async def stop_after_delay(self, minutes: int, zone: Zone | str | None = None) -> bool:
        """Stop playback after the given number of minutes."""
        return await self.send_mcc(MCC.STOP_AFTER_DELAY, param=minutes, zone=zone)

    # ------------------------------------------------------------------
    # position
    # ------------------------------------------------------------------

    async def get_position(self, zone: Zone | str | None = None) -> int:
        """The current playback position in ms."""
        _, resp = await self._conn.get_as_dict("Playback/Position", params=self._zone_params(zone))
        return int(resp.get("Position") or 0)

    async def set_position(self, position: int, zone: Zone | str | None = None) -> bool:
        """Seek to a specified position in ms."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/Position",
            params={"Position": position, **self._zone_params(zone)},
        )
        return ok

    async def media_seek(self, position: int, zone: Zone | str | None = None) -> bool:
        """Seek to a specified position in ms."""
        return await self.set_position(position, zone)

    async def seek_relative(self, delta_ms: int, zone: Zone | str | None = None) -> bool:
        """Seek by the given (signed) number of ms, clamped at zero."""
        current = await self.get_position(zone)
        return await self.set_position(max(0, current + delta_ms), zone)

    # ------------------------------------------------------------------
    # volume
    # ------------------------------------------------------------------

    async def volume_up(self, step: float = 0.1, zone: Zone | str | None = None) -> float:
        """Send volume up command."""
        return await self.set_volume_relative(abs(step), zone)

    async def volume_down(self, step: float = 0.1, zone: Zone | str | None = None) -> float:
        """Send volume down command."""
        return await self.set_volume_relative(-abs(step), zone)

    async def set_volume_relative(self, delta: float, zone: Zone | str | None = None) -> float:
        """Change the volume by the given signed delta, returning the new level."""
        _, resp = await self._conn.get_as_dict(
            "Playback/Volume",
            params={"Level": delta, "Relative": 1, **self._zone_params(zone)},
        )
        return float(resp.get("Level") or 0.0)

    async def set_volume_level(self, volume: float, zone: Zone | str | None = None) -> float:
        """Set volume level, range 0-1."""
        if volume < 0 or volume > 1:
            raise ValueError(f"{volume} not in range 0-1")
        _, resp = await self._conn.get_as_dict(
            "Playback/Volume", params={"Level": volume, **self._zone_params(zone)}
        )
        return float(resp.get("Level") or 0.0)

    async def mute(self, mute: bool, zone: Zone | str | None = None) -> bool:
        """Send (un)mute command."""
        _, resp = await self._conn.get_as_dict(
            "Playback/Mute",
            params={"Set": "1" if mute else "0", **self._zone_params(zone)},
        )
        return bool(int(resp.get("State") or 0))

    # ------------------------------------------------------------------
    # repeat / shuffle / loudness / dsp
    # ------------------------------------------------------------------

    async def get_repeat(self, zone: Zone | str | None = None) -> RepeatMode:
        """The current repeat mode."""
        _, resp = await self._conn.get_as_dict("Playback/Repeat", params=self._zone_params(zone))
        return _safe_enum(RepeatMode, resp.get("Mode"), RepeatMode.UNKNOWN)

    async def set_repeat(self, mode: RepeatMode | str, zone: Zone | str | None = None) -> bool:
        """Set the repeat mode."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/Repeat",
            params={"Mode": str(mode), **self._zone_params(zone)},
        )
        return ok

    async def get_shuffle(self, zone: Zone | str | None = None) -> ShuffleMode:
        """The current shuffle mode."""
        _, resp = await self._conn.get_as_dict("Playback/Shuffle", params=self._zone_params(zone))
        return _safe_enum(ShuffleMode, resp.get("Mode"), ShuffleMode.UNKNOWN)

    async def set_shuffle_mode(
        self, mode: ShuffleMode | str, zone: Zone | str | None = None
    ) -> bool:
        """Set the shuffle mode."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/Shuffle",
            params={"Mode": str(mode), **self._zone_params(zone)},
        )
        return ok

    async def set_shuffle(self, shuffle: bool, zone: Zone | str | None = None) -> bool:
        """Turn shuffle on or off."""
        return await self.set_shuffle_mode(ShuffleMode.ON if shuffle else ShuffleMode.OFF, zone)

    async def get_loudness(self, zone: Zone | str | None = None) -> bool:
        """Whether loudness is enabled."""
        _, resp = await self._conn.get_as_dict("DSP/Loudness", params=self._zone_params(zone))
        return _as_int(resp.get("Current"), 0) != 0

    async def set_loudness(self, on: bool, zone: Zone | str | None = None) -> bool:
        """Turn loudness on or off, returning the resulting state."""
        _, resp = await self._conn.get_as_dict(
            "DSP/Loudness",
            params={"Set": "1" if on else "0", **self._zone_params(zone)},
        )
        return _as_int(resp.get("Current"), 0) != 0

    async def load_dsp_preset(self, name: str, zone: Zone | str | None = None) -> bool:
        """Load the named DSP preset (MC 23.0.2+)."""
        if not name:
            raise ValueError("name is required")
        ok, _ = await self._conn.get_as_dict(
            "Playback/LoadDSPPreset",
            params={"Name": name, **self._zone_params(zone)},
        )
        return ok

    async def get_audio_path_direct(self, zone: Zone | str | None = None) -> AudioPath:
        """Whether the audio path of the given zone is direct."""

        def _parse(text: str) -> tuple[bool, AudioPath]:
            ok, values = to_dict(text)
            if not ok:
                return False, AudioPath()
            return True, AudioPath(values.get("Direct") == "yes")

        _, resp = await self._conn.get(
            "Playback/AudioPathDirect", _parse, params=self._zone_params(zone)
        )
        return resp

    async def get_audio_path(self, zone: Zone | str | None = None) -> AudioPath:
        """Get the audio path of the given zone."""

        def _parse(text: str) -> tuple[bool, AudioPath]:
            root = ElementTree.fromstring(text)
            if root.attrib.get("Status", "OK") != "OK":
                return False, AudioPath()
            paths: list[str] = []
            direct = False
            for child in root:
                name = child.attrib.get("Name", "")
                if name == "AudioPath":
                    continue
                if name == "Direct":
                    direct = child.text == "yes"
                if name.startswith("AudioPath"):
                    paths.append(child.text or "")
            return True, AudioPath(direct, paths)

        _, resp = await self._conn.get("Playback/AudioPath", _parse, params=self._zone_params(zone))
        return resp

    # ------------------------------------------------------------------
    # playlists & playback of content
    # ------------------------------------------------------------------

    @staticmethod
    def _play_mode_params(play_mode: PlayMode | str | None) -> dict:
        """Build the ``PlayMode`` param, if any."""
        return {"PlayMode": str(play_mode)} if play_mode else {}

    async def get_current_playlist(
        self, fields: list[str] | None = None, zone: Zone | str | None = None
    ) -> list[dict]:
        """Get the playing now list for the given zone."""
        fields = fields or DEFAULT_FILE_FIELDS
        _, resp = await self._conn.get_as_json_list(
            "Playback/Playlist",
            params={
                "Fields": ",".join(fields),
                "Action": "JSON",
                **self._zone_params(zone),
            },
        )
        if resp:
            await self._ensure_token()
            for e in resp:
                if "Key" in e:
                    e["ImageURL"] = self._file_image_url(int(e["Key"]), "small", "png")
        return resp

    async def clear_playlist(self, zone: Zone | str | None = None) -> bool:
        """Clear the playing now list."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/ClearPlaylist", params=self._zone_params(zone)
        )
        return ok

    async def get_playlists(self) -> list[Playlist]:
        """The stored playlists."""

        def _parse(text: str) -> tuple[bool, list[Playlist]]:
            root = ElementTree.fromstring(text)
            if root.attrib.get("Status", "OK") != "OK":
                return False, []
            result: list[Playlist] = []
            for item in root:
                values: dict[str, str] = {k: v for k, v in item.attrib.items() if k != "Name"}
                for child in item:
                    name = child.attrib.get("Name")
                    if name:
                        values[name] = child.text or ""
                if "Name" in item.attrib and "Name" not in values:
                    values["Name"] = item.attrib["Name"]
                if not values:
                    continue
                result.append(
                    Playlist(
                        values.get("ID", ""),
                        values.get("Name", ""),
                        values.get("Path", ""),
                        values.get("Type", ""),
                    )
                )
            return True, result

        ok, resp = await self._conn.get("Playlists/List", _parse)
        return resp if ok else []

    async def get_playlist_files(
        self, playlist_id: str, fields: list[str] | None = None
    ) -> list[dict]:
        """The files in the given stored playlist."""
        if not playlist_id:
            raise ValueError("playlist_id is required")
        field_list = ",".join(DEFAULT_FILE_FIELDS + (fields or []))
        _, resp = await self._conn.get_as_json_list(
            "Playlist/Files",
            params={
                "Playlist": playlist_id,
                "Action": "JSON",
                "Fields": field_list,
            },
        )
        return resp

    async def play_playlist(
        self,
        playlist_id: str,
        playlist_type: str = "Path",
        zone: Zone | str | None = None,
        play_mode: PlayMode | str | None = None,
    ) -> bool:
        """Play the given playlist."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/PlayPlaylist",
            params={
                "Playlist": playlist_id,
                "PlaylistType": playlist_type,
                **self._play_mode_params(play_mode),
                **self._zone_params(zone),
            },
        )
        return ok

    async def play_file(
        self,
        file: str,
        zone: Zone | str | None = None,
        play_mode: PlayMode | str | None = None,
    ) -> bool:
        """Play the given file."""
        ok, _ = await self._conn.get_as_dict(
            "Playback/PlayByFilename",
            params={
                "Filenames": file,
                **self._play_mode_params(play_mode),
                **self._zone_params(zone),
            },
        )
        return ok

    async def play_item(
        self,
        item: str,
        zone: Zone | str | None = None,
        play_mode: PlayMode | str | None = None,
    ) -> bool:
        """Play the given library item."""
        ok, _ = await self._conn.get_as_dict(
            "File/GetInfo",
            params={
                "File": item,
                "Action": "Play",
                **self._play_mode_params(play_mode),
                **self._zone_params(zone),
            },
        )
        return ok

    # ------------------------------------------------------------------
    # browse & search
    # ------------------------------------------------------------------

    async def browse_children(self, base_id: int = -1) -> dict[str, str | None]:
        """Get the nodes under the given browse id."""
        _, resp = await self._conn.get_as_dict(
            "Browse/Children",
            params={"Version": 2, "ErrorOnMissing": 0, "ID": base_id},
        )
        return resp

    async def browse_files(self, base_id: int = -1, fields: list[str] | None = None) -> list[dict]:
        """Get the files under the given browse id."""
        field_list = ",".join(DEFAULT_FILE_FIELDS + (fields or []))
        _, resp = await self._conn.get_as_json_list(
            "Browse/Files",
            params={"ID": base_id, "Action": "JSON", "Fields": field_list},
        )
        return resp

    async def play_browse_files(
        self,
        base_id: int = -1,
        zone: Zone | str | None = None,
        play_next: bool | None = None,
        play_mode: PlayMode | str | None = None,
    ) -> dict[str, str | None]:
        """Play the files under the given browse id."""
        if play_mode is None and play_next is not None:
            play_mode = PlayMode.NEXT_TO_PLAY if play_next else PlayMode.ADD
        params = {
            "ID": base_id,
            "Action": "Play",
            **self._play_mode_params(play_mode),
            **self._zone_params(zone),
        }
        _, resp = await self._conn.get_as_dict("Browse/Files", params=params)
        return resp

    async def get_browse_rules(self, view_type: str = "Remote") -> list[BrowseRule]:
        """Get the configured BrowseRule list (MC 32.0.6+)."""

        def _parse(text: str) -> tuple[bool, list[BrowseRule]]:
            root = ElementTree.fromstring(text)
            if root.attrib.get("Status", "OK") != "OK":
                return False, []
            return True, [
                BrowseRule(
                    child.attrib.get("Name", ""),
                    child.attrib.get("Categories", ""),
                    child.attrib.get("Search", ""),
                )
                for child in root
            ]

        try:
            _, resp = await self._conn.get("Browse/Rules", _parse, params={"Type": view_type})
        except UnsupportedRequestError:
            return []
        return resp

    async def search_files(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Search the library, returning the matching files."""
        if not query:
            raise ValueError("No query supplied")
        field_list = ",".join(DEFAULT_FILE_FIELDS + (fields or []))
        params = {"Query": query, "Action": "JSON", "Fields": field_list}
        if limit is not None:
            # Files/Search supports a server side Limit, avoiding a full library payload.
            params["Limit"] = str(limit)
        _, resp = await self._conn.get_as_json_list("Files/Search", params=params)
        return resp[:limit] if limit is not None else resp

    async def play_search(
        self,
        query: str,
        zone: Zone | str | None = None,
        play_next: bool | None = None,
        play_mode: PlayMode | str | None = None,
    ) -> dict[str, str | None]:
        """Play the files located by the query string."""
        if not query:
            raise ValueError("No query supplied")
        if play_mode is None and play_next is not None:
            play_mode = PlayMode.NEXT_TO_PLAY if play_next else PlayMode.ADD
        params = {
            "Query": query,
            "Action": "Play",
            **self._play_mode_params(play_mode),
            **self._zone_params(zone),
        }
        _, resp = await self._conn.get_as_dict("Files/Search", params=params)
        return resp

    # ------------------------------------------------------------------
    # control
    # ------------------------------------------------------------------

    async def send_key_presses(
        self, keys: Sequence[KeyCommand | str] | str, focus: bool = True
    ) -> bool:
        """Send a sequence of key presses.

        A plain ``str`` is sent verbatim; a sequence is joined with ``;``.
        """
        if not keys:
            raise ValueError("No keys")
        if isinstance(keys, str):
            key_param = keys
        else:
            key_param = ";".join(str(k.value) if isinstance(k, Enum) else str(k) for k in keys if k)
        if not key_param:
            raise ValueError("No keys")
        ok, _ = await self._conn.get_as_dict(
            "Control/Key", params={"Key": key_param, "Focus": 1 if focus else 0}
        )
        return ok

    async def send_mcc(
        self,
        command: int,
        param: int | None = None,
        zone: Zone | str | None = None,
        block: bool = True,
    ) -> bool:
        """Send the given MCC command."""
        params = {
            "Command": int(command),
            "Block": 1 if block else 0,
            **self._zone_params(zone),
        }
        if param is not None:
            params["Parameter"] = param
        ok, _ = await self._conn.get_as_dict("Control/MCC", params=params)
        return ok

    async def run_command_line(self, arguments: str) -> bool:
        """Run the given command line arguments against the server."""
        if not arguments:
            raise ValueError("arguments are required")
        ok, _ = await self._conn.get_as_dict("Control/CommandLine", params={"Arguments": arguments})
        return ok
