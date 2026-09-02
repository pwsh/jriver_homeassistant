"""Translation between JRiver Media Center and Home Assistant media taxonomies."""

from __future__ import annotations

from typing import Final

from homeassistant.components.media_player import MediaClass, MediaType

from .mcws import MediaSubType as McMediaSubType, MediaType as McMediaType

MC_FIELD_TO_HA_MEDIATYPE: Final[dict[str, str]] = {
    "Audio": "MUSIC",
    "Artist": "ARTIST",
    "Album": "ALBUM",
    "Album Artist (auto)": "ARTIST",
    "Composer": "ARTIST",
    "Video": "VIDEO",
    "Images": "IMAGE",
    "Playlists": "PLAYLIST",
    "Playing Now": "PLAYLIST",
    "Shows": "TVSHOW",
    "Series": "TVSHOW",
    "Genre": "GENRE",
    "Podcast": "PODCAST",
}

MC_FIELD_TO_HA_MEDIACLASS: Final[dict[str, str]] = {
    k: "TV_SHOW" if v == "TVSHOW" else v for k, v in MC_FIELD_TO_HA_MEDIATYPE.items()
}


def translate_to_media_type(
    media_type: McMediaType | str | None,
    media_sub_type: McMediaSubType | str | None,
    single: bool = False,
) -> MediaType | str:
    """Convert a JRiver media type/sub type pair to a HA MediaType."""
    if media_type == McMediaType.VIDEO:
        if media_sub_type == McMediaSubType.MOVIE:
            return MediaType.MOVIE
        if media_sub_type == McMediaSubType.TV_SHOW:
            return MediaType.EPISODE if single else MediaType.TVSHOW
        return MediaType.VIDEO

    if media_type == McMediaType.AUDIO:
        return MediaType.TRACK if single else MediaType.MUSIC

    if media_type == McMediaType.TV:
        return MediaType.CHANNEL if single else MediaType.TVSHOW

    if media_type == McMediaType.IMAGE:
        return MediaType.IMAGE

    if media_type == McMediaType.PLAYLIST:
        return MediaType.PLAYLIST

    if not media_type:
        if media_sub_type == McMediaSubType.MOVIE:
            return MediaType.MOVIE
        if media_sub_type == McMediaSubType.TV_SHOW:
            return MediaType.EPISODE if single else MediaType.TVSHOW
        if media_sub_type == McMediaSubType.MUSIC:
            return MediaType.TRACK if single else MediaType.MUSIC

    return ""


def translate_to_media_class(
    media_type: McMediaType | str | None,
    media_sub_type: McMediaSubType | str | None,
    single: bool = False,
) -> MediaClass | str:
    """Convert a JRiver media type/sub type pair to a HA MediaClass."""
    if media_type == McMediaType.VIDEO:
        if media_sub_type == McMediaSubType.MOVIE:
            return MediaClass.MOVIE
        if media_sub_type == McMediaSubType.TV_SHOW:
            return MediaClass.EPISODE if single else MediaClass.TV_SHOW
        return MediaClass.VIDEO

    if media_type == McMediaType.AUDIO:
        return MediaClass.TRACK if single else MediaClass.MUSIC

    if media_type == McMediaType.TV:
        return MediaClass.CHANNEL

    if media_type == McMediaType.IMAGE:
        return MediaClass.IMAGE

    if media_type == McMediaType.PLAYLIST:
        return MediaClass.PLAYLIST

    if not media_type:
        if media_sub_type == McMediaSubType.MOVIE:
            return MediaClass.MOVIE
        if media_sub_type == McMediaSubType.TV_SHOW:
            return MediaClass.EPISODE if single else MediaClass.TV_SHOW
        if media_sub_type == McMediaSubType.MUSIC:
            return MediaClass.TRACK if single else MediaClass.MUSIC

    return ""
