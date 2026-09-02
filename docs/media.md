---
title: Media
nav_order: 7
---

# Media browsing and playing

## Browsing

Open the media browser from a JRiver media player card, or from **Media** in the sidebar and
pick the player.

The root of the tree lists:

- the Media Center **remote views** — the ones configured under Options > Media Network >
  Advanced, typically Audio, Video and their sub-views;
- **Playlists** and **Playing Now**, added automatically on servers that support
  `Browse/Rules`;
- every Home Assistant [media source](https://www.home-assistant.io/integrations/media_source/),
  appended after the Media Center entries. Camera PNG sources are filtered out because Media
  Center cannot play them.

Media sources only appear at the root. Once you descend into a Media Center view you see that
view's children.

Descending eventually reaches files rather than nodes. Nodes are expandable, files are
playable. Item names are decorated where it helps: an episode gets `<episode>: <name>`, a
track gets `<track #>: <name>`, and a movie with an HDR format gets `<name> (HDR)`.

Thumbnails come from Media Center. Artwork on the media player itself is proxied through Home
Assistant with an authenticated MCWS token, so it renders from outside your LAN.

On Media Center versions older than 32.0.6 the views are the ones you typed in during setup,
not discovered ones. If none are configured, browsing fails with "No browse paths are
configured, add them in the integration options".

## Playing

`media_player.play_media` accepts several `media_content_id` shapes. They are tested in this
order.

| Content id | Content type | Behaviour |
| --- | --- | --- |
| `N\|<node id>\|<path>` | ignored | Plays every file under that browse node. This is what the media browser produces for a view. |
| `K\|<file key>` | ignored | Plays that library file. This is what the media browser produces for a file. |
| a search expression | `query` or `search` | Runs the search and plays the results |
| a playlist path | `playlist` | Plays the stored playlist |
| `media-source://…` | any | Resolved to a URL, then played as a URL |
| a URL or path | anything else | Played directly by Media Center |

A content type from Media Center's own vocabulary (`music`, `album`, `artist`, `movie`,
`episode`, `playlist`, …) paired with a content id that is not one of the shapes above is
rejected: there is no way to turn a bare title into something Media Center can play. Use a
`query` instead.

### Examples

```yaml
# a library item by key, as produced by the media browser
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: music
  media_content_id: "K|123456"
```

```yaml
# every file under a browse node
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: music
  media_content_id: "N|1042|Audio > Artist > AIR"
```

```yaml
# a search expression
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: query
  media_content_id: "[Album Artist (auto)]=[AIR] ~sort=[Date],[Album],[Track #]"
```

```yaml
# a stored playlist
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: playlist
  media_content_id: 'Alarms\Morning\Wakeup'
```

```yaml
# an internet radio stream, appended rather than replacing
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: url
  media_content_id: http://stream.example.com/radio.flac
  enqueue: add
```

```yaml
# a Home Assistant media source
action: media_player.play_media
target:
  entity_id: media_player.music_room
data:
  media_content_type: music
  media_content_id: media-source://media_source/local/doorbell.mp3
```

## Enqueue modes

| `enqueue` | Media Center play mode | Effect |
| --- | --- | --- |
| `replace` (default when omitted) | — | Clears the playing now list, then plays |
| `add` | `Add` | Appends to the end of the playing now list |
| `next` | `NextToPlay` | Queues after the current file |
| `play` | `NextToPlay` | Queues after the current file, then skips to it |

The search-related actions use the same vocabulary under different names:
[`jriver.play_search`]({{ site.baseurl }}/actions/#jriverplaysearch) takes `replace`, `add`
or `next`.
