"""Tests for the high level MediaServer client."""

from __future__ import annotations

import pytest

from custom_components.jriver.mcws import (
    AudioPath,
    KeyCommand,
    LibraryField,
    PlaybackState,
    Playlist,
    PlayMode,
    RepeatMode,
    ShuffleMode,
    UnsupportedRequestError,
    ViewMode,
    Zone,
)
from custom_components.jriver.mcws.mcc import MCC

from .conftest import OK

ALIVE = """<Response Status="OK">
<Item Name="RuntimeGUID">{123456-7890}</Item>
<Item Name="LibraryVersion">24</Item>
<Item Name="ProgramName">JRiver Media Center</Item>
<Item Name="ProgramVersion">31.0.83</Item>
<Item Name="FriendlyName">MyServer</Item>
<Item Name="ProductVersion">31 Linux</Item>
<Item Name="Platform">Linux</Item>
</Response>"""

ZONES = """<Response Status="OK">
<Item Name="NumberZones">3</Item>
<Item Name="CurrentZoneID">10081</Item>
<Item Name="CurrentZoneIndex">0</Item>
<Item Name="ZoneName0">Player</Item>
<Item Name="ZoneID0">10081</Item>
<Item Name="ZoneGUID0">{xxxx-xxxx}</Item>
<Item Name="ZoneDLNA0">0</Item>
<Item Name="ZoneName1">Family Room</Item>
<Item Name="ZoneID1">10074</Item>
<Item Name="ZoneGUID1">{xxxx-xxxx}</Item>
<Item Name="ZoneDLNA1">1</Item>
<Item Name="ZoneName2">Den</Item>
<Item Name="ZoneID2">10087</Item>
<Item Name="ZoneGUID2">{xxxx-xxxx}</Item>
<Item Name="ZoneDLNA2">1</Item>
</Response>"""

PLAYBACK_INFO = """<Response Status="OK">
<Item Name="ZoneID">10081</Item>
<Item Name="ZoneName">Player</Item>
<Item Name="State">0</Item>
<Item Name="FileKey">-1</Item>
<Item Name="NextFileKey">-1</Item>
<Item Name="PositionMS">0</Item>
<Item Name="DurationMS">1229000</Item>
<Item Name="ElapsedTimeDisplay">0:00</Item>
<Item Name="TotalTimeDisplay">Live</Item>
<Item Name="PlayingNowPosition">-1</Item>
<Item Name="PlayingNowTracks">0</Item>
<Item Name="PlayingNowChangeCounter">2</Item>
<Item Name="Bitrate">0</Item>
<Item Name="Bitdepth">0</Item>
<Item Name="SampleRate">0</Item>
<Item Name="Channels">0</Item>
<Item Name="Chapter">0</Item>
<Item Name="Volume">0.44999</Item>
<Item Name="VolumeDisplay">45% (-27.5 dB)</Item>
<Item Name="LinkedZones">10074,10087</Item>
<Item Name="ImageURL">MCWS/v1/File/GetImage?File=4294967295</Item>
<Item Name="Name">Media Center</Item>
</Response>"""

LIBRARY_FIELDS = """<Response Status="OK">
<Fields>
<Field Name="Filename" DataType="Path" EditType="Filename" DisplayName="Filename"/>
<Field Name="Name" DataType="String" EditType="Standard" DisplayName="Name"/>
<Field Name="Artist" DataType="List" EditType="Standard" DisplayName="Artist"/>
</Fields>
</Response>"""

# older MC omits the Response wrapper (and thus the Status attribute)
LIBRARY_FIELDS_NO_STATUS = """<Fields>
<Field Name="Filename" DataType="Path" EditType="Filename" DisplayName="Filename"/>
</Fields>"""

BROWSE_CHILDREN = """<Response Status="OK">
<Item Name="1000">Audio</Item>
<Item Name="1001">Video</Item>
</Response>"""

BROWSE_FILES = (
    '[{"Key": 1866769, "Name": "Lean Beef Patty", "Media Type": "Audio"},'
    ' {"Key": 1866770, "Name": "Steppa Pig", "Media Type": "Audio"}]'
)

