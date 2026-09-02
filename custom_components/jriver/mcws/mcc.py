"""Media Center Core Commands (MCC) identifiers.

From https://wiki.jriver.com/index.php/Media_Center_Core_Commands.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["MCC"]


class MCC(IntEnum):
    """A subset of the documented MCC command ids."""

    PLAY_PAUSE = 10000
    PLAY = 10001
    STOP = 10002
    NEXT = 10003
    PREVIOUS = 10004
    SHUFFLE = 10005
    CONTINUOUS = 10006
    SET_ZONE = 10011
    SHOW_DSP_STUDIO = 10016
    VOLUME_MUTE = 10017
    VOLUME_UP = 10018
    VOLUME_DOWN = 10019
    VOLUME_SET = 10020
    STOP_AFTER_CURRENT_FILE = 10036
    LINK_ZONE = 10060
    UNLINK_ZONE = 10061
    STOP_AFTER_DELAY = 10067
    STOP_AFTER_TRACKS = 10068
    HIDE_DSP_STUDIO = 10084
    CLOSE_PROGRAM = 20007
    TOGGLE_MODE = 22000
    THEATER_VIEW = 22001
    SET_MODE = 22009
