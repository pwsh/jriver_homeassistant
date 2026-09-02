---
title: Home
nav_order: 1
---

# JRiver Media Center for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that controls
[JRiver Media Center](https://jriver.com/) over its
[Media Network web service](https://wiki.jriver.com/index.php/Web_Service_Interface) (MCWS).

Version 2.0.0 vendors its own MCWS client, so the integration has no external Python
requirements.

![The media player card]({{ site.baseurl }}/assets/img/example.png)

## Fork notice

This site documents the fork at
[pwsh/jriver_homeassistant](https://github.com/pwsh/jriver_homeassistant), branch
`v2-rework`, which carries version 2.0.0. The original integration is
[3ll3d00d/jriver_homeassistant](https://github.com/3ll3d00d/jriver_homeassistant) and remains
the upstream project. Both use the Home Assistant domain `jriver`, so only one of them can be
installed at a time. See [Upgrading]({{ site.baseurl }}/upgrading/) for what changes when you
move from the upstream 0.4.x release.

## What it gives you

| Area | Summary |
| --- | --- |
| Entities | A media player (one per server, or one per zone), a remote, and sensors for the active zone, UI mode, version, playing now, playing now list and audio direct. See [Entities]({{ site.baseurl }}/entities/). |
| Browsing | Media Center remote views, Playlists and Playing Now inside the Home Assistant media browser, alongside Home Assistant media sources. See [Media]({{ site.baseurl }}/media/). |
| Playback | Play, pause, stop, seek, volume, shuffle, repeat, clear playlist, and `play_media` with `replace` / `add` / `next` / `play` enqueue modes. |
| Grouping | In per zone mode the standard `media_player.join` and `media_player.unjoin` actions map onto Media Center zone linking. |
| Sources | In single device mode `select_source` switches the active zone. |
| DSP presets | Preset names listed in the options become sound modes for `media_player.select_sound_mode`. |
| Wake on LAN | `jriver.wake` sends a magic packet to the MAC addresses recorded for the server. |
| Actions | Searches, playlists, relative seek and volume, MCC commands, sleep timers, and two response actions. See [Actions]({{ site.baseurl }}/actions/). |

## Requirements

- Home Assistant 2026.1 or newer.
- JRiver Media Center 24 or newer, with **Options > Media Network > "Use Media Network to
  share this library and enable DLNA"** enabled.
- Media Center 32.0.6 or newer for automatic browse path discovery. On older versions the
  browse views have to be entered by hand during setup.
- The [Wake on LAN](https://www.home-assistant.io/integrations/wake_on_lan/) integration, only
  if you want to use `jriver.wake`.

Media Center has no push interface, so the integration polls. The interval adapts: the
configured interval while a zone is playing, three times slower when everything is idle.

## Quick links

- [Installation]({{ site.baseurl }}/installation/)
- [Configuration]({{ site.baseurl }}/configuration/)
- [Options]({{ site.baseurl }}/options/)
- [Entities]({{ site.baseurl }}/entities/)
- [Actions]({{ site.baseurl }}/actions/)
- [Media browsing and playing]({{ site.baseurl }}/media/)
- [Automation examples]({{ site.baseurl }}/automations/)
- [Upgrading]({{ site.baseurl }}/upgrading/)
- [Troubleshooting]({{ site.baseurl }}/troubleshooting/)
- [Development]({{ site.baseurl }}/development/)
- [Changelog]({{ site.baseurl }}/changelog/)
- [MCWS reference]({{ site.baseurl }}/mcws-functions/)
