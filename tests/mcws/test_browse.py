"""Tests for browse rule/path handling."""

from __future__ import annotations

from custom_components.jriver.mcws import (
    BrowsePath,
    BrowseRule,
    MediaSubType,
    MediaType,
    convert_browse_rules,
    parse_browse_paths_from_text,
    search_for_path,
)

MANY_RULES = """<Response Status="OK">
<Item Name="Images\\Album" Categories="Album" Search=""/>
<Item Name="Audio\\Genre" Categories="Genre\\Album Artist (auto)\\Album" Search=""/>
<Item Name="Audio\\Highly Rated" Categories="" Search="[Rating]=&gt;=4"/>
<Item Name="Audio\\Recent" Categories="Album" Search="~sort="/>
<Item Name="Audio\\Highly Rated\\Recent Albums" Categories="Album" Search=""/>
<Item Name="Images\\Highly Rated" Categories="" Search="[Rating]=&gt;=4"/>
<Item Name="Video\\Recent" Categories="" Search="~sort=[Date Imported]-d ~n=250"/>
<Item Name="Images" Categories="" Search="[Media Type]=[Image]"/>
<Item Name="Audio\\Artist" Categories="Album Artist (auto)\\Album" Search=""/>
<Item Name="Images\\Keyword" Categories="Keywords" Search=""/>
<Item Name="Video\\Movies" Categories="" Search="[Media Sub Type]=[Movie] ~sort=[Name]"/>
<Item Name="Audiobooks\\Books" Categories="Album" Search=""/>
<Item Name="Audiobooks\\Authors" Categories="Artist\\Album" Search=""/>
<Item Name="Video\\Shows" Categories="Series\\Season" Search="[Media Sub Type]=[TV Show]"/>
<Item Name="Video" Categories="" Search="[Media Type]=[Video]"/>
<Item Name="Audio" Categories="" Search="[Media Type]=[Audio]"/>
<Item Name="Video\\Music" Categories="Artist\\Album" Search="[Media Type]=[Video] [Media Sub Type]=[Music]"/>
<Item Name="Images\\Disk" Categories="Location" Search=""/>
<Item Name="Video\\Home Videos" Categories="Year" Search="[Media Sub Type]=[Home Video]"/>
<Item Name="Video\\Disk" Categories="Location" Search=""/>
<Item Name="Radio" Categories="Publisher" Search="[Media Sub Type]=[Radio]"/>
<Item Name="Audiobooks" Categories="" Search="[Media Type]=[Audio] [Genre]=[Audiobook]"/>
<Item Name="Audio\\Podcast" Categories="" Search="[Media Sub Type]=[Podcast] ~sort=[Date]-d"/>
<Item Name="Images\\Camera" Categories="Camera" Search=""/>
<Item Name="Video\\Other" Categories="" Search="-[Media Sub Type]=[Home Video],[Movie],[TV Show]"/>
<Item Name="Images\\Year" Categories="Year\\Album" Search=""/>
<Item Name="Audio\\Composer" Categories="Composer\\Album" Search=""/>
<Item Name="Audio\\Album" Categories="Album" Search=""/>
</Response>"""

TEXT_RULES = [
    "Images",
    "Radio,Channels",
    "Video,Shows|Series,Season",
    "Video,Movies",
    "Video,Music|Artist,Album",
    "Audiobooks,Books|Album",
    "Audiobooks,Authors|Artist,Album",
]


def test_browse_rule_helpers() -> None:
    """Names and categories split on backslash, dropping empties."""
    rule = BrowseRule("Images\\Album", "Album", "")
    assert rule.get_names() == ["Images", "Album"]
    assert rule.get_categories() == ["Album"]
    assert BrowseRule("", "Images\\Album", "").get_names() == []
    assert sorted([BrowseRule("b", "", ""), BrowseRule("a", "", "")]) == [
        BrowseRule("a", "", ""),
        BrowseRule("b", "", ""),
    ]


def test_browse_path_properties() -> None:
    """full_path, descendents and effective types."""
    root = BrowsePath("Audio", media_types=[MediaType.AUDIO])
    child = BrowsePath("Album", parent=root)
    root.children.append(child)
    grandchild = BrowsePath("Album", is_field=True, parent=child)
    child.children.append(grandchild)
    assert root.full_path == "Audio"
    assert grandchild.full_path == "Audio/Album/Album"
    assert root.descendents == [child, grandchild]
    assert grandchild.effective_media_types == [MediaType.AUDIO]
    assert grandchild.effective_media_sub_types == []


