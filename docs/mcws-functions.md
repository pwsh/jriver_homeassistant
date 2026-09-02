---
title: MCWS reference
nav_order: 99
---

# MCWS function catalogue (scraped from a live MC 36.0.31 /MCWS/v1/doc, 2026-09-02)

This is the full list of functions the Media Center web service exposes. It was scraped
from the `/MCWS/v1/doc` page served by a live Media Center 36.0.31 instance, so it
describes that version; older servers expose fewer functions. The integration wraps only a
subset of these — the catalogue is here as a reference when extending the vendored client.

The "Click here" example links below are relative links back to the Media Center instance
that served the original page, so they do not resolve from this site.

### Alive

Simple query to ensure the server is running and to check versions.
### Response:

- RuntimeGUID: The runtime GUID of this web service.
- LibraryVersion: The version number of the library.
- ProgramName: The name of the program.
- ProgramVersion: The version number of the program.
- FriendlyName: The friendly name of this server.
- AccessKey: The access key of this server.
- ProductVersion: The product version.
- Platform: The computer platform, either Windows, Mac, or Linux.
### Examples:

  - Example: [Click here](Alive)
### Authenticate

Simple query to test and establish authentication.
### Response:

- Token: The token that can be appended to calls in place of HTTP authentication.
- ReadOnly: Whether the token is for read-only access.  If not present or false, the token has full rights.
- PreLicensed: True if MC is running in restricted mode
### Examples:

  - Example: [Click here](Authenticate)

## Playback

### Playback/Play

- Start playback (does nothing if already playing).

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Play?Zone=-1&ZoneType=ID&NoUI=1)
### Playback/PlayPause

- Start playback or toggle the pause state.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayPause?Zone=-1&ZoneType=ID&NoUI=1)
### Playback/Pause

- Set the pause state.

**Parameters:**

  - State: The new pause state (0: unpaused, 1: paused, -1: toggle). (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Pause?State=-1&Zone=-1&ZoneType=ID)
### Playback/Next

- Advance to the next track.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Block: Set to one to block the call from returning until the next has finished. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Next?Zone=-1&ZoneType=ID)
### Playback/Previous

- Advance to the previous track.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Block: Set to one to block the call from returning until the previous has finished. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Previous?Zone=-1&ZoneType=ID)
### Playback/Stop

- Stops playback.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Stop?Zone=-1&ZoneType=ID)
### Playback/StopAll

- Stops playback in all zones.

**Response:**


**Examples:**

  - Example: [Click here](Playback/StopAll)
### Playback/Position

- Get / set the position.

**Parameters:**

  - Position: The position to seek to, in milliseconds or percent. (default: <blank>)
  - Relative: When set to 1, 'Position' will be added to the current position to allow jumping forward.  When set to -1, 'Position' will be subtracted from the current position to allow jumping backwards.  Use a 'Position' of -1 to jump the default amount based on the media type. (default: <blank>)
  - Mode: 'ms' for milliseconds. '%' for percent. 'chapter' for chapter index (0-based, local playback only). (default: ms)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Position: The position in milliseconds (after applying changes, if any).

**Examples:**

  - Example: [Get current position](Playback/Position)
  - Example: [Seek 10 seconds into playing file](Playback/Position?Position=10000)
  - Example: [Jump backward (default amount)](Playback/Position?Position=-1&Relative=-1)
  - Example: [Jump forward (default amount)](Playback/Position?Position=-1&Relative=1)
  - Example: [Jump forward 60 seconds](Playback/Position?Position=60000&Relative=1)
### Playback/Volume

- Get / set the volume.

**Parameters:**

  - Level: Level to change the volume to as a decimal from 0 to 1.  Leave this blank to leave the volume unchanged and query for the current volume. (default: <blank>)
  - Relative: When set to 1, 'Level' will be added to the current volume to allow increasing or descreasing the volume by some amount. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Level: The volume as a decimal between 0 and 1 (after applying changes, if any).
  - Display: The volume as a display string (after applying changes, if any).

**Examples:**

  - Example: [Get current volume](Playback/Volume)
  - Example: [Set volume to 75%](Playback/Volume?Level=0.75)
  - Example: [Increase volume 10%](Playback/Volume?Level=0.1&Relative=1)
  - Example: [Decrease volume 10%](Playback/Volume?Level=-0.1&Relative=1)
### Playback/Mute

- Set the mute.

**Parameters:**

  - Set: When set to 1, playback will mute.  When set to 0, playback will unmute. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - State: The mute state after the setting.

**Examples:**

  - Example: [Mute playback](Playback/Mute?Set=1)
### Playback/Repeat

- Get / set the repeat state (Modes: Off, Playlist, Track, Stop, Toggle).

**Parameters:**

  - Mode: The new repeat mode.  Leave this blank to query for the current mode. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Mode: The repeat mode (after applying changes, if any).

**Examples:**

  - Example: [Get current repeat mode](Playback/Repeat)
  - Example: [Set repeat mode to off](Playback/Repeat?Mode=Off)
  - Example: [Set repeat mode to repeat playlist](Playback/Repeat?Mode=Playlist)
  - Example: [Toggle the repeat mode](Playback/Repeat?Mode=Toggle)
### Playback/Shuffle

- Get / set the shuffle state (Modes: Off, On, Automatic, Toggle, Reshuffle).

**Parameters:**

  - Mode: The new shuffle mode.  Leave this blank to query for the current mode. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Mode: The shuffle mode (after applying changes, if any).

**Examples:**

  - Example: [Get current shuffle mode](Playback/Shuffle)
  - Example: [Set shuffle mode to off](Playback/Shuffle?Mode=Off)
  - Example: [Set shuffle mode to on](Playback/Shuffle?Mode=On)
  - Example: [Reshuffle the current playlist](Playback/Shuffle?Mode=Reshuffle)
### Playback/Info

- Get information about the current playback.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Fields: A semi-colon delimited list of additional fields to include in the response. (default: <blank>)
  - Formatted: Set to 1 if you want a formatted values (like a formatted date). (default: 1)

**Response:**

  - ZoneID: The zone ID of this zone.
  - ZoneName: The display name of this zone.
  - State: The playback state of the player.
  - FileKey: The database key of the playing file.
  - NextFileKey: The database key of the next file to play.
  - PositionMS: The position of the playback in milliseconds.
  - DurationMS: The duration of the playing file in milliseconds.
  - ElapsedTimeDisplay: The elapsed playback time as a display friendly string.
  - RemainingTimeDisplay: The remaining playback time as a display friendly string.
  - TotalTimeDisplay: The total playback time as a display friendly string.
  - PositionDisplay: The playback position as a display friendly string.
  - PlayingNowPosition: The index of the current track in Playing Now.
  - PlayingNowTracks: The number of files in Playing Now.
  - PlayingNowPositionDisplay: The current Playing Now position formatted for display.
  - PlayingNowChangeCounter: A counter that increments any time the playlist is changed.
  - Bitrate: The current bitrate, in kbps.
  - Bitdepth: The current bitdepth.
  - SampleRate: The current sample rate in Hz.
  - Channels: The number of audio channels in the current output.
  - Chapter: The current playback chapter.
  - ChapterList: A list of chapters in the current file.
  - Volume: The current volume.
  - VolumeDisplay: A display friendly string version of the current volume.
  - ImageURL: An image URL for the current file.
  - Artist: Artist of current file.
  - Album: Album of current file.
  - Name: Name of current file.
  - Rating: Rating of current file.
  - Status: Playback status as a displayable string.
  - LipSyncAdjustmentMS: The current adjustment for lip-sync.
  - LinkedZones: Semicolon delimited list of zone names in the link (only provided if this zone is part of a link).
  - Fields: The value of specified fields.

