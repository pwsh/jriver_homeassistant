---
title: Entities
nav_order: 5
---

# Entities

## Devices and naming

One device represents the server. In per zone mode each selected zone gets a device too, with
the server as its `via_device`.

| Device | Name | Model |
| --- | --- | --- |
| Server | The name from the config entry, or the host if it was left blank | `Media Center (<platform>)` |
| Zone | `<server name> <zone name>` | `Zone` |

Every entity sets `has_entity_name`, so Home Assistant builds the entity id from the device
name plus the entity name. The media player and the remote have no entity name of their own,
so they take the device name directly. Using a server named `Music Room` and a zone named
`Player` as the example:

| Entity | Entity id |
| --- | --- |
| Server media player (single device mode) | `media_player.music_room` |
| Remote | `remote.music_room` |
| Active zone | `sensor.music_room_active_zone` |
| UI mode | `sensor.music_room_ui_mode` |
| Version | `sensor.music_room_version` |
| Zone media player (per zone mode) | `media_player.music_room_player` |
| Playing now | `sensor.music_room_player_playing_now` |
| Playing now list | `sensor.music_room_player_playing_now_list` |
| Audio direct | `binary_sensor.music_room_player_audio_direct` |

Unique ids are `<entry unique id>_<kind>` for server entities and
`<entry unique id>_zone_<zone id>_<kind>` for zone entities, where the entry unique id is the
Media Center access key when the server reports one and `host:port` otherwise. Zone entities
are keyed by zone **id**, so renaming a zone in Media Center keeps its history.

## Per server

| Entity | Platform | Device class | Category | Enabled by default | State | Attributes |
| --- | --- | --- | --- | --- | --- | --- |
| Media player | `media_player` | — | — | yes (single device mode only) | Playback state of the active zone | see below |
| Remote | `remote` | — | — | yes | `on` when a Media Center window is visible (UI mode above `no_ui`) | — |
| Active zone | `sensor` | `enum` | — | yes | The active zone's name, or unknown if it is not in the current zone list | `id`: the active zone id |
| UI mode | `sensor` | `enum` | diagnostic | yes | One of `unknown`, `no_ui`, `standard`, `mini`, `display`, `theater`, `cover`, `count` | `id`: the raw numeric mode |
| Version | `sensor` | — | diagnostic | **no** | The Media Center version string | `platform`, `library_version`, `product_version` |

## Per zone

Created for every zone on the configured zone list, or for every zone when the list is empty.
Note that the zone media player only exists in per zone mode, while the three sensors are
created either way.

| Entity | Platform | Device class | Category | Enabled by default | State | Attributes |
| --- | --- | --- | --- | --- | --- | --- |
| Media player | `media_player` | — | — | yes (per zone mode only) | Playback state of that zone | see below |
| Playing now | `sensor` | — | — | yes | The name of the playing file | see below |
| Playing now list | `sensor` (unit `tracks`, measurement) | — | — | yes | Number of entries in the playing now list | `next_up` |
| Audio direct | `binary_sensor` | — | diagnostic | yes | `on` when the audio path bypasses DSP | `audio_path`: the DSP chain as a list |

An entity becomes unavailable when the coordinator's last update failed, or when the zone it
belongs to no longer exists on the server.

### Playing now attributes

Everything `Playback/Info` reports, minus the values that tick every second (`position_ms`,
`duration_ms` and the elapsed time display), which belong on the media player where the
recorder handles them efficiently.

