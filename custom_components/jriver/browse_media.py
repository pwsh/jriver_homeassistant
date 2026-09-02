"""Support for browsing the Media Center library."""

from __future__ import annotations

import contextlib
import logging

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    BrowseError,
    BrowseMedia,
    MediaClass,
    MediaType,
)
from homeassistant.core import HomeAssistant

from .mcws import (
    BrowsePath,
    MediaServer,
    MediaSubType as McMediaSubType,
    MediaType as McMediaType,
    search_for_path,
)
from .media_types import (
    MC_FIELD_TO_HA_MEDIACLASS,
    MC_FIELD_TO_HA_MEDIATYPE,
    translate_to_media_class,
    translate_to_media_type,
)

_LOGGER = logging.getLogger(__name__)

PLAYLIST_ROOTS = ("Playlists", "Playing Now")


class UnknownMediaType(BrowseError):
    """Unknown media type."""


def media_source_content_filter(item: BrowseMedia) -> bool:
    """Filter out media sources that Media Center cannot play."""
    return not (
        item.media_content_id.startswith("media-source://camera/")
        and item.media_content_type == "image/png"
    )


def _format_item_name(values: dict) -> str:
    """Build a display name for a library file."""
    media_type = _decode_media_type(values)
    if media_type == MediaType.EPISODE and "Episode" in values:
        return f"{values['Episode']}: {values['Name']}"
    if media_type == MediaType.TRACK and "Track #" in values:
        return f"{values['Track #']}: {values['Name']}"
    if media_type == MediaType.MOVIE and "HDR Format" in values:
        return f"{values['Name']} (HDR)"
    return values["Name"]


def _decode_media_type(item: dict) -> MediaType | str:
    return translate_to_media_type(
        item.get("Media Type", ""), item.get("Media Sub Type", ""), single=True
    )


def _decode_media_class(item: dict) -> MediaClass | str:
    return translate_to_media_class(
        item.get("Media Type", ""), item.get("Media Sub Type", ""), single=True
    )


async def browse_nodes(
    hass: HomeAssistant,
    ms: MediaServer,
    browse_paths: list[BrowsePath],
    parent_content_type: str | None = None,
    parent_id: str = "-1",
) -> tuple[BrowseMedia, int]:
    """Create a BrowseMedia describing the children of the given node."""
    if not parent_id:
        parent_id = "-1"
    parent_media_id = parent_id
    container_media_class: MediaClass = MediaClass.DIRECTORY
    container_media_type: MediaType | str = "library"
    parent_name: str | None = None
    path_tokens: list[str] = []

    if parent_id == "-1":
        pass
    elif parent_id.startswith("N|"):
        _, parent_id, parent_name = parent_id.split("|", 2)
        path_tokens = parent_name.split(" > ")
        if parent_content_type:
            container_media_type = parent_content_type
        browse_path = search_for_path(browse_paths, path_tokens)
        if browse_path:
            if classification := _classify_browse_path(browse_path):
                container_media_class, container_media_type = classification
        elif path_tokens and path_tokens[0] in PLAYLIST_ROOTS:
            container_media_class = MediaClass.PLAYLIST
            container_media_type = MediaType.PLAYLIST
    else:
        raise BrowseError(f"Unknown media_content_id format {parent_id}")

    is_child = parent_name is not None

    nodes = await ms.browse_children(base_id=int(parent_id))
    items: list[dict] = []
    expandable: bool
    if nodes:
        for name, node_id in nodes.items():
            child_path = [*path_tokens, name]
            if container_media_class == MediaClass.PLAYLIST:
                media_type = container_media_type
                media_class = container_media_class
            else:
                browse_path = search_for_path(browse_paths, child_path)
                if not browse_path:
                    continue
                if classification := _classify_browse_path(browse_path):
                    media_class, media_type = classification
                else:
                    media_class = container_media_class
                    try:
                        media_type = MediaType[container_media_type]
                    except KeyError:
                        media_type = container_media_type
            items.append(
                {
                    "media_id": f"N|{node_id}|{' > '.join(child_path)}",
                    "name": name,
                    "thumbnail": await ms.get_browse_thumbnail_url(node_id),
                    "mt": media_type,
                    "mc": media_class,
                }
            )
        expandable = len(items) > 0
    else:
        files = await ms.browse_files(base_id=int(parent_id))
        items = [
            {
                "media_id": f"K|{file['Key']}",
                "name": _format_item_name(file),
                "thumbnail": await ms.get_file_image_url(int(file["Key"])),
                "mt": _decode_media_type(file),
                "mc": _decode_media_class(file),
            }
            for file in files
        ]
        expandable = False

    children: list[BrowseMedia] = [
        BrowseMedia(
            title=item["name"],
            media_class=item["mc"],
            media_content_type=item["mt"],
            media_content_id=item["media_id"],
            can_play=is_child,
            can_expand=expandable,
            thumbnail=item["thumbnail"],
        )
        for item in items
    ]
    count = len(children)

    # only the root browse offers the Home Assistant media sources
    if not is_child:
        with contextlib.suppress(BrowseError):
            item = await media_source.async_browse_media(
                hass, None, content_filter=media_source_content_filter
            )
            if item.domain is None:
                if item.children:
                    children = [*children, *item.children]
            else:
                children.append(item)

    return (
        BrowseMedia(
            media_class=container_media_class,
            media_content_id=parent_media_id,
            media_content_type=container_media_type,
            title=parent_name if parent_name else "Media Library",
            can_play=not expandable,
            can_expand=expandable,
            children=children,
        ),
        count,
    )


def _classify_browse_path(path: BrowsePath) -> tuple[MediaClass, MediaType] | None:
    """Work out the HA media class/type pair for a browse path."""

    def _translate(
        media_type: McMediaType, media_sub_type: McMediaSubType | None
    ) -> tuple[MediaClass, MediaType] | None:
        mt = translate_to_media_type(media_type, media_sub_type)
        mc = translate_to_media_class(media_type, media_sub_type)
        if isinstance(mt, MediaType) and isinstance(mc, MediaClass):
            return mc, mt
        return None

    mt_name = MC_FIELD_TO_HA_MEDIATYPE.get(path.name)
    mc_name = MC_FIELD_TO_HA_MEDIACLASS.get(path.name)
    if mt_name and mc_name:
        return MediaClass[mc_name], MediaType[mt_name]

    for media_type in path.effective_media_types:
        if path.effective_media_sub_types:
            for media_sub_type in path.effective_media_sub_types:
                if values := _translate(media_type, media_sub_type):
                    return values
        elif values := _translate(media_type, None):
            return values

    return None