**Examples:**

  - Example: [Get information](Playback/Info?Zone=-1)
### Playback/Playlist

- Get the current playlist.

**Parameters:**

  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Get playlist](Playback/Playlist?Zone=-1)
### Playback/Zones

- Get information about all zones.

**Parameters:**

  - Hidden: Set to 1 to see hidden zones. (default: <blank>)

**Response:**

  - NumberZones: The number of zones.
  - CurrentZoneID: The current zone ID.
  - CurrentZoneIndex: The current zone index.
  - ZoneName#: The name of the zone at index #.
  - ZoneID#: The ID of the zone at index #.
  - ZoneGUID#: The GUID of the zone at index #.
  - ZoneDLNA#: Whether the zone at index # is a DLNA zone.

**Examples:**

  - Example: [Get zone information](Playback/Zones)
### Playback/SetZone

- Set the active zone.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/SetZone?Zone=-1&ZoneType=ID)
### Playback/LinkZones

- Links the specified zones.

**Parameters:**

  - Zone1: The zone the command is targetted for. (default: -1)
  - ZoneType1: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Zone2: The zone the command is targetted for. (default: -1)
  - ZoneType2: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/LinkZones?Zone1=-1&ZoneType1=ID&Zone2=-1&ZoneType2=ID)
### Playback/UnlinkZones

- Unlinks the specified zone.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/UnlinkZones?Zone=-1&ZoneType=ID)
### Playback/PlayByIndex

- Play a file in Playing Now.

**Parameters:**

  - Index: The index of the file to play (0 based). (default: 0)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Play the first file](Playback/PlayByIndex?Index=0&Zone=-1)
### Playback/PlayByKey

- Play a file (or files) by database key.

**Parameters:**

  - Key: The list of keys of the files to play (seperated by comma). (default: -1)
  - Location: The location of the file.  Use 'End' to add to the end of the current playlist, 'Next' to play next, or a number to insert at a specific index. (default: <blank>)
  - Album: Set to 1 to play the entire album starting at this file. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayByKey?Key=-1&NoUI=1&Zone=-1&ZoneType=ID)
### Playback/PlayDoctor

- Plays using Play Doctor.

**Parameters:**

  - Seed: The Play Doctor seed. (default: <blank>)
  - AllCloud: All files are selected/played from CloudPlay. (default: <blank>)
  - Key: The file to start with (optional) (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayDoctor?NoUI=1&Zone=-1&ZoneType=ID)
### Playback/PlayLive

- Play from a live source.

**Parameters:**

  - Mode: The mode of live playback. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayLive?NoUI=1&Zone=-1&ZoneType=ID)
### Playback/LoadDSPPreset

- Loads a DSP preset.

**Parameters:**

  - Name: The name of the preset to load (or a saved preset file). (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/LoadDSPPreset?Zone=-1&ZoneType=ID)
### Playback/SaveDSPPreset

- Save the DSP preset.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/SaveDSPPreset?Zone=-1&ZoneType=ID)
### Playback/SetPlaylist

- Set the current playlist.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Playlist: A serialized playlist. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playback/SetPlaylist?Zone=-1&ZoneType=ID)
### Playback/ClearPlaylist

- Clear the current playlist and stop playback.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Clear Playing Now](Playback/ClearPlaylist)
### Playback/EditPlaylist

- Edit the current playlist (move, remove, etc.)

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Action: The edit action (Move, Remove). (default: <blank>)
  - Source: The source file index (0-based). (default: <blank>)
  - Target: The target index when moving (0-based). (default: <blank>)

**Response:**


**Examples:**

  - Example: [Remove the first file](Playback/EditPlaylist?Action=Remove&Source=0)
  - Example: [Move a track to the first position](Playback/EditPlaylist?Action=Move&Source=9&Target=0)
### Playback/PlayAdvanced

- Plays files using a PLAY_COMMAND object (for internal use).

**Parameters:**

  - PlayCommand: Serialized PLAY_COMMAND object (for internal use only). (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayAdvanced?NoUI=1&Zone=-1&ZoneType=ID)
### Playback/UpdatePlayStats

- Update the play stats.

**Parameters:**

  - File: The file to update play stats for. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playback/UpdatePlayStats)
### Playback/PlayByFilename

- Play a set of files by filename.

**Parameters:**

  - Filenames: A pipe delimited list of filenames to play. (default: <blank>)
  - Location: The location of the file.  Use 'End' to add to the end of the current playlist, 'Next' to play next, or a number to insert at a specific index. (default: End)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayByFilename?Location=End&NoUI=1&Zone=-1&ZoneType=ID)
### Playback/AudioPath

- Gets the audio path information for the current playback.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - AudioPath: The list of changes being made.
  - Direct: Whether we're in direct mode.

**Examples:**

  - Example: [Click here](Playback/AudioPath?Zone=-1&ZoneType=ID)
### Playback/AudioPathDirect

- Returns whether the audio path is direct.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Direct: Whether we're in direct mode.

**Examples:**

  - Example: [Click here](Playback/AudioPathDirect?Zone=-1&ZoneType=ID)
### Playback/PlayPlaylist

- Plays a playlist.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Playlist: The ID of the playlist to play or the path. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayPlaylist?Zone=-1&ZoneType=ID&PlaylistType=ID&NoUI=1)
### Playback/PlayRadioParadise

- Plays Radio Paradise.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Channel: The channel to play (defaults to zero). (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)

**Response:**

  - PlaylistID: The playlist ID of the Radio Paradise stream.

**Examples:**

  - Example: [Click here](Playback/PlayRadioParadise?Zone=-1&ZoneType=ID&NoUI=1)
### Playback/PlayRadioJRiver

- Plays Radio JRiver.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Station: The name of the station. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Playback/PlayRadioJRiver?Zone=-1&ZoneType=ID&NoUI=1)
### Playback/Divert

- Diverts playback.

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - Destination: The ID of the destination zone. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playback/Divert?Zone=-1&ZoneType=ID)

## Library

### Library/List

- Gets a list of libraries.

**Response:**

  - NumberOfLibraries: The number of libraries.
  - DefaultLibrary: The index of the default library.

**Examples:**

  - Example: [Click here](Library/List)
### Library/Load

- Loads a library.

**Parameters:**

  - Library: The index of the library to load (from Library/List). (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Library/Load)
### Library/Get

- Get a copy of the library.

**Parameters:**

  - Settings: Whether settings should be included with the library. (default: 0)
  - IncrementalFileSignaturesXML: A block of XML containing file signatures.  When this is provided, only changed files will be returned. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Library/Get?Settings=0)
### Library/GetStats

- Get some stats about the library.

**Response:**

  - Files: The number of files in the library.
  - AudioFiles: The number of audio files in the library.
  - ImageFiles: The number of image files in the library.
  - VideoFiles: The number of video files in the library.
  - OtherFiles: The number of other files in the library.
  - Artists: The number of artists in the library.
  - Albums: The number of albums in the library.

**Examples:**

  - Example: [Click here](Library/GetStats)
### Library/Merge

- Merge changes into the library.

**Parameters:**

  - Delta: A binary package describing the changes. (default: <blank>)

**Response:**

  - MasterRevision: Library 'Master' revision number after changes have been applied.
  - SyncRevision: Library 'Sync' revision number after changes have been applied.
  - NewFiles: A semicolon delimited list of new files in the form: client key;server key;client key;server key;etc.

**Examples:**

  - Example: [Click here](Library/Merge)
### Library/GetRevision

- Get the revision number of the library.

