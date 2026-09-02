# JRiver Media Center for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that controls
[JRiver Media Center](https://jriver.com/) over its
[Media Network web service](https://wiki.jriver.com/index.php/Web_Service_Interface) (MCWS).

It gives you a media player per Media Center zone (or one for the whole server), a remote for
the Media Center user interface, sensors describing what is playing, library browsing inside the
Home Assistant media browser, and a set of actions for playlists, searches, DSP presets and
sleep timers.

**Documentation:** <https://pwsh.github.io/jriver_homeassistant/>

**Fork:** this branch is a rework maintained at
[pwsh/jriver_homeassistant](https://github.com/pwsh/jriver_homeassistant); upstream is
[3ll3d00d/jriver_homeassistant](https://github.com/3ll3d00d/jriver_homeassistant).

Version 2.0 vendors its own MCWS client, so the integration has **no external Python
requirements**.

---

## Requirements

- JRiver Media Center 24 or newer (32.0.6+ recommended: browse views are then discovered
  automatically).
- **Options > Media Network > "Use Media Network to share this library and enable DLNA"** enabled.
- Home Assistant 2026.1 or newer.
- Optional: the [Wake on LAN](https://www.home-assistant.io/integrations/wake_on_lan/)
  integration if you want to use the `jriver.wake` action.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=3ll3d00d&repository=jriver_homeassistant)

Add this repository to HACS as an integration, install it, then restart Home Assistant.

### Manual

Copy the whole `custom_components/jriver/` directory (including the `mcws/` subdirectory) into
your `config/custom_components/` directory and restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jriver)

### 1. Server location

Enter either the access key shown in Options > Media Network, or the host and port that Media
Center listens on. Media Center must be running and reachable from Home Assistant.

![Server Location](img/config_1.png?raw=true "Server Location")

The config entry is identified by the server's access key when one is available, so the entry
survives a change of IP address. Otherwise `host:port` is used.

### 2. Authentication

Shown only when Media Center requires authentication. The credentials are the ones in
Options > Media Network > Authentication.

![Authentication](img/config_2.png?raw=true "Authentication")

If the credentials later stop working, Home Assistant starts a reauthentication flow rather
than silently failing.

### 3. Wake on LAN

Optionally record the MAC addresses of the machine running Media Center so the `jriver.wake`
action can send a magic packet.

### 4. Browse paths (MC < 32.0.6 only)

Media Center exposes its remote views over MCWS from 32.0.6 onwards. On older versions the views
have to be entered by hand.

![Browse Paths](img/config_3.png?raw=true "Browse Paths")

Each entry is a pipe delimited pair of comma separated lists: the path names on the left and the
category (library field) names on the right, for example
`Audio,Artist|Album Artist (auto),Album`.

### 5. Zones

Shown only when Media Center has more than one zone. There are two topologies:

1. **one device for the whole server** — the media player follows the active zone and gains a
   source selector listing the zones (switching source calls `Playback/SetZone`);
2. **one device per zone** — each selected zone gets its own media player, remote grouping
   (zone linking) is available and per-zone sensors are created.

![SingleOrMulti](img/config_4.png?raw=true)

![Zone Selection](img/config_5.png?raw=true "Zone Selection")

### 6. Playback fields

Any library field selected here is requested with every `Playback/Info` call and exposed as an
attribute on the playing now sensors and the media player.

## Options

Everything below can be changed from the integration's **Configure** button; the entry reloads
automatically.

| Option | Default | Notes |
| --- | --- | --- |
| Poll interval | 2 s | Seconds between updates while a zone is playing. Idle zones are polled 3× less often. |
| Turn off behaviour | Stop playback | `stop` calls `Playback/StopAll`. `close_program` additionally sends MCC 20007, which **closes Media Center** and is known to hang the process on Linux. |
| DSP presets | none | Names of DSP presets. When set, the media player gains `select_sound_mode`. |
| Zones | all | Whether zones are separate devices and which zones to include. Zones outside the list are not polled. |
| Browse paths | discovered | Only asked for on Media Center < 32.0.6. |
| MAC addresses / wake on LAN | off | Used by `jriver.wake`. |
| Extra fields | none | Additional library fields to expose as attributes. |

The **Reconfigure** button moves an existing entry to a new host, port or name without losing its
history; it refuses to point the entry at a different server.

## Entities

### Per server

| Entity | Platform | State | Attributes |
| --- | --- | --- | --- |
| Media player (single device mode only) | `media_player` | Playback state of the active zone | see below |
| Remote | `remote` | `on` when a Media Center window is visible | |
| Active zone | `sensor` (enum) | Name of the active zone | `id` |
| UI mode | `sensor` (enum, diagnostic) | `standard`, `theater`, `no_ui`, … | `id` |
| Version | `sensor` (diagnostic, disabled by default) | Media Center version | `platform`, `library_version`, `product_version` |

### Per zone

| Entity | Platform | State | Attributes |
| --- | --- | --- | --- |
| Media player (per zone mode only) | `media_player` | Playback state of that zone | see below |
| Playing now | `sensor` | Name of the playing file | `artist`, `album`, `album_artist`, `series`, `season`, `episode`, `media_type`, `media_sub_type`, `playback_state`, `volume`, `muted`, `live_input`, `is_active`, `linked_zones`, plus any configured extra fields |
| Playing now list | `sensor` (`tracks`) | Number of entries in the playing now list | `next_up`: up to 10 upcoming `{key, name, artist, album}` |
| Audio direct | `binary_sensor` (diagnostic) | `on` when playback bypasses DSP | `audio_path`: the DSP chain |

Position and duration are deliberately **not** playing-now sensor attributes; they change every
second and belong on the media player, which the recorder handles efficiently.

### Media player

Supported features: play, pause, stop, seek, volume set/mute/step, previous/next track,
play media, browse media, clear playlist, shuffle, repeat, turn on, turn off, plus
`select_source` (single device mode), `grouping` (per zone mode) and `select_sound_mode`
(when DSP presets are configured).

Extra attributes: `zone_name`, `zone_id`, `linked_zones` (the *names* of the zones this one is
linked to, as reported by Media Center; `group_members` holds the matching entity ids),
`playing_now_position`,
`playing_now_tracks`, `next_file_key`, `live_input`, `audio_direct`, `audio_path`, and
`bitrate` / `sample_rate` / `bitdepth` / `channels` when Media Center reports them.

## Media browsing

The media browser shows the Media Center remote views (Audio, Video, Playlists, Playing Now …)
alongside any Home Assistant [media source](https://www.home-assistant.io/integrations/media_source/).
Artwork is fetched through Home Assistant using an authenticated MCWS token, so it works from
outside your LAN.

## Playing media

```yaml
# play a library item by key (as produced by the media browser)
action: media_player.play_media
target:
  entity_id: media_player.phosphorus
data:
  media_content_type: music
  media_content_id: "K|123456"

# play a search expression
action: media_player.play_media
target:
  entity_id: media_player.phosphorus
data:
  media_content_type: query
  media_content_id: "[Album Artist (auto)]=[AIR] ~sort=[Date],[Album],[Track #]"

# play a stored playlist
action: media_player.play_media
target:
  entity_id: media_player.phosphorus
data:
  media_content_type: playlist
  media_content_id: 'Alarms\Morning\Wakeup'

# append a URL to the playing now list instead of replacing it
action: media_player.play_media
target:
  entity_id: media_player.phosphorus
data:
  media_content_type: url
  media_content_id: http://stream.example.com/radio.flac
  enqueue: add
```

`enqueue` accepts `replace` (default, clears the playing now list first), `add`, `next` and
`play`.

## Grouping and zone linking

In per zone mode the media players support the standard grouping actions, which map onto
`Playback/LinkZones` and `Playback/UnlinkZones`:

```yaml
action: media_player.join
target:
  entity_id: media_player.phosphorus_player
data:
  group_members:
    - media_player.phosphorus_office
```

`media_player.unjoin` unlinks the targeted zone.

## DSP presets

List your preset names in the integration options and they become sound modes:

```yaml
action: media_player.select_sound_mode
target:
  entity_id: media_player.phosphorus
data:
  sound_mode: Night
```

The `jriver.load_dsp_preset` action does the same thing for a preset that is not in the options
list, and can target a named zone.

## Actions

### `jriver.play_search`

```yaml
action: jriver.play_search
target:
  entity_id: media_player.phosphorus
data:
  query: "[Album Artist (auto)]=[AIR]"
  play_mode: add   # replace | add | next
```

### `jriver.append_search_results_to_playlist`

```yaml
action: jriver.append_search_results_to_playlist
target:
  entity_id: media_player.phosphorus
data:
  query: "[Album Artist (auto)]=[AIR]"
```

### `jriver.play_playlist`

```yaml
action: jriver.play_playlist
target:
  entity_id: media_player.phosphorus
data:
  playlist_path: 'Alarms\Morning\Wakeup'
```

### `jriver.seek_relative`

Moves relative to the current position (clamped to the file duration).

```yaml
action: jriver.seek_relative
target:
  entity_id: media_player.phosphorus
data:
  seek_duration: -30
```

### `jriver.adjust_volume`

```yaml
action: jriver.adjust_volume
target:
  entity_id: media_player.phosphorus
data:
  delta: -5
```

### `jriver.activate_zone`

```yaml
action: jriver.activate_zone
target:
  entity_id: remote.phosphorus
data:
  zone_name: Office
```

### `jriver.send_mcc`

Exposes `MCWS/v1/Control/MCC`.

```yaml
action: jriver.send_mcc
target:
  entity_id: remote.phosphorus
data:
  command: 22009
  parameter: 3
  block: true
```

### `jriver.stop_after`

A sleep timer. Supply exactly one of `minutes`, `tracks` or `current`.

```yaml
action: jriver.stop_after
target:
  entity_id: remote.phosphorus
data:
  minutes: 45
```

### `jriver.load_dsp_preset`

```yaml
action: jriver.load_dsp_preset
target:
  entity_id: remote.phosphorus
data:
  preset: Night
  zone_name: Player
```

### `jriver.wake`

Sends a wake on LAN magic packet to the MAC addresses recorded for the server. Because Home
Assistant will not call an action on an unavailable entity, this is a **domain** action that
takes an entity or device id rather than an entity target.

```yaml
action: jriver.wake
data:
  entity_id: remote.phosphorus
```

### `jriver.get_playlist` (returns a response)

```yaml
action: jriver.get_playlist
data:
  entity_id: media_player.phosphorus
response_variable: playing_now
```

Returns `{ "zone": "Player", "entries": [ … ] }`. The playing now list is exposed this way
rather than as a state attribute so it cannot overflow the recorder's attribute size limit.

### `jriver.search` (returns a response)

```yaml
action: jriver.search
data:
  entity_id: media_player.phosphorus
  query: "[Album Artist (auto)]=[AIR]"
  fields: [Name, Artist, Album]
  limit: 50
response_variable: matches
```

## Power behaviour

- `turn_on` sends MCC 22009 to show the standard view. It cannot start Media Center if the
  machine is off; use `jriver.wake` for that.
- `turn_off` calls `Playback/StopAll`. If you set the turn off behaviour option to
  **close_program** it also sends MCC 20007.

> **Warning (Linux)** — MCC 20007 closes Media Center entirely and, on some headless Linux
> installs, leaves the process hung so that MCWS never comes back. This is why `stop` is the
> default and closing the program is opt in.

## Known limitations

- Media Center has no push interface, so the integration polls. The interval adapts (fast while
  playing, slower when idle) but there is always some latency.
- `Playback/Repeat` and `Playback/Shuffle` are not available on every Media Center version. When
  the server rejects them the integration stops asking and the repeat/shuffle state is reported
  as unknown.
- Browse views are only discovered automatically on Media Center 32.0.6 and newer.
- Playlists longer than 500 entries are truncated in the coordinator; use `jriver.get_playlist`
  for the full list.
- Disabling a zone's device in Home Assistant does not stop polling for it; remove the zone from
  the options instead.
- `Playback/Info` reports `LinkedZones` as zone names, so `group_members` cannot resolve a linked
  zone whose name is duplicated or that is not in the configured zone list.
- Media Center keeps reporting the previous track's duration for a zone that has nothing loaded.
  The integration reports no media at all for such a zone rather than a stale duration.

## Removing the integration

Delete the config entry from Settings > Devices & Services > JRiver Media Center. All devices,
entities and history are removed with it. If you installed manually, also delete
`config/custom_components/jriver/`. Nothing is written to Media Center itself, so no cleanup is
needed there.

## Development

```bash
uv venv
. .venv/bin/activate
uv pip install -r requirements-dev.txt

pytest -q
ruff check custom_components tests
ruff format custom_components tests

# keep translations/en.json in sync after editing strings.json
python scripts/expand_strings.py
python scripts/check_translations.py
```

See [docs/architecture.md](docs/architecture.md) for how the integration is put together.

## Credits

The vendored MCWS client in `custom_components/jriver/mcws/` is derived from
[hamcws](https://github.com/3ll3d00d/hamcws) (MIT).