`name`, `zone_id`, `zone_name`, `playback_state`, `volume`, `muted`, `live_input`, `artist`,
`album`, `album_artist`, `series`, `season`, `episode`, `media_type`, `media_sub_type`,
`remaining_time_display`, `total_time_display`, `position_display`, `volume_display`,
`playing_now_position`, `playing_now_tracks`, `playing_now_position_display`, `bitrate`,
`bitdepth`, `sample_rate`, `channels`, `chapter`, `lip_sync_adjustment_ms`, `rating`,
`linked_zones`, plus `is_active` (true when this is the active zone) and any
[extra fields]({{ site.baseurl }}/options/#step-5-extra-fields) you configured.

`Playback/Info` omits `ZoneName` for the local, non-DLNA zone; the sensor falls back to the
configured zone name.

### Playing now list attributes

`next_up` holds up to ten upcoming entries, each `{key, name, artist, album}`, starting one
past the current playing now position. The full list is not a state attribute — a long
playlist would blow past the recorder's attribute size limit. Use
[`jriver.get_playlist`]({{ site.baseurl }}/actions/#jrivergetplaylist) instead. The
coordinator itself keeps at most 500 entries per zone.

## Media player

### Supported features

Always: `PAUSE`, `PLAY`, `STOP`, `SEEK`, `VOLUME_SET`, `VOLUME_MUTE`, `VOLUME_STEP`,
`PREVIOUS_TRACK`, `NEXT_TRACK`, `PLAY_MEDIA`, `BROWSE_MEDIA`, `CLEAR_PLAYLIST`, `SHUFFLE_SET`,
`REPEAT_SET`, `TURN_ON`, `TURN_OFF`.

| Feature | When |
| --- | --- |
| `SELECT_SOURCE` | Single device mode only |
| `GROUPING` | Per zone mode only |
| `SELECT_SOUND_MODE` | Only when DSP presets are configured in the options |

### State mapping

| Media Center | Home Assistant |
| --- | --- |
| No playback info for the zone | `off` |
| `STOPPED`, `WAITING` | `idle` |
| `PAUSED` | `paused` |
| `PLAYING` | `playing` |
| anything else | `idle` |

### Media metadata

`media_content_id` is the file key as a string, `media_content_type` is the Home Assistant
media type translated from Media Center's media type and sub type. Both are `None` when the
zone has no file loaded (file key `-1`), as are the title, duration, position and artwork.

Duration and position are also `None` for a live input. Media Center keeps reporting the
previous track's duration for a zone with nothing loaded, so the integration reports no media
at all rather than a stale value.

Artwork is fetched through Home Assistant using an authenticated MCWS token, so it works from
outside your LAN. `media_image_remotely_accessible` is false.

### Repeat and shuffle

| Media Center repeat | Home Assistant |
| --- | --- |
| `Off`, `Stop` | `off` |
| `Playlist` | `all` |
| `Track` | `one` |

Setting `all` maps to `Playlist`, `one` to `Track` and anything else to `Off`. Shuffle is
`true` when Media Center reports `On` or `Reshuffle`.

`Playback/Repeat` and `Playback/Shuffle` do not exist on every Media Center version. When the
server rejects them the coordinator stops asking and both are reported as unknown.

### Source list

In single device mode `source` is the active zone's name and `source_list` is every zone name
the server reports — not just the configured allowlist. Selecting a source calls
`Playback/SetZone`. In per zone mode both are `None`.

### Grouping

In per zone mode `group_members` starts with this entity and adds the media player entity id
of each zone Media Center reports in `LinkedZones`.

`Playback/Info` reports linked zones as **names**, so a linked zone cannot be resolved when
its name is duplicated, or when it has no media player entity (it is not in the configured
zone list, or the integration is in single device mode).

### Sound modes

`sound_mode_list` is the DSP preset list from the options, or `None` when it is empty. The
`sound_mode` attribute reflects the last preset selected through
`media_player.select_sound_mode` in this Home Assistant run; it is not read back from Media
Center.

### Extra state attributes

| Attribute | Notes |
| --- | --- |
| `zone_name` | Falls back to the configured zone name for the local zone |
| `zone_id` | |
| `linked_zones` | Zone **names**, as reported by Media Center |
| `playing_now_position` | Index of the current entry in the playing now list |
| `playing_now_tracks` | Length of the playing now list |
| `next_file_key` | `None` when Media Center reports `-1` |
| `live_input` | |
| `audio_direct` | Only when the audio path is known |
| `audio_path` | The DSP chain, only when the audio path is known |
| `bitrate`, `sample_rate`, `bitdepth`, `channels` | Only when Media Center reports them |

Any configured extra fields are merged in on top.