**Response:**

  - Master: The master revision number of the database.
  - Sync: The revision number of the database (only included sync-worthy revisions).
  - LibraryStartup: Timestamp of the Library Startup (ie. the last reset of the revision counter).

**Examples:**

  - Example: [Click here](Library/GetRevision)
### Library/Fields

- Gets the fields in the library.

**Response:**


**Examples:**

  - Example: [Click here](Library/Fields)
### Library/CreateField

- Creates or updates a library field.

**Parameters:**

  - Name: The name of the field. (default: <blank>)
  - Type: The data type of the field (string or integer). (default: string)
  - Expression: An expression for a calcualted field. (default: <blank>)

**Response:**

  - Field: The name of the updated or created field.

**Examples:**

  - Example: [Click here](Library/CreateField?Type=string)
### Library/DeleteField

- Deletes a library field.

**Parameters:**

  - Name: The name of the field. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Library/DeleteField)
### Library/CreateFile

- Creates a library file.

**Response:**

  - Key: The key of the new file.

**Examples:**

  - Example: [Click here](Library/CreateFile)
### Library/Connect

- Connects to a remote library.

**Parameters:**

  - URL: A URL for connecting to a library server. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Library/Connect)
### Library/Values

- Get a list of values from the database (artists, albums, etc.).

**Parameters:**

  - Filter: Empty to get all values for a particular field, or some search to get matching values from any number of fields. (default: <blank>)
  - Field: A comma-delimited list of fields to get values from (leave blank when searching to search default fields). (default: <blank>)
  - Files: A search to use to get the files to retrieve values from (use empty to use all imported files). (default: <blank>)
  - Limit: Maximum number of values to return. (default: <blank>)

**Response:**


**Examples:**

  - Example: [All artists](Library/Values?Field=Artist)
  - Example: [Image keywords](Library/Values?Field=Keywords&Files=[Media Type]=[Image])
  - Example: [Search values for 'Dylan'](Library/Values?Filter=Dylan)
  - Example: [Search specific audio values for 'Rock'](Library/Values?Filter=Rock&Field=Genre,Artist,Album&Files=[Media Type]=[Audio])
### Library/Import

- Imports files from a folder.

**Parameters:**

  - Path: The path to search for files. (default: <blank>)
  - Block: Whether the import should finish before the function returns. (default: 0)

**Response:**


**Examples:**

  - Example: [Click here](Library/Import?Block=0)

## Playlists

### Playlists/List

- Gets a list of all playlists.

**Parameters:**

  - Group: Only return playlists within this group. (default: <blank>)
  - IncludeMediaTypes: Return the media types of files in the playlist (comma separated list).  Only valid for regular playlists, not smartlists. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Get list of all playlists.](Playlists/List)
  - Example: [Get list of all playlists within the 'Smartlists' group.](Playlists/List?Group=Smartlists)
  - Example: [Get list of all playlists and return the media types.](Playlists/List?IncludeMediaTypes=1)
### Playlists/Add

- Add a new playlist.

**Parameters:**

  - Type: The type of playlist to create (Playlist, Smartlist, Playlist Group). (default: <blank>)
  - Path: The full path to the new playlist. (default: <blank>)
  - Search: The search string to use to get the files to retrieve values from (use empty to use all imported files). (default: <blank>)
  - CreateMode: The creation mode (Overwite: overwrite the existing playlist at the path; Rename: rename the new playlist if a playlist already exists at the path). (default: <blank>)

**Response:**

  - PlaylistID: The ID of the newly created playlist.

**Examples:**

  - Example: [Create 'One Random Album' Smartlist](Playlists/Add?Type=Smartlist&Path=One Random Album&Search=[Media Type]=[Audio] ~n=1 ~a&CreateMode=Overwrite)

## Playlist

### Playlist/Files

- Gets the files of a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - ResetCache: Reset the cache so that Smartlist files are regenerated. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/Files?PlaylistType=ID&Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID&ResetCache=1)
### Playlist/Delete

- Deletes the playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/Delete?PlaylistType=ID)
### Playlist/AddFile

- Add a file to a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/AddFile?PlaylistType=ID&File=-1&FileType=Key)
### Playlist/AddFiles

- Adds files to a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - Keys: A comma seperated list of file keys (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/AddFiles?PlaylistType=ID)
### Playlist/RemoveFile

- Remove a file from a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/RemoveFile?PlaylistType=ID&File=-1&FileType=Key)
### Playlist/RemoveFiles

- Remove files from a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - Keys: A comma seperated list of file keys (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/RemoveFiles?PlaylistType=ID)
### Playlist/RemoveDuplicates

- Remove duplicates from a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/RemoveDuplicates?PlaylistType=ID)
### Playlist/Clear

- Clears the playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/Clear?PlaylistType=ID)
### Playlist/MoveFile

- Moves a file in a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - NewIndex: The new index of the file (default: 0)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/MoveFile?PlaylistType=ID&File=-1&FileType=Key&NewIndex=0)
### Playlist/Build

- Builds a playlist.

**Parameters:**

  - Keys: A comma seperated list of keys. (default: <blank>)
  - Playlist: The name of the playlist. (default: <blank>)

**Response:**

  - PlaylistID: The ID of the playlist that gets built.

**Examples:**

  - Example: [Click here](Playlist/Build)
### Playlist/Rename

- Renames a playlist.

**Parameters:**

  - Playlist: The playlist the command is targetted for. (default: <blank>)
  - PlaylistType: The type of value provided in 'Playlist' (ID: playlist id; Path: playlist path). (default: ID)
  - NewName: The new name of the playlist. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Playlist/Rename?PlaylistType=ID)

## Files

### Files/Search

- Perform a database search for files.

**Parameters:**

  - Query: The search string (empty returns full library) (default: <blank>)
  - FilterForUser: Filter the search using the active user account (default: <blank>)
  - Limit: Maximum umber of files to return (default: no limit) (default: <blank>)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Files/Search?Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID)
### Files/Current

- Get the currently selected files.

**Parameters:**

  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Files/Current?Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID)
### Files/GetInfo

- Get information or play a list of files.

**Parameters:**

  - Keys: A comma seperated list of file keys (default: <blank>)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Files/GetInfo?Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID)
### Files/GetLinkExpanded

- Gets the files with the links expanded.

**Parameters:**

  - Keys: A comma seperated list of file keys (default: <blank>)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Files/GetLinkExpanded?Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID)

## File

### File/GetFile

- Get the contents of a file in the database.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Helper: Allows getting sidecar / helper files (used internally). (default: <blank>)
  - Conversion: The conversion settings to use. (default: <blank>)
  - Quality: The conversion quality to use (low, medium, high, etc.). (default: <blank>)
  - Resolution: The resolution of the target device (allows making better conversion decisions). (default: <blank>)
  - AndroidVersion: The Android version of the target device (if applicable). (default: <blank>)
  - Prepare: Set to 1 to prepare the file (useful when waiting for video conversion, etc.). (default: <blank>)
  - Playback: 0: Downloading (not real-time playback); 1: Real-time playback with update of playback statistics, Scrobbling, etc.; 2: Real-time playback, no playback statistics handling. (default: <blank>)
  - Start: The start position for playback.  This is normally seconds (decimal supported), but usage can vary based on playback type. (default: <blank>)
  - MimeType: The mime type to use in the response (leave blank for default mime type). (default: <blank>)
  - HLS: Use HTTP Live Streaming. (default: <blank>)
  - HLSVOD: Use experimental Video-On-Demand HTTP Live Streaming. (default: <blank>)
  - Context: The context used to access the file (used for HTTP Live Streaming). (default: <blank>)

