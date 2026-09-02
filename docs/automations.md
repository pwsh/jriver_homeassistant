---
title: Automations
nav_order: 8
---

# Automation examples

Every example assumes a server named `Music Room` with a zone named `Player`, giving
`media_player.music_room` in single device mode and `media_player.music_room_player` in per
zone mode. Substitute your own entity ids; see
[Entities]({{ site.baseurl }}/entities/#devices-and-naming) for how they are derived.

## Play a search from a button

```yaml
automation:
  - alias: Play AIR on the study button
    triggers:
      - trigger: state
        entity_id: input_button.study_music
    actions:
      - action: jriver.play_search
        target:
          entity_id: media_player.music_room
        data:
          query: "[Album Artist (auto)]=[AIR] ~sort=[Date],[Album],[Track #]"
          play_mode: replace
```

## Wake the server, then play

`jriver.wake` is a domain action so it can be called while the server is off and its entities
are unavailable. Wait for the media player to come back before sending playback commands.

```yaml
automation:
  - alias: Morning wake up
    triggers:
      - trigger: time
        at: "07:00:00"
    actions:
      - action: jriver.wake
        data:
          entity_id: remote.music_room
      - wait_template: >-
          {{ not is_state('media_player.music_room', 'unavailable') }}
        timeout: "00:02:00"
        continue_on_timeout: false
      - action: media_player.volume_set
        target:
          entity_id: media_player.music_room
        data:
          volume_level: 0.25
      - action: jriver.play_playlist
        target:
          entity_id: media_player.music_room
        data:
          playlist_path: 'Alarms\Morning\Wakeup'
```

## Nudge the volume with a remote

`jriver.adjust_volume` moves by a signed percentage of full scale, so you do not have to read
the current level first.

```yaml
automation:
  - alias: Volume down on double press
    triggers:
      - trigger: event
        event_type: zha_event
        event_data:
          command: "double"
    actions:
      - action: jriver.adjust_volume
        target:
          entity_id: media_player.music_room
        data:
          delta: -5
```

## Sleep timer at night

`jriver.stop_after` targets the active zone and takes exactly one of `minutes`, `tracks` or
`current`.

```yaml
automation:
  - alias: Stop the music half an hour after midnight starts
    triggers:
      - trigger: state
        entity_id: media_player.music_room
        to: playing
    conditions:
      - condition: time
        after: "23:00:00"
        before: "05:00:00"
    actions:
      - action: jriver.stop_after
        target:
          entity_id: remote.music_room
        data:
          minutes: 30
```

## Announce what is coming next

The playing now list sensor carries up to ten upcoming entries in its `next_up` attribute.
For the full list use
[`jriver.get_playlist`]({{ site.baseurl }}/actions/#jrivergetplaylist).

```yaml
automation:
  - alias: Announce the next track
    triggers:
      - trigger: state
        entity_id: sensor.music_room_player_playing_now
    variables:
      next_up: >-
        {{ state_attr('sensor.music_room_player_playing_now_list', 'next_up') | default([], true) }}
    conditions:
      - condition: template
        value_template: "{{ next_up | count > 0 }}"
    actions:
      - action: notify.persistent_notification
        data:
          title: Up next
          message: >-
            {{ next_up[0].name }} by {{ next_up[0].artist }}
```

## Link zones when a scene runs

Per zone mode only. `media_player.join` maps onto Media Center zone linking.

```yaml
automation:
  - alias: Whole house audio
    triggers:
      - trigger: state
        entity_id: scene.party
    actions:
      - action: media_player.join
        target:
          entity_id: media_player.music_room_player
        data:
          group_members:
            - media_player.music_room_kitchen
            - media_player.music_room_office
```

Unlink again with `media_player.unjoin` on the same entity.

## Switch DSP preset by time of day

Requires the preset names to be listed in the integration
[options]({{ site.baseurl }}/options/#dsp-presets). For a preset that is not listed, use
`jriver.load_dsp_preset` instead.

```yaml
automation:
  - alias: Night listening profile
    triggers:
      - trigger: time
        at: "22:00:00"
        id: night
      - trigger: time
        at: "08:00:00"
        id: day
    actions:
      - action: media_player.select_sound_mode
        target:
          entity_id: media_player.music_room
        data:
          sound_mode: >-
            {{ 'Night' if trigger.id == 'night' else 'Default' }}
```

## Search and act on the results

`jriver.search` returns a response, so a script can inspect the matches before playing
anything.

```yaml
script:
  play_recent_additions:
    sequence:
      - action: jriver.search
        data:
          entity_id: media_player.music_room
          query: "[Media Type]=[Audio] [Date Imported]=>-7d"
          fields: [Key, Name, Artist]
          limit: 50
        response_variable: matches
      - condition: template
        value_template: "{{ matches.results | count > 0 }}"
      - action: media_player.play_media
        target:
          entity_id: media_player.music_room
        data:
          media_content_type: music
          media_content_id: "K|{{ matches.results[0]['Key'] }}"
```