# a raw control character inside a string value, as MC sometimes emits
PLAYLIST_JSON = (
    '[{"Key": 1866769, "Name": "Lean\x01 Beef Patty", "Artist": "JPEGMAFIA"},'
    ' {"Key": 1866770, "Name": "Steppa Pig", "Artist": "JPEGMAFIA"}]'
)

PLAYLISTS = """<Response Status="OK">
<Item>
<Field Name="ID">1234</Field>
<Field Name="Name">Favourites</Field>
<Field Name="Path">Top\\Favourites</Field>
<Field Name="Type">Playlist</Field>
</Item>
<Item>
<Field Name="ID">1235</Field>
<Field Name="Name">Chill</Field>
<Field Name="Path">Top\\Chill</Field>
<Field Name="Type">Playlist</Field>
</Item>
</Response>"""

AUDIO_PATH = """<Response Status="OK">
<Item Name="AudioPath">No changes are being made</Item>
<Item Name="Direct">yes</Item>
<Item Name="AudioPath0">No changes are being made</Item>
</Response>"""


async def test_alive(fake, make_server) -> None:
    """Alive populates media_server_info."""
    fake.set("Alive", ALIVE)
    ms = await make_server()
    assert ms.media_server_info is None
    info = await ms.alive()
    assert info.name == "MyServer"
    assert info.version_tuple == (31, 0, 83)
    assert info.library_version == 24
    assert info.is_linux
    assert ms.media_server_info == info
    assert ms.host == "localhost"
    assert isinstance(ms.port, int)
    assert ms.make_url("x").endswith("/x")


async def test_auth_token_and_image_urls(fake, make_server) -> None:
    """Tokens are fetched once and appended to image urls."""
    ms = await make_server()
    assert await ms.get_auth_token() == "1234567"
    url = await ms.get_file_image_url(123456)
    assert url == (
        f"http://localhost:{ms.port}/MCWS/v1/File/GetImage?File=123456"
        "&Type=Thumbnail&ThumbnailSize=Large&Format=png&Token=1234567"
    )
    url = await ms.get_file_image_url(1, thumbnail_size="small", format="jpg")
    assert "ThumbnailSize=small" in url
    assert "Format=jpg" in url
    url = await ms.get_browse_thumbnail_url(654321)
    assert url == (
        f"http://localhost:{ms.port}/MCWS/v1/Browse/Image"
        "?UseStackedImages=1&Format=jpg&ID=654321&Token=1234567"
    )
    assert fake.count("Authenticate") == 1


async def test_zones(fake, make_server) -> None:
    """Zones are parsed and the active one flagged."""
    fake.set("Playback/Zones", ZONES)
    ms = await make_server()
    zones = await ms.get_zones()
    assert [z.name for z in zones] == ["Player", "Family Room", "Den"]
    assert [z.id for z in zones] == [10081, 10074, 10087]
    assert zones[0].active
    assert not zones[1].active
    assert zones[1].is_dlna


async def test_library_fields(fake, make_server) -> None:
    """Library fields are parsed."""
    fake.set("Library/Fields", LIBRARY_FIELDS)
    ms = await make_server()
    fields = await ms.get_library_fields()
    assert len(fields) == 3
    assert fields[0] == LibraryField("Filename", "Path", "Filename", "Filename")


async def test_library_fields_without_status(fake, make_server) -> None:
    """A <Fields> root with no Status attribute still parses."""
    fake.set("Library/Fields", LIBRARY_FIELDS_NO_STATUS)
    ms = await make_server()
    fields = await ms.get_library_fields()
    assert fields == [LibraryField("Filename", "Path", "Filename", "Filename")]


async def test_library_fields_failure(fake, make_server) -> None:
    """A Failure response returns an empty list."""
    fake.set("Library/Fields", '<Response Status="Failure"/>')
    ms = await make_server()
    assert await ms.get_library_fields() == []