**Response:**

  - PercentPrepared: The integer progress percentage of a file preparation operation, such as transcoding.

**Examples:**

  - Example: [Click here](File/GetFile?File=-1&FileType=Key)
### File/GetImage

- Get an image for a file in the database.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Type: The type of image to get: Thumbnail (default), Full, ThumbnailsBinary (default: Thumbnail)
  - ThumbnailSize: The size of the thumbnail (if type is thumbnail): Small, Medium, Large (default), ExtraLarge (default: <blank>)
  - Rebuild: Whether the thumbnail should be rebuilt (default: <blank>)
  - Version: ThumbnailsBinary only; version of the binary format (default: 1)
  - Width: The width for the returned image. (default: <blank>)
  - Height: The height for the returned image. (default: <blank>)
  - FillTransparency: A color to fill image transparency with (hex number). (default: <blank>)
  - Square: Set to 1 to crop the image to a square aspect ratio. (default: <blank>)
  - Pad: Set to 1 to pad around the image with transparency to fullfill the requested size. (default: <blank>)
  - Format: The preferred image format (jpg or png). (default: jpg)

**Response:**


**Examples:**

  - Example: [Click here](File/GetImage?File=-1&FileType=Key&Type=Thumbnail&Version=1&Format=jpg)
### File/QuickFindCoverArt

- Finds the cover art for a file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)

**Response:**


**Examples:**

  - Example: [Click here](File/QuickFindCoverArt?File=-1&FileType=Key)
### File/SetImage

- Set the image for a file in the database.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Type: The type of image (jpg, gif, etc.). (default: jpg)
  - Image: The image (as base 64 encoded). (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](File/SetImage?File=-1&FileType=Key&Type=jpg)
### File/GetInfo

- Get information or play a file object.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Show file information for file key](File/GetInfo?File=1)
  - Example: [Show file information for filename](File/GetInfo?File=C:\1.mp3&FileType=Filename)
  - Example: [Play file key](File/GetInfo?File=1&Action=Play)
### File/SetInfo

- Set information about a file object.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Field: The field to set. (default: <blank>)
  - Value: The value to set the field to. (default: <blank>)
  - List: Set to 'CSV' and comma delimit (RFC 4180) the field and value to set multiple values in one call. (default: <blank>)
  - Formatted: Set to 1 if you're passing a formatted value (like a formatted date). (default: 1)
  - Dirty: Set to 0 to make the file not dirty. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](File/SetInfo?File=-1&FileType=Key&Formatted=1&Dirty=1)
### File/Rotate

- Rotate an image file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Degrees: The degrees to rotate the image. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](File/Rotate?File=-1&FileType=Key)
### File/Played

- Update the play stats after a file has been played.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)

**Response:**


**Examples:**

  - Example: [Click here](File/Played?File=-1&FileType=Key)
### File/CreateParticle

- Create particles.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Count: The number of particles to create. (default: <blank>)

**Response:**

  - Keys: The keys of the created particles.

**Examples:**

  - Example: [Click here](File/CreateParticle?File=-1&FileType=Key)
### File/Delete

- Deletes a file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Mode: The delete mode (empty for default, 'Disk' for delete from disk, 'Recycle' for recycling. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](File/Delete?File=-1&FileType=Key)
### File/Bookmark

- Gets and sets the bookmark.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Set: The value in milliseconds to set (leave empty to not set and only get) (set to empty to remove) (default: <blank>)

**Response:**

  - Bookmark: The value of the bookmark.

**Examples:**

  - Example: [Click here](File/Bookmark?File=-1&FileType=Key)
### File/GetFilledTemplate

- Get a filled template for a file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - Expression: The expression to evaluate. (default: <blank>)

**Response:**

  - Value: The value of the evaluated expression.

**Examples:**

  - Example: [Click here](File/GetFilledTemplate?File=-1&FileType=Key)
### File/GetPlaylists

- Get playlists for a file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)

**Response:**

  - Playlists: The list of playlists.

**Examples:**

  - Example: [Show playlists for file key](File/GetPlaylists?File=1)
  - Example: [Show playlists for filename](File/GetPlaylists?File=C:\1.mp3&FileType=Filename)

## Browse

### Browse/Children

- Returns child browse items for a location, enabling traversal of the browse hierarchy.

**Parameters:**

  - ID: The parent ID (empty or -1 to start at root). (default: <blank>)
  - Skip: Set to 1 to skip browse levels that contain only one choice. (default: <blank>)
  - ErrorOnMissing: Return on error when the parent node was not found, otherwise returns the root node (disabled by default, set to 1 to enable) (default: 0)

**Response:**


**Examples:**

  - Example: [Click here](Browse/Children?ErrorOnMissing=0)
### Browse/Image

- Gets the image for a browse item.

**Parameters:**

  - ID: The ID of the browse item. (default: <blank>)
  - Fallback: The name of the fallback image to use if ID is invalid. (default: <blank>)
  - FallbackColor: If no image found for ID or fallback, generate an image filled with this color. Use RGBA values (0-255) separated by commas, e.g. FallbackColor=128,240,169[,255], the 4th value is for Alpha and is optional - default is 255. (default: <blank>)
  - NoDefaultImage: If 1, no default image will be provided if no file-based images are available. (default: <blank>)
  - UseStackedImages: If 1, display a group of items with a stack of fanned thumbnails, if 0 use a single thumbnail. (default: 1)
  - Width: The width for the returned image. (default: <blank>)
  - Height: The height for the returned image. (default: <blank>)
  - FillTransparency: A color to fill image transparency with (hex number). (default: <blank>)
  - Square: Set to 1 to crop the image to a square aspect ratio. (default: <blank>)
  - Pad: Set to 1 to pad around the image with transparency to fullfill the requested size. (default: <blank>)
  - Format: The preferred image format (jpg or png). (default: jpg)

**Response:**


**Examples:**

  - Example: [Click here](Browse/Image?UseStackedImages=1&Format=jpg)
### Browse/Files

- Gets files for a browse item.

**Parameters:**

  - ID: The ID of the browse item. (default: <blank>)
  - Action: The action to perform with the files (MPL: return MPL playlist; JSON: Return files as JSON array; Play: plays files; Save: saves the files (as a playlist in the library, etc.); Serialize: return serialized file array (basically a list of file keys); M3U: saves the list as an m3u). (default: mpl)
  - Shuffle: Set to 1 to shuffle the files. (default: <blank>)
  - ActiveFile: A file key to set as active (used as the file that playback starts with, etc.). (default: -1)
  - ActiveFileOnly: Set to 1 to trim the returned files to only contain the active file. (default: <blank>)
  - PlayMode: Play mode flags delimited by commas (Add: adds to end of playlist; NextToPlay: adds files in the next to play position). (default: <blank>)
  - Fields: The fields to include in an MPL (use empty to include all fields) (set to Calculated to include calculated fields). (default: <blank>)
  - NoLocalFilenames: Set to 1 to filter out local filenames from MPL output (since they might be meaningless to a server). (default: <blank>)
  - PlayDoctor: Set to 1 to change the files to a Play Doctor generated playlist using these files as a seed. (default: <blank>)
  - SaveMode: Playlist: playlist (overwrites existing; returns ID) (default: <blank>)
  - SaveName: A backslash delimited path used with the action 'Save'. (default: <blank>)
  - NoUI: Set to one to put the player in no UI mode. (default: 0)
  - Formatted: Set to 1 if you want a formatted value (like a formatted date). (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - ResetCache: Reset the cache so that Smartlist files are regenerated. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Browse/Files?Action=mpl&ActiveFile=-1&NoUI=0&Formatted=0&Zone=-1&ZoneType=ID&ResetCache=1)
