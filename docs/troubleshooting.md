---
title: Troubleshooting
nav_order: 10
---

# Troubleshooting

## Setup fails

### `cannot_connect`

Media Center is not answering on the address given.

- Confirm **Options > Media Network > "Use Media Network to share this library and enable
  DLNA"** is ticked and Media Center is running.
- Confirm the port. It is `52199` by default; the form defaults to that.
- Check that the SSL toggle matches how Media Center is actually served. HTTPS against a
  plain HTTP server fails here.
- Check any firewall between Home Assistant and the Media Center machine.

### `timeout_connect`

The server was reachable but did not answer in time. The connection timeout is 10 seconds and
is stored on the config entry. A Media Center that is busy scanning a library can exceed it;
try again once it settles.

### `invalid_auth` during setup

The setup flow moves you to the credentials step automatically the first time Media Center
demands authentication. If it rejects what you enter, check **Options > Media Network >
Authentication** in Media Center.

### `invalid_access_key`

The access key could not be resolved to an address. Access key lookup goes through JRiver's
service, so it needs outbound internet access from Home Assistant. Copy the key exactly as
shown in **Options > Media Network** — it is a short alphanumeric string like `AbCdEf`. If
lookup keeps failing, enter the host and port directly instead; the entry still works, it just
loses the ability to follow the server across an IP address change.

### `already_configured`

The same server is already set up. The entry is identified by the access key when the server
reports one, so adding it a second time by host name is recognised as a duplicate.

### `wrong_server` when reconfiguring

Reconfiguration deliberately refuses to point an existing entry at a different Media Center
instance, because the entry's history belongs to the old one. Add the other server as a
separate entry.

## Home Assistant asks me to reauthenticate

Media Center rejected the stored credentials during a poll. The integration raises a
reauthentication flow rather than failing silently. Enter the current user name and password
from **Options > Media Network > Authentication**.

## Entities are unavailable

Every entity goes unavailable when the last coordinator update failed, and a zone entity also
goes unavailable when its zone no longer exists on the server.

The coordinator only fails the whole update when the cheap tier fails: `Alive`,
`Playback/Zones` or `UserInterface/Info`. When that happens Home Assistant's own backoff takes
over and retries with a growing delay, so recovery after the server comes back is not
instant. Reloading the integration forces an immediate retry.

Failures in the per-zone and expensive tiers are logged at debug level and the previous good
value is kept, so a single misbehaving zone cannot take everything else down.

If a zone's entities never appear, check that the zone is on the
[zone list]({{ site.baseurl }}/options/#step-2-zones) in the options. An empty list means all
zones.

## Turning off hangs Media Center on Linux

The [turn off behaviour]({{ site.baseurl }}/options/#turn-off-behaviour) option set to
`close_program` sends MCC 20007 after stopping playback, which closes Media Center entirely.
On some headless Linux installs the process is left hung and MCWS never comes back, so the
integration cannot reconnect and cannot restart it either.

Set the option back to **Stop playback**, which is the default. If Media Center is already
hung you have to kill and restart it on the host.

## The playing now list is too big for the recorder

This was a defect in 0.4.x, where the whole playing now list went into the playlist sensor's
state attributes and exceeded the recorder's 16 KB limit. It is fixed: the sensor now reports a
track count and a bounded `next_up` attribute. See [Upgrading]({{ site.baseurl }}/upgrading/).

## Reading diagnostics

**Settings > Devices & Services > JRiver Media Center > ⋮ > Download diagnostics** produces a
JSON file containing:

- the config entry's data and options, with the password, user name, access key and MAC
  addresses redacted;
- the server's name, version, platform, library version and whether it supports browse rules
  and audio path direct;
- the coordinator's current update interval, last update success flag and zone allowlist;
- the zone list, active zone id, UI mode, per-zone playback info, audio paths, playlist
  lengths, repeat and shuffle state, and the names of the resolved browse paths.

It is the fastest way to see what the integration actually thinks the server looks like.

## Enabling debug logging

Add to `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.jriver: debug
```

Or turn it on without a restart from **Settings > Devices & Services > JRiver Media Center >
⋮ > Enable debug logging**.

Debug logging reports which zones are being refreshed, features the server rejected as
unsupported, unique id migrations, and every optional call that failed quietly.

## Known limitations

- Media Center has no push interface, so the integration polls. The interval adapts — the
  configured interval while playing, three times slower when idle — but there is always some
  latency.
- `Playback/Repeat` and `Playback/Shuffle` are not available on every Media Center version.
  When the server rejects them the integration stops asking and the state reads as unknown.
- Browse views are only discovered automatically on Media Center 32.0.6 and newer. On older
  versions they have to be entered by hand.
- The coordinator keeps at most 500 playing now entries per zone. Use `jriver.get_playlist`
  for the full list.
- Disabling a zone's device in Home Assistant does not stop polling for it; remove the zone
  from the options instead.
- `Playback/Info` reports `LinkedZones` as zone names, so `group_members` cannot resolve a
  linked zone whose name is duplicated or that has no media player entity.
- Media Center keeps reporting the previous track's duration for a zone that has nothing
  loaded. The integration reports no media at all for such a zone rather than a stale
  duration.
