---
title: Configuration
nav_order: 3
---

# Configuration

The setup flow runs once when you add the integration. Everything it collects except the
server location and credentials can be changed later from
[Options]({{ site.baseurl }}/options/).

{: .note }
> The screenshots below come from the 0.4.x release. The forms have gained fields and better
> labels since, so treat them as a guide to what each step is for rather than a pixel accurate
> record.

## 1. Server location

Asks for an **access key**, or a **host** and **port**. Fill in one or the other; the access
key is resolved to a host and port for you.

| Field | Notes |
| --- | --- |
| API key | The access key shown in Options > Media Network, for example `AbCdEf`. |
| Host | Hostname or IP address of the machine running Media Center, for example `mc.local`. |
| Port | The Media Network port. `52199` by default. |
| Name | A memorable name for the server. Left blank, the name Media Center reports is used. |
| Uses an SSL certificate | Connect over HTTPS rather than HTTP. |

![Server location]({{ site.baseurl }}/assets/img/config_1.png)

The name becomes the server device's name, which in turn drives the entity ids (see
[Entities]({{ site.baseurl }}/entities/)).

The config entry is identified by the access key the server reports, when it reports one. That
means the entry survives a change of IP address. When there is no access key, `host:port` is
used instead.

Errors you may see here: `cannot_connect`, `timeout_connect`, `invalid_access_key` (the access
key could not be resolved to an address), and `already_configured` if the same server is
already set up.

## 2. Credentials

Shown only when Media Center rejects the unauthenticated connection. Both fields are optional
in the form, but the pair must be what Media Center expects.

| Field | Notes |
| --- | --- |
| Username | From Options > Media Network > Authentication. |
| Password | As above. Entered as a password field, so it is not shown on screen. |

![Credentials]({{ site.baseurl }}/assets/img/config_2.png)

## 3. Wake on LAN

Asks whether to configure the `jriver.wake` action, and for the MAC addresses to send the
magic packet to.

| Field | Notes |
| --- | --- |
| Configure the jriver.wake action? | Requires at least one MAC address when ticked. |
| MAC address | One or more addresses. Six pairs of hex digits separated by `:` or `-`; dashes are normalised to colons and the value is lower cased. |

If Media Center reports its own MAC addresses when the integration connects, they are filled
in for you and wake on LAN is pre-enabled.

`jriver.wake` also needs the Home Assistant
[Wake on LAN](https://www.home-assistant.io/integrations/wake_on_lan/) integration to be set
up; the action fails with `wol_unavailable` otherwise.

## 4. Browse paths

**Skipped entirely on Media Center 32.0.6 and newer**, which exposes its remote views over
MCWS and has them discovered automatically.

On older versions the views must be typed in. They are the same views configured in Media
Center under **Options > Media Network > Advanced > "Customize views for JRemote, Gizmo and
Panel"**.

Each entry is a pipe delimited pair of comma separated lists. The path names go on the left,
the category (library field) names on the right:

```
Audio,Artist|Album Artist (auto),Album
```

The form is pre-filled with a default set:

```
Audio,Album|Album
Audio,Artist|Album Artist (auto),Album
Audio,Composer|Composer,Album
Audio,Genre|Genre,Album Artist (auto),Album
Audio,Podcast
Audio,Recent|Album
Video,Movies
Video,Music|Artist,Album
Video,Shows|Series,Season
```

A path with no categories, such as `Audio,Podcast`, is allowed. An entry that does not parse
gives the `invalid_paths` error; an empty list gives `no_paths`.

## 5. Zones

**Skipped when Media Center reports only one zone.**

The first form asks whether zones should be separate devices.

![Single device or one per zone]({{ site.baseurl }}/assets/img/config_4.png)

| Topology | Behaviour |
| --- | --- |
| One device for the whole server (unticked) | A single media player that follows the active zone. It gains `select_source`, listing the zone names; selecting one calls `Playback/SetZone`. |
| One device per zone (ticked) | Each selected zone gets its own device with its own media player. `grouping` (zone linking) is available, and per-zone sensors are created. |

When you tick the box, a second form asks which zones to include. At least one is required
(`no_zones` otherwise).

![Zone selection]({{ site.baseurl }}/assets/img/config_5.png)

{: .note }
> The zone list is also a polling allowlist. Only zones on it, plus whichever zone is
> currently active, are polled. See [Options]({{ site.baseurl }}/options/).

## 6. Playback fields

The last step offers the library fields Media Center knows about. Anything selected here is
requested with every `Playback/Info` call and exposed as an attribute on the playing now
sensors and the media player.

Leave it empty if you have no use for extra metadata; every field adds work to every poll.

If the library fields cannot be loaded the list is empty and the step can simply be
submitted.

## Reauthentication

If Media Center starts rejecting the stored credentials, the integration raises a
reauthentication flow rather than failing silently. Home Assistant shows a **Reconfigure**
prompt on the integration card and on the notifications panel. The form asks for a user name
and password, verifies them against the server, and reloads the entry.

## Reconfiguration

**Settings > Devices & Services > JRiver Media Center > ⋮ > Reconfigure** moves an existing
entry to a new access key, host, port, name or SSL setting without losing its history. The
stored credentials are reused.

The flow connects to the address you give it and compares the resulting unique id with the
entry's. If they differ it aborts with `wrong_server`: reconfiguration will not repoint an
entry at a different Media Center instance. Set that one up as a separate entry instead.

Everything else, including zones, browse paths, MAC addresses and extra fields, lives in
[Options]({{ site.baseurl }}/options/), not here.