### Browse/Reset

- Resets the browse tree.

**Response:**


**Examples:**

  - Example: [Click here](Browse/Reset)
### Browse/Rules

- Returns the rules used for the view.

**Parameters:**

  - Type: Whether you want 'Remote' or 'Tree'. (default: Remote)

**Response:**


**Examples:**

  - Example: [Click here](Browse/Rules?Type=Remote)

## VideoStream

### VideoStream/Get

- Start streaming a video file.

**Parameters:**

  - File: The key of the file. (default: -1)
  - FileType: The type of value provided in 'File' (Key: file key; Filename: filename of file; Selected: the selected file). (default: Key)
  - StreamToken: Unique token to identify the streaming session. Optional, but Recommended. Mandatory to identify the streaming session with other VideoStream calls. (default: <blank>)
  - Preset: Conversion Preset. Low, Medium, High, VeryHigh. Default: Medium (default: Medium)
  - Format: Streaming Format. Available formats: Progressive (progressive CBR file streaming, MPEG-TS), HLSVOD (HTTP Live Streaming Video-on-Demand), HLSLive (HTTP Live Streaming Live playlist). Default: Progressive (default: Progressive)
  - Context: The context used to access the file (used internally for HTTP Live Streaming, do not set manually). (default: <blank>)
  - VideoCodec: The video codec to use. Recommended Codecs for Streaming: mpeg2, h264 (default: <blank>)
  - VideoResolution: The video resolution, including an optional behavior flag. The resolution can be prefixed with either "flex" to avoid upscaling of lower resolution material, or "fixed" to strictly enforce the requested resolution, even if the aspect ratio does not match (anamorphic encoding), Example: VideoResolution=flex1920x1080 (default: <blank>)
  - VideoBitrate: The video bitrate, in kbit/s, eg. VideoBitrate=1000 for 1MBit/s video (default: <blank>)
  - VideoFramerate: The video framerate. If not specified, AutoFPS is used. Prefixing the bitrate with "auto" treats it as a maximum. eg. VideoFramerate=25 for fixed 25 FPS, or VideoFramerate=auto30 for AutoFPS with a maximum of 30 FPS (default: <blank>)
  - AudioCodec: The audio codec to use. Recommended Codecs for Streaming: aac, ac3 (default: <blank>)
  - AudioChannel: The number of audio channel to use. Suggested channel for streaming: 2 (Stereo) or 6 (5.1). The number of channel can be prefixed with "flex" to disable upmixing of sources with fewer channel. Example: AudioChannel=flex6 (default: <blank>)
  - AudioSamplerate: The audio sample rate. Note: Most video streaming codecs are limited to 48000 Hz. If the requested rate is not supported by the encoder, the closest match will be chosen. (default: <blank>)
  - AudioBitrate: The audio bitrate, in kbit/s. Note: Some audio codecs have preset bitrates that should be used for maximum compatibility. (default: <blank>)
  - Playback: 1: Real-time playback with update of playback statistics, Scrobbling, etc.; 2: Real-time playback, no playback statistics handling. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](VideoStream/Get?File=-1&FileType=Key&Preset=Medium&Format=Progressive&Playback=1)
### VideoStream/StreamInfo

- Get audio/subtitle info about an active streaming session

**Parameters:**

  - StreamToken: Unique token to identify the streaming session. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](VideoStream/StreamInfo)
### VideoStream/SelectStream

- Select an audio/subtitle stream for playback (dynamic change only supported on HLSVOD streaming)

**Parameters:**

  - StreamToken: Unique token to identify the streaming session. (default: <blank>)
  - StreamID: ID of the stream, as listed in StreamInfo (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](VideoStream/SelectStream)

## Control

### Control/AnalyzeAudio

- Analyze audio for the specified tree path.

**Parameters:**

  - TreePath: The tree path to analyze. (default: <blank>)
  - Keys: A comma delimited list of keys (instead of a tree path). (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Control/AnalyzeAudio)
### Control/MCC

- Perform a Media Core Command (MCC).

**Parameters:**

  - Command: The command (an integer value from the MC_COMMANDS enumeration; visit DevZone for the command list). (default: <blank>)
  - Parameter: The parameter to the command. (default: 0)
  - Block: 0: return immediately (command is posted and processed asynchronously); 1: wait for the command to finish before returning. (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Play / pause](Control/MCC?Command=10000)
  - Example: [Shuffle Playing Now](Control/MCC?Command=10005&Parameter=2)
### Control/CommandLine

- Run a command line.

**Parameters:**

  - Arguments: The command line arguments (default: <blank>)
  - Target: The target for the command line (uses launcher when empty) (default: <blank>)

**Response:**


**Examples:**

  - Example: [Toggle pause](Control/CommandLine?Arguments=/Command Pause)
### Control/Key

- Simulate the press of a keyboard key.

**Parameters:**

  - Key: The key sequence to simulate, separated by semicolons.  Keys can be a single letter or any of the following special keys: Insert, Menu, Delete, +, -, Left, Right, Up, Down, Backspace, Enter, Escape, Apps, Page Up, Page Down, Home, End, Space, Print Screen, Tab, NumPad0...NumPad9, F1...F24 (default: <blank>)
  - Focus: Brings the program to the front and takes focus if set to 1. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Up](Control/Key?Key=Up&Focus=1)
  - Example: [Right](Control/Key?Key=Right&Focus=1)
  - Example: [Enter](Control/Key?Key=Enter&Focus=1)
  - Example: [Ctrl+C (Copy)](Control/Key?Key=Ctrl;C&Focus=1)
  - Example: [Ctrl+Shift+Left (Jump Back)](Control/Key?Key=Ctrl;Shift;Left&Focus=1)
  - Example: [Win+E (Windows Explorer)](Control/Key?Key=Win;E)

## Handheld

### Handheld/Sync

- Run a sync of an attached handheld.

**Parameters:**

  - Device: The device to sync. (default: <blank>)
  - DeviceType: The type of value provided in 'Device' (Name: device name; ID: session id). (default: Name)
  - ShowWarnings: If warnings are allowed. (default: 1)

**Response:**


**Examples:**

  - Example: [Click here](Handheld/Sync?DeviceType=Name&ShowWarnings=1)

## Television

### Television/SeekInformation

- Gets seek information for television playback.

**Parameters:**

  - File: The base file of the television program. (default: <blank>)
  - Time: The time to get seeking information for. (default: <blank>)

**Response:**

  - AudioSeekByte: The seek byte for the audio stream.
  - VideoSeekByte: The seek byte for the video stream.

**Examples:**

  - Example: [Click here](Television/SeekInformation)
### Television/PlayChannel

- Requests the player to find a TV control and start buffering a TV channel for the client.

**Parameters:**

  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Television/PlayChannel?Channel=-1&Zone=-1&ZoneType=ID)
### Television/GetPlayerServingChannel

- Get the player that was previously started serving the given channel.

**Parameters:**

  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - TVPlayer: The pointer to CTVPlayer object that serves the channel.

**Examples:**

  - Example: [Click here](Television/GetPlayerServingChannel?Channel=-1&Zone=-1&ZoneType=ID)
### Television/GetJTVFile

- Get the jtv file from the given TVPlayer for the client to play.

**Parameters:**

  - Channel: The key of the TV channel to play. (default: -1)
  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - JTVFilename: The jtv file the server serves.
  - JTVFileKey: The key of the jtv file the server serves
  - PlaybackInfo: The PlaybackInfo tag.

**Examples:**

  - Example: [Click here](Television/GetJTVFile?Channel=-1&TVPlayer=0&Zone=-1&ZoneType=ID)