async def test_playback_info(fake, make_server) -> None:
    """Playback info is parsed and the image url tokenised."""
    fake.set("Playback/Info", PLAYBACK_INFO)
    ms = await make_server()
    info = await ms.get_playback_info(extra_fields=["Rating"])
    assert info.zone_id == 10081
    assert info.state is PlaybackState.STOPPED
    assert info.duration_ms == 1229000
    assert info.linked_zones == [10074, 10087]
    assert info.playback_info == ""
    assert info.image_url.endswith("File=4294967295&Token=1234567")
    assert info.extra_fields == {"Rating": ""}
    params = fake.params("Playback/Info")
    assert "Rating" in params["Fields"]
    assert "Media Type" in params["Fields"]


async def test_playback_info_zone_addressing(fake, make_server) -> None:
    """Zones are addressed by id, names by ZoneType=Name."""
    fake.set("Playback/Info", PLAYBACK_INFO)
    fake.set("Playback/Zones", ZONES)
    ms = await make_server()
    zones = await ms.get_zones()
    await ms.get_playback_info(zones[1])
    assert fake.params("Playback/Info")["Zone"] == "10074"
    assert fake.params("Playback/Info")["ZoneType"] == "ID"
    await ms.get_playback_info("Den")
    assert fake.params("Playback/Info")["Zone"] == "Den"
    assert fake.params("Playback/Info")["ZoneType"] == "Name"
    await ms.get_playback_info()
    assert "Zone" not in fake.params("Playback/Info")


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("play", "Playback/Play"),
        ("play_pause", "Playback/PlayPause"),
        ("pause", "Playback/Pause"),
        ("stop", "Playback/Stop"),
        ("next_track", "Playback/Next"),
        ("previous_track", "Playback/Previous"),
        ("stop_all", "Playback/StopAll"),
        ("clear_playlist", "Playback/ClearPlaylist"),
    ],
)
async def test_simple_commands(fake, make_server, method: str, path: str) -> None:
    """Simple commands hit the right endpoint and report success."""
    fake.set(path, OK)
    ms = await make_server()
    assert await getattr(ms, method)() is True
    assert fake.count(path) == 1


async def test_simple_commands_failure(fake, make_server) -> None:
    """A Failure status is reported as False."""
    fake.set("Playback/Play", '<Response Status="Failure"/>')
    ms = await make_server()
    assert await ms.play() is False


async def test_volume(fake, make_server) -> None:
    """Volume up/down/set and relative changes."""
    fake.set(
        "Playback/Volume",
        '<Response Status="OK"><Item Name="Level">0.54999</Item></Response>',
    )
    ms = await make_server()
    assert await ms.volume_up() == 0.54999
    assert fake.params("Playback/Volume") == {"Level": "0.1", "Relative": "1"}
    assert await ms.volume_down(0.2) == 0.54999
    assert fake.params("Playback/Volume") == {"Level": "-0.2", "Relative": "1"}
    assert await ms.set_volume_relative(-0.05) == 0.54999
    assert fake.params("Playback/Volume") == {"Level": "-0.05", "Relative": "1"}
    assert await ms.set_volume_level(0.5) == 0.54999
    assert fake.params("Playback/Volume") == {"Level": "0.5"}


@pytest.mark.parametrize("volume", [-0.1, 1.1])
async def test_set_volume_out_of_range(fake, make_server, volume: float) -> None:
    """An out of range volume raises."""
    ms = await make_server()
    with pytest.raises(ValueError, match="not in range"):
        await ms.set_volume_level(volume)


async def test_mute(fake, make_server) -> None:
    """Mute reports the resulting state."""
    fake.set("Playback/Mute", '<Response Status="OK"><Item Name="State">1</Item></Response>')
    ms = await make_server()
    assert await ms.mute(True) is True
    assert fake.params("Playback/Mute")["Set"] == "1"
    fake.set("Playback/Mute", '<Response Status="OK"><Item Name="State">0</Item></Response>')
    assert await ms.mute(False) is False
    assert fake.params("Playback/Mute")["Set"] == "0"


