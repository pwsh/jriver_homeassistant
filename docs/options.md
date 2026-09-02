---
title: Options
nav_order: 4
---

# Options

**Settings > Devices & Services > JRiver Media Center > Configure** opens the options flow.
The entry reloads automatically when it finishes, so entities are rebuilt with the new
settings.

The flow needs to reach Media Center to list zones and library fields. If the server is
unreachable the first form shows a connection error and cannot be submitted.

## Summary

| Option | Key | Default | Effect |
| --- | --- | --- | --- |
| Poll interval | `poll_interval` | 2 s | Seconds between updates while a zone is playing. |
| Turn off behaviour | `turn_off_behaviour` | `stop` | What `turn_off` does. |
| DSP presets | `dsp_presets` | empty | Preset names exposed as sound modes. |
| Show zones as separate devices | `per_zone` | off | Zone topology. |
| Zones | `device_zones` | empty (all) | Which zones get devices, and the polling allowlist. |
| View paths | `browse_paths` | discovered | Only asked for on Media Center < 32.0.6. |
| Enable the jriver.wake action / MAC address | `use_wol`, `mac` | off | Wake on LAN. |
| Field name | `extra_fields` | empty | Extra library fields exposed as attributes. |

## Step 1: polling, power and DSP

### Poll interval

Whole seconds, between 1 and 60. This is the interval used while any polled zone is
**playing**.

When nothing is playing the interval is multiplied by 3 and clamped back into the 1–60 second
range, so the default 2 s becomes 6 s while idle. The interval is recalculated at the end of
every update.

Only the cheap calls run on every tick: `Playback/Zones`, `UserInterface/Info` and
`Playback/Info` for each polled zone. `Alive` runs every 5 minutes, `Browse/Rules` every 15
minutes, and the audio path, playing now list, repeat and shuffle are only refetched for a
zone when its file key or playing now change counter changes.

### Turn off behaviour

| Value | Label | Behaviour |
| --- | --- | --- |
| `stop` | Stop playback | `media_player.turn_off` and `remote.turn_off` call `Playback/StopAll`. |
| `close_program` | Stop playback and close Media Center | As above, then sends MCC 20007. |

{: .warning }
> MCC 20007 closes Media Center entirely. On some headless Linux installs it leaves the
> process hung so that MCWS never comes back and the integration cannot reconnect. This is why
> `stop` is the default and closing the program is opt in.

`turn_on` is unaffected by this option: it always sends MCC 22009 with parameter 0, which
shows the standard view. It cannot start Media Center if the machine is off — use
`jriver.wake` for that.

### DSP presets

A free text list of DSP preset names as they exist in Media Center. When the list is
non-empty:

- the media player advertises `SELECT_SOUND_MODE`;
- `sound_mode_list` is exactly the names you typed;
- `media_player.select_sound_mode` rejects anything not on the list.

The names are not validated against the server. A misspelling produces a preset that fails
when selected. `jriver.load_dsp_preset` bypasses the list and can load any preset by name.

## Step 2: zones

| Field | Effect |
| --- | --- |
| Show zones as separate devices | Off: one media player for the server, which follows the active zone and gains `select_source`. On: one device and one media player per selected zone, with `grouping` available. |
| Zones | The zones to include. At least one is required when the per-zone box is ticked. |

The zone list does two jobs:

1. **Which entities exist.** The playing now sensor, playing now list sensor and audio direct
   binary sensor are created for zones on the list. An empty list means every zone.
2. **What gets polled.** A zone is polled when it is on the list, or when it is the active
   zone. Zones outside the list are ignored on every tick, which is the cheapest way to keep
   a large Media Center install responsive.

{: .note }
> Disabling a zone device in Home Assistant does not stop it being polled. Remove the zone
> from this list instead.

## Step 3: browse paths

Skipped when the server supports `Browse/Rules` (Media Center 32.0.6 and newer); the existing
value is carried through unchanged. Otherwise the same form as
[setup step 4]({{ site.baseurl }}/configuration/#4-browse-paths), pre-filled with the
configured paths or, if there are none, the built-in defaults.

## Step 4: wake on LAN

| Field | Effect |
| --- | --- |
| Enable the jriver.wake action | When off, the stored MAC addresses are cleared and `jriver.wake` fails with `no_mac_addresses`. |
| MAC address | One or more addresses. Six pairs of hex digits separated by `:` or `-`. |

## Step 5: extra fields

The library fields Media Center reports, offered as a multi-select. Anything chosen is
requested with every `Playback/Info` and lands on:

- the playing now sensor's attributes, and
- the media player's extra state attributes.

Submitting this form saves the whole options set and reloads the entry.