### Television/StopChannel

- Informs TV control that a client has stopped playing the given TV channel

**Parameters:**

  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - File: The jtv file key that has been played by client (default: <blank>)
  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Television/StopChannel?TVPlayer=0&Channel=-1&Zone=-1&ZoneType=ID)
### Television/GetAudioPrograms

- Get available audio programs on the currently playing channel

**Parameters:**

  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - File: The jtv file key that has been played by client (default: <blank>)
  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - AudioPrograms: Returns a list of audio programs

**Examples:**

  - Example: [Click here](Television/GetAudioPrograms?TVPlayer=0&Channel=-1&Zone=-1&ZoneType=ID)
### Television/SetAudioProgram

- Set audio program on the currently playing channel

**Parameters:**

  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - File: The jtv file key that has been played by client (default: <blank>)
  - Channel: The key of the TV channel to play. (default: -1)
  - AudioProgram: A string representing the audio program (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - NotAllowed: Returns 1 if the tuner has more tasks than just serving this client alone

**Examples:**

  - Example: [Click here](Television/SetAudioProgram?TVPlayer=0&Channel=-1&Zone=-1&ZoneType=ID)
### Television/SetActiveAudioProgramAsDefault

- Save active audio program on the currently playing channel as default

**Parameters:**

  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - File: The jtv file key that has been played by client (default: <blank>)
  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - NotAllowed: Returns 1 if the tuner has more tasks than just serving this client alone

**Examples:**

  - Example: [Click here](Television/SetActiveAudioProgramAsDefault?TVPlayer=0&Channel=-1&Zone=-1&ZoneType=ID)
### Television/ClientCallback

- Informs TV control that a client is still alive playing a TV channel

**Parameters:**

  - TVPlayer: The pointer to the CTVPlayer object that started the TV control on the given channel (default: 0)
  - File: The jtv file key that has been played by client (default: <blank>)
  - Channel: The key of the TV channel to play. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](Television/ClientCallback?TVPlayer=0&Channel=-1&Zone=-1&ZoneType=ID)
### Television/GetRecordingRuleConflict

- Query TV recording database whether a given recording rule has any conflicts

**Parameters:**

  - RuleID: RecordingRule ID (default: 0)
  - ParentRuleID: The parent ID of the recording rule (default: 0)
  - Name: The name of the recording rule (default: <blank>)
  - Properties: The recording rule properties (default: <blank>)

**Response:**

  - HasConflicts: Returns true or false
  - Messages: String messages to be displayed to user

**Examples:**

  - Example: [Click here](Television/GetRecordingRuleConflict?RuleID=0&ParentRuleID=0)
### Television/GetRecordingActionConflicts

- Query TV recording database whether a given recording rule has any conflicts

**Parameters:**

  - ProgramKey: Program key (default: -1)

**Response:**

  - HasConflicts: Returns true or false
  - Messages: String messages to be displayed to user

**Examples:**

  - Example: [Click here](Television/GetRecordingActionConflicts?ProgramKey=-1)
### Television/GetPlayerRecordingFile

- Get the player that is currently recording a given file.

**Parameters:**

  - File: The key of the file that is being recorded. (default: -1)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - TVPlayer: The pointer to CTVPlayer object that serves the channel.
  - ChannelKey: The television channel being recorded.

**Examples:**

  - Example: [Click here](Television/GetPlayerRecordingFile?File=-1&Zone=-1&ZoneType=ID)
### Television/GetRecordingSchedule

- Get a list of recordings scheduled for the next specified number of hours.

**Parameters:**

  - RangeInHours: The number of hours of schedules to report starting from current hour. (default: -1)

**Response:**

  - NumberRecordings: The number of recordings in the specified period.
  - ProgKey#: The program key of the recording at index #.
  - ChannelKey#: The channel key of the recording at index #.
  - RecordingID#: The recording rule ID of the recording at index #.
  - StartTime#: The start time of the recording at index #.
  - Duration#: The duration of the recording at index #.
  - ProgName#: The program name of the recording at index #.
  - Description#: The description of the recording at index #.
  - Status#: The status of the recording at index #.
  - TypeOfRecording#: The type of recording at index #.
  - IsRecordingNow#: Boolean indicating whether the recording at index # has started.

**Examples:**

  - Example: [Click here](Television/GetRecordingSchedule?RangeInHours=-1)
### Television/GetRecordingScheduleXML

- Get a list of recordings scheduled for the next specified number of hours.

**Parameters:**

  - RangeInHours: The number of hours of schedules to report starting from current hour. (default: 168)
  - FormatDateTime: Specifies whether to format the start time: 0 not formatted, 1 formatted (default: 1)

**Response:**

  - Recordings: The recordings in the specified period, in an xml formatted string.  Empty if no recording is scheduled.

**Examples:**

  - Example: [Click here](Television/GetRecordingScheduleXML?RangeInHours=168&FormatDateTime=1)
### Television/GetOrderedListOfTVChannels

- Get television channel custom ordering

**Response:**

  - OrderedList: Returns an ordered list of television channels

**Examples:**

  - Example: [Click here](Television/GetOrderedListOfTVChannels)
### Television/SetOrderedListOfTVChannels

- Set television channel custom ordering

**Parameters:**

  - OrderedList: Ordered list of television channels (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Television/SetOrderedListOfTVChannels)
### Television/ResetChannelOrderSetting

- Reset television channel ordering

**Response:**


**Examples:**

  - Example: [Click here](Television/ResetChannelOrderSetting)
### Television/GetChannelKeyPlayingInZone

- Get television channel key that is being served to the client

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - ChannelKey: Returns a channel key

**Examples:**

  - Example: [Click here](Television/GetChannelKeyPlayingInZone?Zone=-1&ZoneType=ID)
### Television/GetPlayingChannelAndRecordingProgramKeys

- Get television channel key that is being served to the client and all program keys currently being recorded

**Parameters:**

  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name (default: ID)

**Response:**

  - ChannelKey: Returns a channel key
  - ProgramKeys: Returns a comma separated list of program keys

**Examples:**

  - Example: [Click here](Television/GetPlayingChannelAndRecordingProgramKeys?Zone=-1&ZoneType=ID)
### Television/GetAllRecordingProgramKeys

- Get all television program keys currently being recorded

**Response:**

  - ChannelKey: Returns a channel key
  - ProgramKeys: Returns a comma separated list of program keys

**Examples:**

  - Example: [Click here](Television/GetAllRecordingProgramKeys)
### Television/GetTelevisionStatus

- Get Standard View television status text line

**Response:**

  - TVStatus: Returns status text

**Examples:**

  - Example: [Click here](Television/GetTelevisionStatus)
### Television/ReadRecordingFolderTestFile

- Request the server to read the content of the folder test file

**Parameters:**

  - TestFile: The file path and name of a client created file (default: <blank>)

**Response:**

  - FileContent: Returns a string read from the test file

**Examples:**

  - Example: [Click here](Television/ReadRecordingFolderTestFile)
### Television/GetTVStatusPage

- Ask the server to send tuner status page contents (tuner status and recording actions)

**Response:**

  - TVStatus: Returns a string from GetStatus

**Examples:**

  - Example: [Click here](Television/GetTVStatusPage)
### Television/GetTVLogs

- Ask the server to send TV Logs

**Response:**

  - TVLogs: Returns a string from ReadLogLines

**Examples:**

  - Example: [Click here](Television/GetTVLogs)
### Television/GetGuidePrograms

- Ask the server to send guide programs

**Parameters:**

  - StartDate: Start datetime (empty means starting now) (default: <blank>)
  - EndDate: End datetime (empty means 24 hours from start time) (default: <blank>)
  - Channels: Comma-separated list of channel keys (empty means all channels) (default: <blank>)

