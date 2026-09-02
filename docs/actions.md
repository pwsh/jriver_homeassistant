---
title: Actions
nav_order: 6
---

# Actions

The integration registers eleven `jriver.*` actions. Nine are entity actions targeted at a
media player or a remote; three are domain actions that take an entity or device id as a
field, because Home Assistant will not call an entity action on an unavailable entity.

| Action | Target | Response |
| --- | --- | --- |
| `jriver.play_search` | `media_player` entity | no |
| `jriver.append_search_results_to_playlist` | `media_player` entity | no |
| `jriver.play_playlist` | `media_player` entity | no |
| `jriver.seek_relative` | `media_player` entity | no |
| `jriver.adjust_volume` | `media_player` entity | no |
| `jriver.activate_zone` | `remote` entity | no |
| `jriver.send_mcc` | `remote` entity | no |
| `jriver.stop_after` | `remote` entity | no |
| `jriver.load_dsp_preset` | `remote` entity | no |
| `jriver.wake` | `entity_id` and/or `device_id` field | no |
| `jriver.get_playlist` | `entity_id` field | yes |
| `jriver.search` | `entity_id` field | yes |

Failures raise `HomeAssistantError` with a translated message, so they surface in the UI and
stop the automation rather than being logged and swallowed.

---

## `jriver.play_search`

