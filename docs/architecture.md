---
title: Architecture
parent: Development
nav_order: 1
---

# Architecture

## Module layering

```
custom_components/jriver/
  mcws/           vendored MCWS client, no Home Assistant imports
  const.py        domain, config/option keys, defaults, entity kinds, action names
  media_types.py  Media Center media type/sub type -> HA MediaType/MediaClass
  coordinator.py  MediaServerUpdateCoordinator + the frozen MediaServerData snapshot
  models.py       JRiverRuntimeData and the typed JRiverConfigEntry alias
  entity.py       MediaServerEntity base: device topology, unique ids, the @cmd wrapper
  services.py     action schemas, target resolution and the domain action handlers
  browse_media.py the media browser tree
  __init__.py     setup, unload, migration, action registration
  config_flow.py  setup, reauth, reconfigure and the options flow
  media_player.py / remote.py / sensor.py / binary_sensor.py / diagnostics.py
```

Nothing above `mcws/` talks HTTP, and nothing inside `mcws/` imports Home Assistant. The client
is a straight port of `hamcws` with its defects fixed and extra endpoints added, vendored so the
integration declares no requirements.

Imports flow one way: `const` and `media_types` depend on nothing local (bar `mcws`),
`coordinator` depends on `const`/`mcws`, `models` on `coordinator`, `entity` on `models`, and the
platforms on everything below them.

## Coordinator tiers

A single `DataUpdateCoordinator` per config entry produces an immutable `MediaServerData`
snapshot. Each tick runs in tiers so a slow or unsupported call cannot stall or break the rest:

| Tier | Calls | When |
| --- | --- | --- |
| Cheap | `Playback/Zones`, `UserInterface/Info` | every tick |
| Identity | `Alive` | every 5 minutes, or after a failure |
| Per zone | `Playback/Info` for each polled zone | every tick, gathered concurrently |
| Expensive | `Playback/AudioPath`, `Playback/Playlist`, `Playback/Repeat`, `Playback/Shuffle` | only when a zone's file key or `PlayingNowChangeCounter` changes, or on first sight |
| Browse | `Browse/Rules` | every 15 minutes, or when the server version changes |

A zone is polled when it is in the configured allowlist, or when it is the active zone. Failures
in the cheap tier raise `UpdateFailed` (or `ConfigEntryAuthFailed` for an auth error) and let the
coordinator's backoff take over; failures in the per zone and expensive tiers are logged at debug
and the previous good value is kept. State belonging to zones that no longer exist is pruned.

The update interval is recomputed at the end of every tick: the configured poll interval while
any zone is playing, three times that when everything is idle, clamped to 1–60 seconds.

## Device topology

```
Server device                (DOMAIN, <entry unique id>)
├── media_player             single device mode only
├── remote
├── sensor.active_zone
├── sensor.ui_mode           diagnostic
├── sensor.version           diagnostic, disabled by default
└── Zone device              (DOMAIN, <entry unique id>_zone_<zone id>), via_device the server
    ├── media_player         per zone mode only
    ├── sensor.playing_now
    ├── sensor.playlist
    └── binary_sensor.audio_direct
```

Entity unique ids are `<entry unique id>_<kind>` or `<entry unique id>_zone_<zone id>_<kind>`.
The entry's unique id is the Media Center access key when the server reports one, otherwise
`host:port`.

Zone entities are keyed by zone **id**, not name, so renaming a zone keeps its history. Version 1
entries used name based ids; `async_migrate_entry` rewrites the server level ids during migration
and the zone level ids on the first successful refresh, when the zone ids are known.

## Data flow

```
MCWS  ──►  mcws.MediaServer  ──►  MediaServerUpdateCoordinator
                                        │  MediaServerData (frozen)
                                        ▼
                          MediaServerEntity subclasses
                          (properties read coordinator.data directly)
                                        │
   commands ◄── @cmd ◄── entity actions ─┘
```

Entities never cache derived state in `_handle_coordinator_update`; every property reads the
current snapshot, so an entity is correct the moment it is added. Commands go the other way
through the `@cmd` decorator, which maps client errors onto `HomeAssistantError` (with translated
messages) and requests a coordinator refresh once the call succeeds.

`ConfigEntry.runtime_data` holds a `JRiverRuntimeData` with the client, the coordinator and the
resolved options; there is no `hass.data` usage. Domain actions resolve their target by looking
the entity up in the entity registry, following `config_entry_id` back to the entry, and parsing
the zone id out of the entity's unique id.