**Response:**

  - Programs: XML formatted EPG program info

**Examples:**

  - Example: [Click here](Television/GetGuidePrograms)
### Television/SetRecording

- Ask the server to send guide programs

**Parameters:**

  - RuleName: Specify a rule name.  For example you can use the program name (series name or episode name).  Optional, especially if ExistingRuleID is provided. (default: <blank>)
  - RecType: Type of recording.  1: record program; 2: record by time and channel; 3: set to no recording (do not use for this function); 4: subscription search; 5: subscription by time. (default: 1)
  - ProgKey: Program key of the guide program to record, must be included if RecType of 1.  Can be included for other types too. (default: <blank>)
  - ExistingRuleID: Existing recording rule ID.  Optional.  Needed only if calling this function to modify an existing recording rule.  Can also be skipped if ProgKey is valid and RecType is 1. (default: 0)
  - Channels: Semicolon-separated list of channel keys (empty or -1 means all channels).  Needed for RecType of 2 (single channel), 4 (multiple channels allowed), and 5 (single channel) (default: <blank>)
  - ExtBefore: Recording prepadding.  Specifies number of minutes by which to start recording early.  Empty means use user configured default value. (default: <blank>)
  - ExtAfter: Recording postpadding.  Specifies number of minutes by which to end recording late.  Empty means use user configured default value. (default: <blank>)
  - SubRules: Subscription rules using expression language, used with RecType 4 only.  Optional if ProgKey is also provided.  Example: ([Name]="College Basketball" or [Series]="College Basketball") ([Name]="Duke" or [Description]="Duke"). (default: <blank>)
  - ProgName: Program name.  Needed only with time-based recordings (RecType 2 and 5) (default: <blank>)
  - SubTimeMode: Subscription search time mode, used with RecType of 4.  0: All showing; 1: One per week near anchor time; 2: One per day near anchor time; 3: One per day near prime time; 4: One per day near middle of night. (default: <blank>)
  - SubTimeAnchor: Subscription search anchor time, used with RecType of 4.  Use string representation of system date-time format.  Not needed for other recording types, and not needed if a ProgKey is also provided. (default: <blank>)
  - NoRerun: Subscription search do not include reruns.  0 or 1.  Needed only for RecType of 4.  Optional.  If not specified, default value will be applied. (default: <blank>)
  - OnlyIfNotPrevRecorded: Subscription search only programs not previously recorded.  Needed only for RecType of 4.  Optional.  If not specified, default value will be applied. (default: <blank>)
  - FieldsToCompare: When OnlyIfNotPrevRecorded is specified, which fields are used to determine whether a program is previously already recorded.  Bitwise ORing of the following values: 1: [Name], 2: [Seires], 4: [Description], 8: [Season], 16: [Episode].  So a value of 7 means [Name], [Seires], and [Description] all must match to be considered a match.  Needed only for RecType of 4.  Optional.  If not specified, default value 7 will be applied. (default: 7)
  - StartTime: Starting time of the recording.  Needed only for RecType of 2 and 5, and may be skipped if ProgKey is provided. (default: <blank>)
  - Duration: Duration of the recording, in minutes.  Needed only for RecType of 2 and 5, and only if ProgKey is not provided. (default: <blank>)
  - DaysOfWeek: Semi-colon separated list of days.  1: Sunday, 2: Monday, 3: Tuesday, etc.  Needed only for RecType of 5. (default: <blank>)
  - QualityPref: Preferred video quality.  0: HD video, 1: SD video.  Needed only for RecType of 4. (default: <blank>)
  - Priority: Priority of the recording.  Integers 1 - 100.  Predefined values are 25: Low, 40: Medium-low, 50: Medium (default), 60: Medium-high, 75: High.  Optional, defaults to Medium. (default: <blank>)
  - KeepDays: Number of days to keep the recording before it is automatically deleted.  Optional.  Default to no cleanup (0). (default: <blank>)
  - KeepEpisodes: Number of episodes to keep.  Applicable only for subscription recordings (types 4 and 5).  Oldest episodes over this number will be deleted.  Optional.  Default to no cleanup (0). (default: <blank>)
  - Tags: Apply specified tags to the recording.  Optional.  If not specified (or empty), the default in TV options (or previously set tags, in case of modifying an exisitng recording) will be used.  Special value of "-1" means apply no tags. (default: <blank>)
  - ExecCom: The command to execute after recording is done.  Optional.  If not specified, the default in TV options will be used. (default: <blank>)
  - ComArgs: Commnad line arguments for ExecCom.  Optional.  If not specified (or empty), the default in TV options (or previously set tags, in case of modifying an exisitng recording) will be used.  Special value of "-1" means execute no command. (default: <blank>)

**Response:**

  - RecRuleID: Recording rule ID.  Positive values are valid.  0 is invalid.

**Examples:**

  - Example: [Click here](Television/SetRecording?RecType=1&ExistingRuleID=0&FieldsToCompare=7)
### Television/CancelRecording

- Cancel a scheduled recording.  Note that if CancelType 0 is used with a RecRuleID that represents a recording type of 5 (time-based subscription), it is equivalent to CancelType of 1.

**Parameters:**

  - RecRuleID: Recording rule ID (default: <blank>)
  - CancelType: Type of canceling.  0: Cancel specified program only (not meaningful if RecRuleID represents a recording of type 5), 1: Cancel subscription, 2: Suspend subscription recording (SuspStart and SuspEnd must be supplied). (default: 0)
  - ProgKey: Program database key of the program to cancel (not needed if canceling an entire subscription) (default: <blank>)
  - SuspStart: Date on which suspension starts (used with CancelType of 2) (default: <blank>)
  - SuspEnd: Date on which recording resumes (used with CancelType of 2) (default: <blank>)

**Response:**

  - Result: Success or failure.  1: canceling succeeded, 0: canceling failed.

**Examples:**

  - Example: [Click here](Television/CancelRecording?CancelType=0)

## UserInterface

### UserInterface/Info

- Gets information about the state of the user interface.

**Response:**

  - Mode: The user interface mode expressed as a UI_MODES integer (defined in MCCommands.h).
  - InternalMode: The internal user interface mode as a UI_MODES integer (will be in the UI_MODE_INTERNAL_* block).
  - ViewDisplayName: The display name of the current view.
  - SelectionDisplayName: The display name of the current selection.

**Examples:**

  - Example: [Click here](UserInterface/Info)
### UserInterface/Show

- Shows a view in the user interface.

**Parameters:**

  - View: The view to show. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](UserInterface/Show)
### UserInterface/GetStreaming

- Gets the streaming choices in the tree.

**Response:**

  - Streaming: The list of streaming choices semi-colon delimited.
  - Stations: The list of Radio JRiver sites.

**Examples:**

  - Example: [Click here](UserInterface/GetStreaming)
### UserInterface/GetRadioJRiver

- Plays the JRiver Radio station.

**Parameters:**

  - Site: The site to play. (default: <blank>)

**Response:**

  - Keys: The list of file keys, sepearted by comma.

**Examples:**

  - Example: [Click here](UserInterface/GetRadioJRiver)
### UserInterface/OSD

- Turn the OSD on or off

**Parameters:**

  - On: 1 or 0 to turn the OSD on or off. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](UserInterface/OSD)

## Configuration

### Configuration/Audio

- **ListDevices**
  - List the available audio output devices.
  - **Response:**
    - NumberDevices: The number of available devices.
    - DeviceName#: The name of the device at index #.
    - DevicePlugin#: The Name of the plugin of the device at index #.
  - **Examples:**
    - [Click here](Configuration/Audio/ListDevices)