Plays the results of a library search in the targeted zone.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `query` | yes | | A [JRiver search expression](https://wiki.jriver.com/index.php/Search_Language) |
| `play_mode` | no | `replace` | `replace`, `add` or `next` |

`replace` clears the playing now list first. `add` appends, `next` queues after the current
file.

```yaml
action: jriver.play_search
target:
  entity_id: media_player.music_room
data:
  query: "[Album Artist (auto)]=[AIR] ~sort=[Date],[Album],[Track #]"
  play_mode: replace
```

## `jriver.append_search_results_to_playlist`

Appends the results of a search to the end of the playing now list. Equivalent to
`jriver.play_search` with `play_mode: add`.

| Field | Required | Notes |
| --- | --- | --- |
| `query` | yes | A JRiver search expression |

```yaml
action: jriver.append_search_results_to_playlist
target:
  entity_id: media_player.music_room
data:
  query: "[Album Artist (auto)]=[AIR]"
```

## `jriver.play_playlist`

Plays a stored playlist. The path is the Media Center playlist path, with backslashes
separating the folders.

| Field | Required | Notes |
| --- | --- | --- |
| `playlist_path` | yes | Rejected when blank or whitespace |

```yaml
action: jriver.play_playlist
target:
  entity_id: media_player.music_room
data:
  playlist_path: 'Alarms\Morning\Wakeup'
```

## `jriver.seek_relative`

Moves forward or backward from the current position. The result is clamped to zero at the
bottom and to the file's duration at the top. Fails if the zone has nothing loaded.

| Field | Required | Notes |
| --- | --- | --- |
| `seek_duration` | yes | Seconds, −3600 to 3600. Negative seeks backwards. |

```yaml
action: jriver.seek_relative
target:
  entity_id: media_player.music_room
data:
  seek_duration: -30
```

## `jriver.adjust_volume`

Changes the volume by a signed percentage of full scale.

| Field | Required | Notes |
| --- | --- | --- |
| `delta` | yes | Integer, −100 to 100 |

```yaml
action: jriver.adjust_volume
target:
  entity_id: media_player.music_room
data:
  delta: -5
```

## `jriver.activate_zone`

Makes the named zone the active zone. The name is checked against the zones the server
currently reports.

| Field | Required | Notes |
| --- | --- | --- |
| `zone_name` | yes | A Media Center zone name |

```yaml
action: jriver.activate_zone
target:
  entity_id: remote.music_room
data:
  zone_name: Office
```

## `jriver.send_mcc`

Sends a raw [Media Center Core Command](https://wiki.jriver.com/index.php/Media_Center_Core_Commands)
via `MCWS/v1/Control/MCC`.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `command` | yes | | Integer, 10000 to 40000 |
| `parameter` | no | | Integer |
| `block` | no | `true` | Wait for the command to complete |
| `zone_name` | no | | Target a specific zone |

```yaml
action: jriver.send_mcc
target:
  entity_id: remote.music_room
data:
  command: 22009
  parameter: 3
  block: true
```

## `jriver.stop_after`

A sleep timer. Supply exactly one of the three fields; the schema treats them as mutually
exclusive and the action fails if none is given. It always targets the **active** zone.

| Field | Required | Notes |
| --- | --- | --- |
| `minutes` | one of | 1 to 1440. Sets a stop-after-delay. |
| `tracks` | one of | 1 to 100. Sends MCC 10068. |
| `current` | one of | `true` stops at the end of the current file. |

```yaml
action: jriver.stop_after
target:
  entity_id: remote.music_room
data:
  minutes: 45
```

## `jriver.load_dsp_preset`

Loads a DSP preset by name. Unlike `media_player.select_sound_mode`, the name does not have
to be listed in the options, and a zone can be named explicitly.

| Field | Required | Notes |
| --- | --- | --- |
| `preset` | yes | The preset name as it exists in Media Center |
| `zone_name` | no | Defaults to the server's own target zone |

```yaml
action: jriver.load_dsp_preset
target:
  entity_id: remote.music_room
data:
  preset: Night
  zone_name: Player
```

## `jriver.wake`

Sends a wake on LAN magic packet to every MAC address configured for the resolved server(s).

| Field | Required | Notes |
| --- | --- | --- |
| `entity_id` | one of | One or more JRiver entities |
| `device_id` | one of | One or more JRiver devices |

At least one of the two must be given. This is a domain action rather than an entity action
precisely so it can be called while the server is off and its entities are unavailable.

It fails with `no_wake_target` if nothing resolves to a loaded entry, `wol_unavailable` if the
Home Assistant Wake on LAN integration is not set up, and `no_mac_addresses` if no MAC
addresses are configured.

```yaml
action: jriver.wake
data:
  entity_id: remote.music_room
```

## `jriver.get_playlist`

Returns the playing now list for the zone behind the given media player.

| Field | Required | Notes |
| --- | --- | --- |
| `entity_id` | yes | A single JRiver media player |

```yaml
action: jriver.get_playlist
data:
  entity_id: media_player.music_room_player
response_variable: playing_now
```

Response shape — at most 500 entries, each carrying the fields `Key`, `Name`, `Artist`,
`Album`, `Duration` and `Media Type`:

```yaml
zone: Player
entries:
  - Key: "123456"
    Name: Cemetery Party
    Artist: AIR
    Album: Love 2
    Duration: "212"
    Media Type: Audio
```

## `jriver.search`

Runs a library search and returns the matches.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `entity_id` | yes | | A single JRiver media player; only the server it belongs to matters |
| `query` | yes | | A JRiver search expression |
| `fields` | no | `Key`, `Name`, `Artist`, `Album`, `Duration`, `Media Type` | Library fields to return |
| `limit` | no | 100 | 1 to 500; passed to `Files/Search` |

```yaml
action: jriver.search
data:
  entity_id: media_player.music_room
  query: "[Album Artist (auto)]=[AIR]"
  fields: [Name, Artist, Album]
  limit: 50
response_variable: matches
```

Response shape:

```yaml
results:
  - Name: Cemetery Party
    Artist: AIR
    Album: Love 2
```

---

# Standard actions

## `media_player.play_media`

See [Media]({{ site.baseurl }}/media/) for the content id formats. `enqueue` accepts
`replace` (the default, which clears the playing now list first), `add`, `next` and `play`.
`play` queues next and then skips to it.

## `media_player.repeat_set` and `media_player.shuffle_set`

`repeat` takes `off`, `all` or `one`. Both are unavailable on Media Center versions that do
not implement `Playback/Repeat` and `Playback/Shuffle`; the coordinator stops asking after the
first rejection and the state reads as unknown.

## `media_player.select_source`

Single device mode only. The source is a zone name; selecting one changes the active zone.

## `media_player.join` and `media_player.unjoin`

Per zone mode only. They map onto `Playback/LinkZones` and `Playback/UnlinkZones`.

```yaml
action: media_player.join
target:
  entity_id: media_player.music_room_player
data:
  group_members:
    - media_player.music_room_office
```

`unjoin` unlinks the targeted zone. Members that are not JRiver media players belonging to the
same config entry are ignored.

## `media_player.select_sound_mode`

Loads one of the DSP presets configured in the options. Anything not on that list is
rejected; use `jriver.load_dsp_preset` for presets you have not listed.

```yaml
action: media_player.select_sound_mode
target:
  entity_id: media_player.music_room
data:
  sound_mode: Night
```

## `media_player.turn_on` and `media_player.turn_off`

`turn_on` sends MCC 22009 with parameter 0, which shows the standard view. It cannot start
Media Center if the machine is off; use `jriver.wake`.

`turn_off` calls `Playback/StopAll` and, when the
[turn off behaviour option]({{ site.baseurl }}/options/#turn-off-behaviour) is
`close_program`, additionally sends MCC 20007. `remote.turn_on` and `remote.turn_off` behave
identically.

## `remote.send_command`

Sends one or more key presses via `Control/Key`, joined with `;` and delivered with focus.

Each command is matched first against the key **names**, then against their **values**, and
is otherwise passed to Media Center verbatim.

| Name | Value | | Name | Value |
| --- | --- | --- | --- | --- |
| `UP` | `Up` | | `MENU` | `Menu` |
| `DOWN` | `Down` | | `DELETE` | `Delete` |
| `LEFT` | `Left` | | `PLUS` | `+` |
| `RIGHT` | `Right` | | `MINUS` | `-` |
| `ENTER` | `Enter` | | `BACKSPACE` | `Backspace` |
| `HOME` | `Home` | | `ESCAPE` | `Escape` |
| `END` | `End` | | `APPS` | `Apps` |
| `PAGE_UP` | `Page Up` | | `SPACE` | `Space` |
| `PAGE_DOWN` | `Page Down` | | `PRINT_SCREEN` | `Print Screen` |
| `CTRL` | `Ctrl` | | `TAB` | `Tab` |
| `SHIFT` | `Shift` | | `INSERT` | `Insert` |
| `ALT` | `Alt` | | | |

```yaml
action: remote.send_command
target:
  entity_id: remote.music_room
data:
  command:
    - DOWN
    - DOWN
    - ENTER
```
