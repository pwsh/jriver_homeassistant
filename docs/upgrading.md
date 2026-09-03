---
title: Upgrading
nav_order: 9
---

# Upgrading from 0.4.x

Version 2.0.0 is a rework. Existing config entries and entities are migrated automatically the
first time Home Assistant loads it. This page lists what happens on its own and what needs your
attention.

{: .warning }
> If the upstream 3ll3d00d version is installed through HACS, remove it before installing this
> fork. Both use the Home Assistant domain `jriver`, so they cannot coexist.

## What happens automatically

| Change | Detail |
| --- | --- |
| Config entry version | Version 1 entries are migrated to version 2 on load. |
| Data moves to options | `browse_paths`, `per_zone`, `device_zones`, `extra_fields` and `use_wol` move from entry data to entry options. The new `poll_interval`, `turn_off_behaviour` and `dsp_presets` options are given their defaults. A `timeout` and an empty `api_key` are added to entry data if missing; the field is labelled **Access key** in the UI but the stored key remains `api_key`. |
| Server entity unique ids | `<uid>_player` becomes `<uid>_media_player`, `<uid>_activezone` becomes `<uid>_active_zone`, `<uid>_uimode` becomes `<uid>_ui_mode`. |
| Zone entity unique ids | Rewritten on the first successful refresh, when the zone ids are known: `<uid>_player-<zone name>`, `<uid>_<zone name>_playingnow` and `<uid>_<zone name>_playlist` become `<uid>_zone_<zone id>_media_player`, `…_playing_now` and `…_playlist`. |
| Entity ids and history | Preserved, because the registry entries are rewritten rather than recreated. |
| Devices | One device for the server, plus one per zone in per zone mode, replacing the old device-per-entity layout. |
| Old devices | The empty device-per-entity records left by 0.4.x are deleted on the first load, along with devices for zones that no longer exist on the server. |
| Entry title | Version 1 entries titled with the access key or the host are retitled to the configured name, so the integration page lists the server by name. |
| Entry identity | The entry's unique id is now the Media Center access key when the server reports one, so a change of IP address no longer creates a duplicate entry. |

Devices are also removable by hand: if a device is no longer backed by the server, the **Delete**
button on its page removes it. Live server and zone devices refuse deletion.

Because zone entities are now keyed by zone **id** rather than name, renaming a zone in Media
Center no longer orphans its entities.

## What breaks

### `jriver.add_to_playlist` has been removed

It had several defects and duplicated other actions. Replace calls with:

| Old usage | Replacement |
| --- | --- |
| A search query | [`jriver.append_search_results_to_playlist`]({{ site.baseurl }}/actions/#jriverappendsearchresultstoplaylist) |
| A playlist path | [`jriver.play_playlist`]({{ site.baseurl }}/actions/#jriverplayplaylist) |

### Audio direct is now a binary sensor

The old `sensor.<server>_<zone>_audio_direct` entity is deleted during migration. A
`binary_sensor.<server>_<zone>_audio_direct` takes its place, with a fresh history. It is a
diagnostic entity and its `audio_path` attribute still holds the DSP chain.

Automations, templates and dashboards referring to the old sensor need updating, including any
that compared the state to a string rather than to `on`/`off`.

### The playlist sensor reports a track count

It used to dump the whole playing now list into its state attributes, which exceeded the
recorder's 16 KB attribute limit on any real playlist.

It now reports the **number of entries** as its state, with unit `tracks`, and exposes only the
next ten entries as the `next_up` attribute. Use
[`jriver.get_playlist`]({{ site.baseurl }}/actions/#jrivergetplaylist) for the full list.

### YAML configuration has been removed

The leftover `media_player:` platform import is gone. The integration has been config flow
only for some time; delete any remaining `jriver` platform block from `configuration.yaml`.

### The `hamcws` dependency has been dropped

A fixed and extended copy of the client is vendored in `custom_components/jriver/mcws/`, so
the integration declares no requirements at all. Nothing to do — but if you pinned `hamcws`
yourself for some reason, it is no longer used.

## What to check after upgrading

1. **Options.** Open **Configure** on the integration and walk through the new options flow
   once. Poll interval, turn off behaviour and DSP presets have never been set on a migrated
   entry, so they hold their defaults.
2. **Entity ids.** Confirm your media players, sensors and the remote still carry the entity
   ids your automations use. Migration preserves them, but a zone renamed between the two
   versions may not match.
3. **The audio direct entity.** Search your dashboards and automations for `audio_direct` and
   move them to the `binary_sensor` domain.
4. **The playlist sensor.** Anything reading the old full-list attributes needs rewriting
   against `next_up` or `jriver.get_playlist`.
5. **`add_to_playlist`.** Search your automations for it; calls now fail.
6. **New capabilities you may want.** Repeat and shuffle now work, `select_source` switches
   the active zone in single device mode, `grouping` links zones in per zone mode, and DSP
   presets become sound modes once listed in the options.
7. **Diagnostics.** Download diagnostics from the integration page to confirm the entry data
   and options look right; credentials, the access key and MAC addresses are redacted.