- **SetDevice**
  - Set the audio output device.
  - **Parameters:**
    - Zone: The zone the command is targetted for. (default: -1)
    - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
    - DeviceIndex: The index of the device to set as the active device. (default: -1)
  - **Response:**
  - **Examples:**
    - [Click here](Configuration/Audio/SetDevice?Zone=-1&ZoneType=ID&DeviceIndex=-1)
- **GetDevice**
  - Get the audio output device.
  - **Parameters:**
    - Zone: The zone the command is targetted for. (default: -1)
    - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)
  - **Response:**
    - DeviceIndex: The index of the active audio device.
    - DeviceName: The name of the active audio device.
    - DevicePlugin: The plugin of the active audio device.
  - **Examples:**
    - [Click here](Configuration/Audio/GetDevice?Zone=-1&ZoneType=ID)
### Configuration/ErrorFreeMode

- Set the error free mode. (optional -- omit to query only)

**Parameters:**

  - ErrorFree: The state of the error free mode (0 or 1). (default: <blank>)

**Response:**

  - ErrorFree: The new state of the error free mode.

**Examples:**

  - Example: [Click here](Configuration/ErrorFreeMode)
### Time

Returns current system time for use in zone link sync operations.
### Response:

- SystemTime: The current system time in a 64 bit unsigned integer compatible with the unix timeval struct and our own CZoneLinkTime object.  The top 32 bits are seconds since Jan 1 1970, the bottom 32 bits are micro-seconds.
### Examples:

  - Example: [Click here](Time)
### Articles

Returns current list of articles.
### Parameters:

- SortIgnoreState: The new state of whether to ignore for sorting (0: off, 1: on). (default: -1)
### Response:

- Articles: The list of articles.
- Ignore: Whether to ignore articles.
### Examples:

  - Example: [Click here](Articles?SortIgnoreState=-1)

## DSP

### DSP/Set

- Set whether a DSP is on or off.

**Parameters:**

  - DSP: The name of the DSP. (default: <blank>)
  - On: 1 for on and 0 for off. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Turn equalizer on](DSP/Set?DSP=Equalizer&On=1&Zone=-1&ZoneType=ID)
### DSP/SetEqualizer

- Set the level of an EQ slider.

**Parameters:**

  - Slider: The number of the slider. (default: <blank>)
  - Level: The level of the slider. (default: <blank>)
  - On: Set to one to turn on the equalizer. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](DSP/SetEqualizer?Zone=-1&ZoneType=ID)
### DSP/SetTempo

- Set the tempo.

**Parameters:**

  - Tempo: The tempo. (default: <blank>)
  - Relative: Set to 1 to set the tempo relative to the current tempo. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Click here](DSP/SetTempo?Zone=-1&ZoneType=ID)
### DSP/Loudness

- Get and set the loudness.

**Parameters:**

  - Set: Set to 0 for off, 1 for on, and -1 to toggle. (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**

  - Current: The current value of the Loudness after the setting.

**Examples:**

  - Example: [Click here](DSP/Loudness?Zone=-1&ZoneType=ID)
### DSP/SetAdaptiveVolume

- Set the adaptive volume setting.

**Parameters:**

  - Strength: The strength (1, 2, or 3 or 0 for off). (default: <blank>)
  - Zone: The zone the command is targetted for. (default: -1)
  - ZoneType: The type of value provided in 'Zone' (ID: zone id; Index: zone index; Name: zone name). (default: ID)

**Response:**


**Examples:**

  - Example: [Set to night mode.](DSP/SetAdaptiveVolume?Strength=2)

## Podcast

### Podcast/Delete

- Delete a podcast.

**Parameters:**

  - Name: The name of the podcast to delete. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Podcast/Delete)

## Share

### Share/Get

- Gets a shared file.

**Parameters:**

  - File: The encrypted key of the file. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Share/Get)

## Settings

### Settings/ShowNetworkInfo

- Show the network information for the device.

**Response:**

  - IPConfig: Displays the IP configuration.
  - Netstat: The routing table information.

**Examples:**

  - Example: [Click here](Settings/ShowNetworkInfo)
### Settings/ShowWirelessNetworks

- Lists the avialable wireless networks.

**Response:**

  - WirelessNetworks: A list of the available wireless networks.

**Examples:**

  - Example: [Click here](Settings/ShowWirelessNetworks)

## Engen

### Engen/ServerLocation

- Returns the URL of a JRiver Engen IoT Server.  If it hasn't been configured in Media Center, it will be the default value.

**Parameters:**

  - CheckAlive: Set to 1 to verify that the Engen server is alive and running. (default: <blank>)

**Response:**

  - ServerLocation: The URL of a JRiver Engen IoT Server.
  - Alive: If CheckAlive is set to 1, test if the Engen server is running. Return value will be 'Alive=1' (running) or 'Alive=0'

**Examples:**

  - Example: [Click here](Engen/ServerLocation)

## Settings

### Settings/ReenterLicenseKey

- Allows the user to re-install the Id license

**Parameters:**

  - License: The license for the Id.  Also referred to as a registration code.  In this format: DCJD8-CPYN6-X1CO0-4B7O9-AZON1-C8X50 (default: <blank>)
  - Email: This should only be included when installing a newly purchased license.  It's the email address entered when purchasing the license.  This MUST NOT be included when simply restoring an existing license. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Settings/ReenterLicenseKey)
### Settings/Reboot

- Reboots the system.

**Response:**

  - Status: Displays the status of the system.

**Examples:**

  - Example: [Click here](Settings/Reboot)
### Settings/Shutdown

- Shutdown the system.

**Response:**


**Examples:**

  - Example: [Click here](Settings/Shutdown)
### Settings/AbortShutdown

- Cancel a system power command.

**Response:**


**Examples:**

  - Example: [Click here](Settings/AbortShutdown)
### Settings/Skin

- Sets the skin.

**Parameters:**

  - Skin: The skin name. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Settings/Skin)

## Spotlight

### Spotlight/GetPage

- Get Spotlight page.

**Parameters:**

  - Key: File key (empty means current file) (default: <blank>)
  - Type: Optional spotlight page type: artist, movie, tvshow, person (overrides file key and uses search parameters below) (default: <blank>)
  - Name: Name or person ID (from TMDB) (default: <blank>)
  - MovieYear: Movie year (default: <blank>)
  - MovieIMDBId: Movie IMDB id (default: <blank>)
  - TVSeason: TV show season (default: <blank>)
  - TMDBId: Movie/TV show TMDB id (default: <blank>)

**Response:**

  - XML with embedded style sheet.

**Examples:**

  - Example: [Click here](Spotlight/GetPage)
### Spotlight/ClearCache

- Clear Spotlight cache.

**Parameters:**

  - Type: Spotlight page type: artist, movie, tvshow, person. (default: <blank>)

**Response:**


**Examples:**

  - Example: [Click here](Spotlight/ClearCache)

## Cloudplay

### Cloudplay/GetPlaylists

- Get playlists of desired type.

**Parameters:**

  - Type: type of playlists: Popular, etc. (default: <blank>)

**Response:**

  - JSON array of playlists.

**Examples:**

  - Example: [Click here](Cloudplay/GetPlaylists)
### Cloudplay/GetTracks

- Get tracks as keys for desired search.

**Parameters:**

  - Type: type of search: playlist, artist, genre (default: <blank>)
  - Query: playlist ID, artist name, or genre name (default: <blank>)

**Response:**

  - List of file keys, separated by commas.

**Examples:**

  - Example: [Click here](Cloudplay/GetTracks)