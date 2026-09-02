"""Constants for the JRiver Media Center integration."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

DOMAIN: Final = "jriver"

# config entry data keys (in addition to the homeassistant.const ones)
CONF_BROWSE_PATHS: Final = "browse_paths"
CONF_DEVICE_PER_ZONE: Final = "per_zone"
CONF_DEVICE_ZONES: Final = "device_zones"
CONF_EXTRA_FIELDS: Final = "extra_fields"
CONF_USE_WOL: Final = "use_wol"
CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_TURN_OFF_BEHAVIOUR: Final = "turn_off_behaviour"
CONF_DSP_PRESETS: Final = "dsp_presets"

DEFAULT_PORT: Final = 52199
DEFAULT_SSL: Final = False
DEFAULT_TIMEOUT: Final = 10
DEFAULT_DEVICE_PER_ZONE: Final = False
DEFAULT_POLL_INTERVAL: Final = 2
MIN_POLL_INTERVAL: Final = 1
MAX_POLL_INTERVAL: Final = 60
IDLE_POLL_MULTIPLIER: Final = 3

DEFAULT_BROWSE_PATHS: Final = [
    "Audio,Artist|Album Artist (auto),Album",
    "Audio,Album|Album",
    "Audio,Recent|Album",
    "Audio,Genre|Genre,Album Artist (auto),Album",
    "Audio,Composer|Composer,Album",
    "Audio,Podcast",
    "Video,Movies",
    "Video,Shows|Series,Season",
    "Video,Music|Artist,Album",
]

# how often the cheap Alive call is made (seconds)
ALIVE_REFRESH_INTERVAL: Final = 300
# how often browse rules are reloaded (seconds)
BROWSE_PATHS_REFRESH_INTERVAL: Final = 900

# fields requested when loading the playing now list
PLAYLIST_FIELDS: Final = ["Key", "Name", "Artist", "Album", "Duration", "Media Type"]
# upper bound on the number of playing now entries held in memory
MAX_PLAYLIST_ENTRIES: Final = 500
# how many upcoming entries are exposed as an attribute on the playlist sensor
NEXT_UP_COUNT: Final = 10


class TurnOffBehaviour(StrEnum):
    """What media_player.turn_off should do."""

    STOP = "stop"
    CLOSE_PROGRAM = "close_program"


DEFAULT_TURN_OFF_BEHAVIOUR: Final = TurnOffBehaviour.STOP

# entity kinds, used to build unique ids
KIND_MEDIA_PLAYER: Final = "media_player"
KIND_REMOTE: Final = "remote"
KIND_ACTIVE_ZONE: Final = "active_zone"
KIND_UI_MODE: Final = "ui_mode"
KIND_VERSION: Final = "version"
KIND_PLAYING_NOW: Final = "playing_now"
KIND_PLAYLIST: Final = "playlist"
KIND_AUDIO_DIRECT: Final = "audio_direct"

# services
SERVICE_WAKE: Final = "wake"
SERVICE_GET_PLAYLIST: Final = "get_playlist"
SERVICE_SEARCH: Final = "search"
SERVICE_ADD_SEARCH: Final = "append_search_results_to_playlist"
SERVICE_PLAY_PLAYLIST: Final = "play_playlist"
SERVICE_PLAY_SEARCH: Final = "play_search"
SERVICE_SEEK_RELATIVE: Final = "seek_relative"
SERVICE_ADJUST_VOLUME: Final = "adjust_volume"
SERVICE_ACTIVATE_ZONE: Final = "activate_zone"
SERVICE_SEND_MCC: Final = "send_mcc"
SERVICE_STOP_AFTER: Final = "stop_after"
SERVICE_LOAD_DSP_PRESET: Final = "load_dsp_preset"

# service attributes
ATTR_PLAYLIST_PATH: Final = "playlist_path"
ATTR_QUERY: Final = "query"
ATTR_PLAY_MODE: Final = "play_mode"
ATTR_SEEK_DURATION: Final = "seek_duration"
ATTR_DELTA: Final = "delta"
ATTR_ZONE_NAME: Final = "zone_name"
ATTR_MCC_COMMAND: Final = "command"
ATTR_MCC_PARAMETER: Final = "parameter"
ATTR_MCC_BLOCK: Final = "block"
ATTR_MINUTES: Final = "minutes"
ATTR_TRACKS: Final = "tracks"
ATTR_CURRENT: Final = "current"
ATTR_PRESET: Final = "preset"
ATTR_FIELDS: Final = "fields"
ATTR_LIMIT: Final = "limit"