async def test_position(fake, make_server) -> None:
    """Position query, absolute seek and relative seek."""
    fake.set(
        "Playback/Position",
        '<Response Status="OK"><Item Name="Position">5000</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_position() == 5000
    assert await ms.set_position(1000) is True
    assert fake.params("Playback/Position")["Position"] == "1000"
    assert await ms.media_seek(2000) is True
    assert fake.params("Playback/Position")["Position"] == "2000"
    assert await ms.seek_relative(3000) is True
    assert fake.params("Playback/Position")["Position"] == "8000"
    assert await ms.seek_relative(-9000) is True
    assert fake.params("Playback/Position")["Position"] == "0"


async def test_repeat(fake, make_server) -> None:
    """Repeat can be queried and set."""
    fake.set(
        "Playback/Repeat",
        '<Response Status="OK"><Item Name="Mode">Playlist</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_repeat() is RepeatMode.PLAYLIST
    assert "Mode" not in fake.params("Playback/Repeat")
    assert await ms.set_repeat(RepeatMode.TRACK) is True
    assert fake.params("Playback/Repeat")["Mode"] == "Track"


async def test_repeat_unknown_mode(fake, make_server) -> None:
    """An unrecognised repeat mode falls back to UNKNOWN."""
    fake.set(
        "Playback/Repeat",
        '<Response Status="OK"><Item Name="Mode">Wibble</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_repeat() is RepeatMode.UNKNOWN


async def test_repeat_unsupported(fake, make_server) -> None:
    """An unsupported function raises UnsupportedRequestError cleanly."""
    ms = await make_server()
    with pytest.raises(UnsupportedRequestError):
        await ms.set_repeat(RepeatMode.OFF)


async def test_shuffle(fake, make_server) -> None:
    """Shuffle can be queried and set, including the bool wrapper."""
    fake.set(
        "Playback/Shuffle",
        '<Response Status="OK"><Item Name="Mode">On</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_shuffle() is ShuffleMode.ON
    assert await ms.set_shuffle_mode(ShuffleMode.RESHUFFLE) is True
    assert fake.params("Playback/Shuffle")["Mode"] == "Reshuffle"
    assert await ms.set_shuffle(True) is True
    assert fake.params("Playback/Shuffle")["Mode"] == "On"
    assert await ms.set_shuffle(False) is True
    assert fake.params("Playback/Shuffle")["Mode"] == "Off"


async def test_loudness(fake, make_server) -> None:
    """Loudness can be queried and set."""
    fake.set(
        "Playback/Loudness",
        '<Response Status="OK"><Item Name="Loudness">1</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_loudness() is True
    assert await ms.set_loudness(False) is True
    assert fake.params("Playback/Loudness")["Set"] == "0"
    fake.set(
        "Playback/Loudness",
        '<Response Status="OK"><Item Name="State">0</Item></Response>',
    )
    assert await ms.get_loudness() is False


async def test_load_dsp_preset(fake, make_server) -> None:
    """A DSP preset can be loaded by name."""
    fake.set("Playback/LoadDSPPreset", OK)
    ms = await make_server()
    assert await ms.load_dsp_preset("Movie", "Den") is True
    params = fake.params("Playback/LoadDSPPreset")
    assert params["Name"] == "Movie"
    assert params["Zone"] == "Den"
    with pytest.raises(ValueError, match="name is required"):
        await ms.load_dsp_preset("")


async def test_link_and_unlink_zones(fake, make_server) -> None:
    """Zones can be linked and unlinked."""
    fake.set("Playback/LinkZones", OK)
    fake.set("Playback/UnlinkZones", OK)
    fake.set("Playback/Zones", ZONES)
    ms = await make_server()
    zones = await ms.get_zones()
    assert await ms.link_zones(zones[0], zones[1]) is True
    assert fake.params("Playback/LinkZones") == {"Zone1": "10081", "Zone2": "10074"}
    assert await ms.unlink_zone("Den") is True
    assert fake.params("Playback/UnlinkZones") == {"Zone": "Den"}


async def test_link_zones_unsupported(fake, make_server) -> None:
    """Link zones raises cleanly when the function is missing."""
    ms = await make_server()
    with pytest.raises(UnsupportedRequestError):
        await ms.link_zones(1, 2)


async def test_set_active_zone(fake, make_server) -> None:
    """The active zone can be set by name."""
    fake.set("Playback/SetZone", OK)
    ms = await make_server()
    assert await ms.set_active_zone("Den") is True
    assert fake.params("Playback/SetZone")["Zone"] == "Den"
    with pytest.raises(ValueError, match="zone is required"):
        await ms.set_active_zone("")


async def test_current_playlist(fake, make_server) -> None:
    """The playing now list is parsed and image urls added without N awaits."""
    fake.set("Playback/Playlist", PLAYLIST_JSON, content_type="application/json")
    ms = await make_server()
    resp = await ms.get_current_playlist()
    assert len(resp) == 2
    assert resp[0]["Name"] == "Lean Beef Patty"
    assert "ImageURL" in resp[0]
    assert "ThumbnailSize=small" in resp[1]["ImageURL"]
    # one token fetch for the whole list, not one per item
    assert fake.count("Authenticate") == 1
    assert fake.params("Playback/Playlist")["Action"] == "JSON"


async def test_current_playlist_custom_fields(fake, make_server) -> None:
    """Custom fields are passed through."""
    fake.set("Playback/Playlist", "[]", content_type="application/json")
    ms = await make_server()
    assert await ms.get_current_playlist(fields=["Key", "Rating"]) == []
    assert fake.params("Playback/Playlist")["Fields"] == "Key,Rating"
    assert fake.count("Authenticate") == 0


async def test_playlists(fake, make_server) -> None:
    """Stored playlists are parsed."""
    fake.set("Playlists/List", PLAYLISTS)
    ms = await make_server()
    playlists = await ms.get_playlists()
    assert playlists == [
        Playlist("1234", "Favourites", "Top\\Favourites", "Playlist"),
        Playlist("1235", "Chill", "Top\\Chill", "Playlist"),
    ]


async def test_playlists_attribute_form(fake, make_server) -> None:
    """Playlists expressed as Item attributes also parse."""
    fake.set(
        "Playlists/List",
        '<Response Status="OK"><Item ID="1" Name="A" Path="P" Type="Playlist"/></Response>',
    )
    ms = await make_server()
    assert await ms.get_playlists() == [Playlist("1", "A", "P", "Playlist")]


async def test_playlists_failure(fake, make_server) -> None:
    """A Failure status yields an empty list."""
    fake.set("Playlists/List", '<Response Status="Failure"/>')
    ms = await make_server()
    assert await ms.get_playlists() == []


async def test_playlist_files(fake, make_server) -> None:
    """The files in a stored playlist are returned."""
    fake.set("Playlist/Files", BROWSE_FILES, content_type="application/json")
    ms = await make_server()
    files = await ms.get_playlist_files("1234", fields=["Rating"])
    assert len(files) == 2
    params = fake.params("Playlist/Files")
    assert params["Playlist"] == "1234"
    assert params["Action"] == "JSON"
    assert "Rating" in params["Fields"]
    with pytest.raises(ValueError, match="playlist_id is required"):
        await ms.get_playlist_files("")


async def test_play_playlist(fake, make_server) -> None:
    """A playlist can be played, optionally appending."""
    fake.set("Playback/PlayPlaylist", OK)
    ms = await make_server()
    assert await ms.play_playlist("abc") is True
    assert fake.params("Playback/PlayPlaylist")["PlaylistType"] == "Path"
    assert "PlayMode" not in fake.params("Playback/PlayPlaylist")
    assert await ms.play_playlist("1", playlist_type="ID", play_mode=PlayMode.ADD) is True
    params = fake.params("Playback/PlayPlaylist")
    assert params["PlaylistType"] == "ID"
    assert params["PlayMode"] == "Add"


async def test_play_file_and_item(fake, make_server) -> None:
    """Files and items can be played with an optional play mode."""
    fake.set("Playback/PlayByFilename", OK)
    fake.set("File/GetInfo", OK)
    ms = await make_server()
    assert await ms.play_file("/x/y.flac") is True
    assert fake.params("Playback/PlayByFilename")["Filenames"] == "/x/y.flac"
    assert await ms.play_file("/x/y.flac", play_mode=PlayMode.NEXT_TO_PLAY) is True
    assert fake.params("Playback/PlayByFilename")["PlayMode"] == "NextToPlay"
    assert await ms.play_item("12345", play_mode=PlayMode.ADD) is True
    params = fake.params("File/GetInfo")
    assert params["Action"] == "Play"
    assert params["PlayMode"] == "Add"


async def test_browse_children(fake, make_server) -> None:
    """Browse children returns the raw name/value dict."""
    fake.set("Browse/Children", BROWSE_CHILDREN)
    ms = await make_server()
    assert await ms.browse_children(1) == {"1000": "Audio", "1001": "Video"}
    params = fake.params("Browse/Children")
    assert params["Version"] == "2"
    assert params["ID"] == "1"


async def test_browse_files(fake, make_server) -> None:
    """Browse files returns a list of dicts."""
    fake.set("Browse/Files", BROWSE_FILES, content_type="application/json")
    ms = await make_server()
    files = await ms.browse_files(5, fields=["Rating"])
    assert len(files) == 2
    params = fake.params("Browse/Files")
    assert params["ID"] == "5"
    assert "Rating" in params["Fields"]


async def test_play_browse_files(fake, make_server) -> None:
    """Browse files can be played with either play_next or play_mode."""
    fake.set("Browse/Files", OK)
    ms = await make_server()
    assert await ms.play_browse_files(5) == {}
    assert "PlayMode" not in fake.params("Browse/Files")
    await ms.play_browse_files(5, play_next=True)
    assert fake.params("Browse/Files")["PlayMode"] == "NextToPlay"
    await ms.play_browse_files(5, play_next=False)
    assert fake.params("Browse/Files")["PlayMode"] == "Add"
    await ms.play_browse_files(5, play_mode=PlayMode.ADD)
    assert fake.params("Browse/Files")["PlayMode"] == "Add"


async def test_search_files(fake, make_server) -> None:
    """Search returns matching files, honouring the limit."""
    fake.set("Files/Search", BROWSE_FILES, content_type="application/json")
    ms = await make_server()
    assert len(await ms.search_files("[Artist]=[x]")) == 2
    assert len(await ms.search_files("[Artist]=[x]", limit=1)) == 1
    assert fake.params("Files/Search")["Action"] == "JSON"
    with pytest.raises(ValueError, match="No query"):
        await ms.search_files("")


async def test_play_search(fake, make_server) -> None:
    """Play search issues an Action=Play request."""
    fake.set("Files/Search", OK)
    ms = await make_server()
    assert await ms.play_search("[Artist]=[x]", play_next=True) == {}
    params = fake.params("Files/Search")
    assert params["Action"] == "Play"
    assert params["PlayMode"] == "NextToPlay"
    with pytest.raises(ValueError, match="No query"):
        await ms.play_search("")


async def test_audio_path(fake, make_server) -> None:
    """The audio path is parsed."""
    fake.set("Playback/AudioPath", AUDIO_PATH)
    ms = await make_server()
    assert await ms.get_audio_path() == AudioPath(True, ["No changes are being made"])


async def test_audio_path_failure(fake, make_server) -> None:
    """A failure yields an empty audio path."""
    fake.set("Playback/AudioPath", '<Response Status="Failure"/>')
    ms = await make_server()
    assert await ms.get_audio_path() == AudioPath()


async def test_audio_path_direct(fake, make_server) -> None:
    """AudioPathDirect reports whether the path is direct."""
    fake.set(
        "Playback/AudioPathDirect",
        '<Response Status="OK"><Item Name="Direct">yes</Item></Response>',
    )
    ms = await make_server()
    assert await ms.get_audio_path_direct() == AudioPath(True)
    fake.set("Playback/AudioPathDirect", '<Response Status="Failure"/>')
    assert await ms.get_audio_path_direct() == AudioPath(False)


async def test_ui_info(fake, make_server) -> None:
    """The UI mode is parsed, unknown values falling back."""
    fake.set(
        "UserInterface/Info",
        '<Response Status="OK"><Item Name="Mode">3</Item></Response>',
    )
    ms = await make_server()
    mode, raw = await ms.get_ui_info()
    assert mode is ViewMode.THEATER
    assert raw == {"Mode": "3"}
    assert await ms.get_view_mode() is ViewMode.THEATER
    fake.set(
        "UserInterface/Info",
        '<Response Status="OK"><Item Name="Mode">99</Item></Response>',
    )
    assert await ms.get_view_mode() is ViewMode.UNKNOWN
    fake.set("UserInterface/Info", OK)
    assert await ms.get_view_mode() is ViewMode.UNKNOWN


async def test_send_key_presses(fake, make_server) -> None:
    """A plain string is sent verbatim; a sequence is joined with ';'."""
    fake.set("Control/Key", OK)
    ms = await make_server()
    assert await ms.send_key_presses("Up") is True
    assert fake.params("Control/Key")["Key"] == "Up"
    assert await ms.send_key_presses(["Up", "Down"]) is True
    assert fake.params("Control/Key")["Key"] == "Up;Down"
    assert await ms.send_key_presses([KeyCommand.PAGE_UP, "Enter"], focus=False) is True
    params = fake.params("Control/Key")
    assert params["Key"] == "Page Up;Enter"
    assert params["Focus"] == "0"
    with pytest.raises(ValueError, match="No keys"):
        await ms.send_key_presses([])
    with pytest.raises(ValueError, match="No keys"):
        await ms.send_key_presses([""])


async def test_send_mcc(fake, make_server) -> None:
    """MCC commands are sent with the expected params."""
    fake.set("Control/MCC", OK)
    ms = await make_server()
    assert await ms.send_mcc(MCC.PLAY_PAUSE) is True
    params = fake.params("Control/MCC")
    assert params["Command"] == "10000"
    assert params["Block"] == "1"
    assert "Parameter" not in params
    assert await ms.send_mcc(10005, param=4, block=False, zone="Den") is True
    params = fake.params("Control/MCC")
    assert params["Parameter"] == "4"
    assert params["Block"] == "0"
    assert params["Zone"] == "Den"


async def test_stop_after_helpers(fake, make_server) -> None:
    """The stop-after helpers use the documented MCC ids."""
    fake.set("Control/MCC", OK)
    ms = await make_server()
    assert await ms.stop_after_current() is True
    assert fake.params("Control/MCC")["Command"] == "10036"
    assert await ms.stop_after_delay(15, zone="Den") is True
    params = fake.params("Control/MCC")
    assert params["Command"] == "10067"
    assert params["Parameter"] == "15"


async def test_run_command_line(fake, make_server) -> None:
    """Command line arguments are forwarded."""
    fake.set("Control/CommandLine", OK)
    ms = await make_server()
    assert await ms.run_command_line("/Play") is True
    assert fake.params("Control/CommandLine")["Arguments"] == "/Play"
    with pytest.raises(ValueError, match="arguments are required"):
        await ms.run_command_line("")


async def test_run_command_line_unsupported(fake, make_server) -> None:
    """An unsupported Control/CommandLine raises cleanly."""
    ms = await make_server()
    with pytest.raises(UnsupportedRequestError):
        await ms.run_command_line("/Play")


async def test_zone_object_addressing(fake, make_server) -> None:
    """A Zone instance is always addressed by ID."""
    zone = Zone({"ZoneID0": "10074", "ZoneName0": "Family Room"}, 0, 1)
    fake.set("Playback/Play", OK)
    ms = await make_server()
    await ms.play(zone)
    assert fake.params("Playback/Play") == {"Zone": "10074", "ZoneType": "ID"}
