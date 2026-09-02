"""A vendored, typed MCWS client for JRiver Media Center.

This package is derived from the ``hamcws`` library v0.2.7
(https://github.com/3ll3d00d/hamcws) by 3ll3d00d, which is unmaintained. It is
vendored here so the integration has no external requirements, with a number of
upstream defects fixed and coverage extended to more MCWS endpoints.

MIT License

Copyright (c) 2023 3ll3d00d
Copyright (c) 2026 jriver_homeassistant contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from .browse import (
    BrowsePath,
    BrowseRule,
    convert_browse_rules,
    parse_browse_paths_from_text,
    search_for_path,
)
from .connection import (
    CannotConnectError,
    InvalidAccessKeyError,
    InvalidAuthError,
    InvalidRequestError,
    MediaServerConnection,
    MediaServerError,
    UnsupportedRequestError,
    get_mcws_connection,
)
from .discovery import load_media_server, resolve_access_key, try_connect
from .mcc import MCC
from .models import (
    AudioPath,
    KeyCommand,
    LibraryField,
    MediaServerInfo,
    MediaSubType,
    MediaType,
    PlaybackInfo,
    PlaybackState,
    Playlist,
    PlayMode,
    RepeatMode,
    ServerAddress,
    ShuffleMode,
    ViewMode,
    Zone,
)
from .server import MediaServer

__all__ = [
    "MCC",
    "AudioPath",
    "BrowsePath",
    "BrowseRule",
    "CannotConnectError",
    "InvalidAccessKeyError",
    "InvalidAuthError",
    "InvalidRequestError",
    "KeyCommand",
    "LibraryField",
    "MediaServer",
    "MediaServerConnection",
    "MediaServerError",
    "MediaServerInfo",
    "MediaSubType",
    "MediaType",
    "PlayMode",
    "PlaybackInfo",
    "PlaybackState",
    "Playlist",
    "RepeatMode",
    "ServerAddress",
    "ShuffleMode",
    "UnsupportedRequestError",
    "ViewMode",
    "Zone",
    "convert_browse_rules",
    "get_mcws_connection",
    "load_media_server",
    "parse_browse_paths_from_text",
    "resolve_access_key",
    "search_for_path",
    "try_connect",
]
