"""Test media browsing and the media type translation."""

from __future__ import annotations

import pytest

from custom_components.jriver.browse_media import browse_nodes, media_source_content_filter
from custom_components.jriver.mcws import (
    MediaSubType as McMediaSubType,
    MediaType as McMediaType,
    parse_browse_paths_from_text,
)
from custom_components.jriver.media_types import (
    translate_to_media_class,
    translate_to_media_type,
)
from homeassistant.components.media_player import BrowseMedia, MediaClass, MediaType
from homeassistant.core import HomeAssistant

from .conftest import FakeMediaServer

PATHS = parse_browse_paths_from_text(["Audio,Album|Album", "Video,Movies"])


@pytest.mark.parametrize(
    ("media_type", "media_sub_type", "single", "expected"),
    [
        (McMediaType.AUDIO, McMediaSubType.MUSIC, False, MediaType.MUSIC),
        (McMediaType.AUDIO, McMediaSubType.MUSIC, True, MediaType.TRACK),
        (McMediaType.VIDEO, McMediaSubType.MOVIE, False, MediaType.MOVIE),
        (McMediaType.VIDEO, McMediaSubType.TV_SHOW, False, MediaType.TVSHOW),
        (McMediaType.VIDEO, McMediaSubType.TV_SHOW, True, MediaType.EPISODE),
        (McMediaType.VIDEO, McMediaSubType.NOT_AVAILABLE, False, MediaType.VIDEO),
        (McMediaType.TV, McMediaSubType.NOT_AVAILABLE, True, MediaType.CHANNEL),
        (McMediaType.IMAGE, McMediaSubType.NOT_AVAILABLE, False, MediaType.IMAGE),
        (McMediaType.PLAYLIST, McMediaSubType.NOT_AVAILABLE, False, MediaType.PLAYLIST),
        (McMediaType.NOT_AVAILABLE, McMediaSubType.MOVIE, False, MediaType.MOVIE),
        (McMediaType.NOT_AVAILABLE, McMediaSubType.NOT_AVAILABLE, False, ""),
    ],
)
def test_translate_to_media_type(media_type, media_sub_type, single, expected) -> None:
    """Media Center types map onto HA media types."""
    assert translate_to_media_type(media_type, media_sub_type, single) == expected


@pytest.mark.parametrize(
    ("media_type", "media_sub_type", "single", "expected"),
    [
        (McMediaType.AUDIO, McMediaSubType.MUSIC, False, MediaClass.MUSIC),
        (McMediaType.AUDIO, McMediaSubType.MUSIC, True, MediaClass.TRACK),
        (McMediaType.VIDEO, McMediaSubType.MOVIE, False, MediaClass.MOVIE),
        (McMediaType.VIDEO, McMediaSubType.TV_SHOW, True, MediaClass.EPISODE),
        (McMediaType.VIDEO, McMediaSubType.NOT_AVAILABLE, False, MediaClass.VIDEO),
        (McMediaType.TV, McMediaSubType.NOT_AVAILABLE, False, MediaClass.CHANNEL),
        (McMediaType.IMAGE, McMediaSubType.NOT_AVAILABLE, False, MediaClass.IMAGE),
        (McMediaType.PLAYLIST, McMediaSubType.NOT_AVAILABLE, False, MediaClass.PLAYLIST),
        (McMediaType.NOT_AVAILABLE, McMediaSubType.MUSIC, True, MediaClass.TRACK),
        (McMediaType.NOT_AVAILABLE, McMediaSubType.NOT_AVAILABLE, False, ""),
    ],
)
def test_translate_to_media_class(media_type, media_sub_type, single, expected) -> None:
    """Media Center types map onto HA media classes."""
    assert translate_to_media_class(media_type, media_sub_type, single) == expected


def test_media_source_content_filter() -> None:
    """Camera snapshots are filtered out of the media source list."""
    camera = BrowseMedia(
        media_class=MediaClass.IMAGE,
        media_content_id="media-source://camera/camera.front",
        media_content_type="image/png",
        title="Front",
        can_play=True,
        can_expand=False,
    )
    music = BrowseMedia(
        media_class=MediaClass.MUSIC,
        media_content_id="media-source://media_source/local/a.mp3",
        media_content_type="audio/mpeg",
        title="A",
        can_play=True,
        can_expand=False,
    )
    assert media_source_content_filter(camera) is False
    assert media_source_content_filter(music) is True


async def test_browse_root(hass: HomeAssistant, fake_server: FakeMediaServer) -> None:
    """The root lists the configured views plus the HA media sources."""
    card, count = await browse_nodes(hass, fake_server, PATHS)

    assert card.title == "Media Library"
    assert card.media_content_id == "-1"
    assert count == 2
    titles = [child.title for child in card.children]
    assert titles[:2] == ["Audio", "Video"]
    assert card.children[0].media_content_id == "N|1|Audio"
    assert card.children[0].can_play is False
    assert card.children[0].can_expand is True


async def test_browse_child_node(hass: HomeAssistant, fake_server: FakeMediaServer) -> None:
    """Browsing into a node returns its children."""
    card, count = await browse_nodes(
        hass, fake_server, PATHS, parent_content_type="music", parent_id="N|1|Audio"
    )

    assert card.title == "Audio"
    assert count == 1
    child = card.children[0]
    assert child.title == "Album"
    assert child.media_content_id == "N|3|Audio > Album"
    assert child.thumbnail == "http://thumb/3"


async def test_browse_files(hass: HomeAssistant, fake_server: FakeMediaServer) -> None:
    """A node with no children lists its files."""
    card, count = await browse_nodes(
        hass,
        fake_server,
        PATHS,
        parent_content_type="music",
        parent_id="N|3|Audio > Album",
    )

    assert count == 1
    child = card.children[0]
    assert child.title == "2: Radian"
    assert child.media_content_id == "K|100"
    assert child.media_content_type == MediaType.TRACK
    assert child.can_play is True
    assert child.can_expand is False


async def test_browse_rejects_unknown_content_id(
    hass: HomeAssistant, fake_server: FakeMediaServer
) -> None:
    """An unrecognised content id is rejected."""
    from homeassistant.components.media_player import BrowseError

    with pytest.raises(BrowseError):
        await browse_nodes(hass, fake_server, PATHS, parent_id="nonsense")
