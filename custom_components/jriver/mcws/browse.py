"""Browse rule/path helpers for the JRiver MCWS interface.

Derived from the ``hamcws`` library (https://github.com/3ll3d00d/hamcws) v0.2.7,
Copyright (c) 3ll3d00d, MIT licensed. See ``__init__.py`` for the full notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging

from .models import MediaSubType, MediaType

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "BrowsePath",
    "BrowseRule",
    "convert_browse_rules",
    "parse_browse_paths_from_text",
    "search_for_path",
]


@dataclass(order=True)
class BrowseRule:
    """A single rule as returned by ``Browse/Rules``."""

    name: str
    categories: str
    search: str

    def get_names(self) -> list[str]:
        """The path segments named by this rule."""
        return [n for n in self.name.split("\\") if n]

    def get_categories(self) -> list[str]:
        """The category (library field) segments named by this rule."""
        return [c for c in self.categories.split("\\") if c]


@dataclass
class BrowsePath:
    """A node in the browsable tree derived from the browse rules."""

    name: str
    is_field: bool = False
    parent: BrowsePath | None = None
    children: list[BrowsePath] = field(default_factory=list)
    media_types: list[MediaType] = field(default_factory=list)
    media_sub_types: list[MediaSubType] = field(default_factory=list)

    @property
    def full_path(self) -> str:
        """The ``/`` delimited path from the root to this node."""
        return f"{self.parent.full_path}/{self.name}" if self.parent else self.name

    @property
    def descendents(self) -> list[BrowsePath]:
        """All nodes beneath this one, depth first."""
        descendents: list[BrowsePath] = []
        for child in self.children:
            descendents.append(child)
            descendents += child.descendents
        return descendents

    @property
    def effective_media_types(self) -> list[MediaType]:
        """The media types for this node, inherited from an ancestor if unset."""
        if self.media_types:
            return self.media_types
        if self.parent:
            return self.parent.effective_media_types
        return []

    @property
    def effective_media_sub_types(self) -> list[MediaSubType]:
        """The media sub types for this node, inherited if unset."""
        if self.media_sub_types:
            return self.media_sub_types
        if self.parent:
            return self.parent.effective_media_sub_types
        return []


def _parse_search(search: str) -> tuple[list[MediaType], list[MediaSubType]]:
    """Attempt to find MediaType and MediaSubType from the search query."""

    def _extract(enum_cls, token: str):
        try:
            return enum_cls(token[1 : token.index("]")])
        except (ValueError, IndexError):
            _LOGGER.debug("Unable to derive %s from %r", enum_cls.__name__, token)
            return None

    mt: list[MediaType | None] = []
    mst: list[MediaSubType | None] = []
    if "[Media Type]=" in search:
        mt = [_extract(MediaType, t) for t in search.split("[Media Type]=")[1].split(",")]
    if "[Media Sub Type]=" in search:
        mst = [_extract(MediaSubType, t) for t in search.split("[Media Sub Type]=")[1].split(",")]
    return [m for m in mt if m], [m for m in mst if m]


def convert_browse_rules(
    rules: list[BrowseRule], flat: bool = False, infer_media_types: bool = True
) -> list[BrowsePath]:
    """Convert the rules into a tree of paths."""
    paths: list[BrowsePath] = []
    all_paths: list[BrowsePath] = []
    sorted_rules = sorted(
        rules, key=lambda r: (r.name, len(r.get_names()), len(r.get_categories()))
    )
    for rule in sorted_rules:
        tokens = rule.get_names()
        if not tokens:
            continue
        mt, mst = _parse_search(rule.search)
        path = BrowsePath(tokens[-1])
        path.media_types = mt
        path.media_sub_types = mst
        if len(tokens) == 1:
            paths.append(path)
            all_paths.append(path)
        else:
            target_path = "/".join(tokens[:-1])
            parent = next((p for p in all_paths if p.full_path == target_path), None)
            if parent:
                parent.children.append(path)
                all_paths.append(path)
                path.parent = parent
        if rule.categories:
            for category in rule.get_categories():
                parent = path
                path = BrowsePath(category, True)
                path.parent = parent
                parent.children.append(path)

    if infer_media_types:
        _infer_media_types(paths)
    return all_paths if flat else paths


def parse_browse_paths_from_text(input_rules: list[str]) -> list[BrowsePath]:
    """Convert user provided ``A,B|cat1,cat2`` strings into BrowsePaths."""
    browse_rules: list[BrowseRule] = []
    for input_rule in input_rules:
        vals = input_rule.split("|", 2)
        names = vals[0].split(",")
        for idx in range(len(names)):
            full_name = "\\".join(names[0 : idx + 1])
            match = next((rule for rule in browse_rules if rule.name == full_name), None)
            if not match:
                match = BrowseRule(full_name, "", "")
                browse_rules.append(match)
            if idx == len(names) - 1 and len(vals) > 1:
                match.categories = "\\".join(vals[1].split(","))
    return convert_browse_rules(browse_rules)


def _infer_media_types(paths: list[BrowsePath]) -> list[BrowsePath]:
    """Heuristically apply media types based on well known category names."""
    for path in paths:
        if path.name == "Audio":
            path.media_types = [MediaType.AUDIO]
            for descendant in path.descendents:
                if descendant.name == "Podcasts":
                    descendant.media_sub_types = [MediaSubType.PODCAST]
                elif descendant.name in ("Album", "Artist", "Composer"):
                    descendant.media_sub_types = [MediaSubType.MUSIC]
                elif descendant.name == "Audiobooks":
                    descendant.media_sub_types = [MediaSubType.AUDIOBOOK]
        elif path.name == "Images":
            path.media_types = [MediaType.IMAGE]
        elif path.name == "Video":
            path.media_types = [MediaType.VIDEO]
            for descendant in path.descendents:
                if descendant.name.startswith("Movies"):
                    descendant.media_sub_types = [MediaSubType.MOVIE]
                elif descendant.name == "Shows":
                    descendant.media_sub_types = [MediaSubType.TV_SHOW]
                elif descendant.name == "Music":
                    descendant.media_sub_types = [MediaSubType.MUSIC_VIDEO]
        elif path.name == "Playlists":
            path.media_types = [MediaType.PLAYLIST]
        elif path.name == "Audiobooks":
            path.media_types = [MediaType.AUDIO]
            path.media_sub_types = [MediaSubType.AUDIOBOOK]
    return paths


def search_for_path(paths: list[BrowsePath], target_path: list[str]) -> BrowsePath | None:
    """Find the BrowsePath identified by the given list of node names.

    Only non field nodes are examined when matching names.
    """
    if not target_path:
        return None

    def _search(level: int, search_paths: list[BrowsePath] | None) -> BrowsePath | None:
        if not search_paths:
            return None
        for path in search_paths:
            if path.is_field:
                continue
            if path.name == target_path[level - 1]:
                if len(target_path) == level:
                    return path
                if (
                    path.descendents
                    and all(c.is_field for c in path.descendents)
                    and len(path.descendents) + level >= len(target_path)
                ):
                    return path.descendents[len(target_path[level:]) - 1]
                return _search(level + 1, path.children)
        return None

    return _search(1, paths)