async def test_get_browse_rules(fake, make_server) -> None:
    """Browse rules are parsed from the XML response."""
    fake.set(
        "Browse/Rules",
        '<Response Status="OK">'
        '<Item Name="Images\\Album" Categories="Album" Search=""/>'
        "</Response>",
    )
    ms = await make_server()
    assert await ms.get_browse_rules() == [BrowseRule("Images\\Album", "Album", "")]
    assert fake.params("Browse/Rules")["Type"] == "Remote"


async def test_get_browse_rules_unsupported(fake, make_server) -> None:
    """An unsupported Browse/Rules returns an empty list."""
    ms = await make_server()
    assert await ms.get_browse_rules() == []


async def test_get_browse_rules_failure(fake, make_server) -> None:
    """A Failure response returns an empty list."""
    fake.set("Browse/Rules", '<Response Status="Failure"/>')
    ms = await make_server()
    assert await ms.get_browse_rules() == []


async def test_convert_browse_rules(fake, make_server) -> None:
    """A realistic rule set converts into the expected tree."""
    fake.set("Browse/Rules", MANY_RULES)
    ms = await make_server()
    rules = await ms.get_browse_rules()
    assert len(rules) == 28

    paths = convert_browse_rules(rules)
    assert {p.name for p in paths} == {
        "Audio",
        "Audiobooks",
        "Images",
        "Radio",
        "Video",
    }
    audio = next(p for p in paths if p.name == "Audio")
    assert audio.effective_media_types == [MediaType.AUDIO]
    assert audio.children[0].name == "Album"
    assert audio.children[0].children[0].is_field
    assert audio.children[0].children[0].effective_media_sub_types == [MediaSubType.MUSIC]

    flat = [p.full_path for p in convert_browse_rules(rules, flat=True)]
    assert "Audio/Highly Rated/Recent Albums" in flat
    assert "Video/Shows" in flat
    assert len(flat) == 28

    unmapped = convert_browse_rules(rules, infer_media_types=False)
    assert next(p for p in unmapped if p.name == "Radio").media_types == []


def test_parse_browse_paths_from_text() -> None:
    """Compact text rules build the same shape of tree."""
    paths = parse_browse_paths_from_text(TEXT_RULES)
    assert {p.name for p in paths} == {"Images", "Radio", "Video", "Audiobooks"}
    video = next(p for p in paths if p.name == "Video")
    assert video.effective_media_types == [MediaType.VIDEO]
    shows = next(c for c in video.children if c.name == "Shows")
    assert shows.effective_media_sub_types == [MediaSubType.TV_SHOW]
    assert shows.children[0].name == "Series"
    assert shows.children[0].is_field
    assert shows.children[0].children[0].name == "Season"


def test_search_for_path() -> None:
    """Paths are located by name, descending into field nodes."""
    paths = parse_browse_paths_from_text(TEXT_RULES)
    assert search_for_path(paths, ["Images"]).full_path == "Images"
    assert search_for_path(paths, ["Radio", "Channels"]).full_path == "Radio/Channels"
    assert search_for_path(paths, ["Video", "Shows"]).full_path == "Video/Shows"
    assert search_for_path(paths, ["Video", "Shows", "The Wire"]).full_path == "Video/Shows/Series"
    assert (
        search_for_path(paths, ["Video", "Shows", "The Wire", "2"]).full_path
        == "Video/Shows/Series/Season"
    )
    assert (
        search_for_path(paths, ["Audiobooks", "Books", "My Book"]).full_path
        == "Audiobooks/Books/Album"
    )
    assert search_for_path(paths, ["My", "Images"]) is None
    assert search_for_path(paths, ["Radio", "Stations"]) is None
    assert search_for_path(paths, []) is None
    assert search_for_path([], ["Images"]) is None


def test_convert_browse_rules_ignores_empty_names() -> None:
    """A rule with no name segments is skipped."""
    assert convert_browse_rules([BrowseRule("", "", "")]) == []
