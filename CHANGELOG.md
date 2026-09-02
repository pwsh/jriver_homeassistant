# Changelog

## 2.0.0

A rework of the integration. Existing config entries and entities are migrated automatically the
first time Home Assistant loads the new version.

### Breaking changes

- **Entity unique ids changed.** Config entries are migrated to version 2 and the entity registry
  is rewritten so entity ids and history are preserved. Zone entities are now keyed by zone id
  rather than zone name, so renaming a zone in Media Center no longer orphans its entities.
- **`jriver.add_to_playlist` has been removed.** It had multiple defects and duplicated
  `jriver.append_search_results_to_playlist` (for a query) and `jriver.play_playlist` (for a
  playlist path). Automations that used it must be updated.
- **The audio direct sensor is now a `binary_sensor`.** The old `sensor` entity is removed during
  migration and a `binary_sensor.<server>_<zone>_audio_direct` takes its place.
- **The playlist sensor now reports a track count**, with the next ten entries as a bounded
  attribute, instead of dumping the whole playing now list into state attributes (which broke the
  recorder's 16 KB limit). Use the new `jriver.get_playlist` action for the full list.
- **YAML configuration has been removed.** The integration has been config flow only for some
  time; the leftover `media_player:` platform import no longer exists.
- **The `hamcws` dependency has been dropped.** A fixed and extended copy of the client is
  vendored in `custom_components/jriver/mcws/`, so the integration now has zero requirements.
- Configuration values such as browse paths, zones and extra fields have moved from entry data to
  entry options. This happens automatically during migration.

### Added

- Reauthentication and reconfiguration flows.
- A full options flow: poll interval, turn off behaviour, DSP presets, zone topology, zone
  allowlist, browse paths, MAC addresses and extra fields.
- Working `repeat` and `shuffle` state and control.
- `MediaPlayerEnqueue` support in `play_media` (`replace`, `add`, `next`, `play`), plus
  `media_content_type: query` and `playlist`.
- `select_source` in single device mode (switches the active zone) and `grouping` in per zone
  mode (zone linking).
- `select_sound_mode` backed by DSP presets configured in the options.
- New actions: `jriver.play_search`, `jriver.stop_after`, `jriver.load_dsp_preset`,
  `jriver.get_playlist` (response) and `jriver.search` (response).
- A diagnostics platform that redacts credentials, the access key and MAC addresses.
- Entity translations, icon translations and enum device classes for the sensors.
- A version sensor (diagnostic, disabled by default).

### Changed

- One device for the server, and in per zone mode one device per zone linked to it, instead of a
  device per entity.
- Runtime state lives on `ConfigEntry.runtime_data` rather than `hass.data`.
- The coordinator now polls adaptively (2 s while playing, 3× slower when idle), calls `Alive`
  every 5 minutes rather than every tick, reloads browse rules every 15 minutes, only polls zones
  in the allowlist plus the active zone, and only refetches playlists and audio paths when the
  file key or the playing now change counter changes.
- Per zone failures are isolated: one bad zone no longer fails the whole update, and the previous
  good value is kept.
- The config entry is identified by the Media Center access key when one is available, so a
  change of IP address no longer creates a duplicate entry.
- Action failures now raise `HomeAssistantError` instead of being logged and swallowed.
- Artwork is proxied through Home Assistant using an authenticated MCWS token.
- The media player's `linked_zones` attribute now lists zone **names**, matching what Media Center
  actually returns in `Playback/Info` (it previously tried to parse them as ids and was always
  empty). `group_members` maps those names to the corresponding zone entity ids.
- A zone with no file loaded no longer reports the stale duration, position, title, media type or
  artwork that Media Center leaves behind from the previous track.
- The zone name attribute falls back to the configured zone name for the local zone, which
  `Playback/Info` reports without a `ZoneName`.
- `jriver.search` and `jriver.append_search_results_to_playlist` now pass the limit to
  `Files/Search` instead of fetching the whole result set and trimming it locally.
- Loudness now uses the real `DSP/Loudness` endpoint; the previous `Playback/Loudness` call does
  not exist and always failed. (Not exposed to Home Assistant users.)
- `Playback/Info` also parses `RemainingTimeDisplay`, `PositionDisplay`,
  `PlayingNowPositionDisplay`, `LipSyncAdjustmentMS` and `Rating`, which appear on the playing now
  sensor.

### Fixed

- `media_content_id` reported `-1` when nothing was loaded.
- `jriver.seek_relative` performed an absolute seek.
- `jriver.adjust_volume` used two different code paths for positive and negative deltas.
- `media_player.play` paused a zone that was already playing.
- `repeat_set` raised `NotImplementedError` despite the feature being advertised.
- `jriver.wake` could not resolve its target entity.
- The coordinator mutated the previous (frozen) snapshot and never pruned removed zones.
- Sensors could hold a stale state because they returned early without writing.
- The `select_zones` form field was unlabelled.
- The password field in the config flow is now a password input.
- The configured connection timeout is honoured instead of a hard coded 20 seconds.
- The test workflow measured coverage of the wrong package and used a broken cache key.
