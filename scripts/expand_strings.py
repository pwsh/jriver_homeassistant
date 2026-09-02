"""Expand strings.json placeholder references into translations/en.json."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
STRINGS = ROOT / "custom_components" / "jriver" / "strings.json"
EN = ROOT / "custom_components" / "jriver" / "translations" / "en.json"

COMMON = {
    "common::config_flow::data::api_key": "API key",
    "common::config_flow::data::name": "Name",
    "common::config_flow::data::host": "Host",
    "common::config_flow::data::port": "Port",
    "common::config_flow::data::ssl": "Uses an SSL certificate",
    "common::config_flow::data::username": "Username",
    "common::config_flow::data::password": "Password",
    "common::config_flow::error::cannot_connect": "Failed to connect",
    "common::config_flow::error::invalid_auth": "Invalid authentication",
    "common::config_flow::error::timeout_connect": "Timeout establishing connection",
    "common::config_flow::error::unknown": "Unexpected error",
    "common::config_flow::abort::already_configured_device": "Device is already configured",
    "common::config_flow::abort::reauth_successful": "Re-authentication was successful",
    "common::config_flow::abort::reconfigure_successful": "Re-configuration was successful",
}

REF = re.compile(r"^\[%key:(?P<key>.+)%\]$")


def resolve(key: str, root: dict) -> str:
    if key in COMMON:
        return COMMON[key]
    if key.startswith("component::jriver::"):
        node = root
        for token in key[len("component::jriver::") :].split("::"):
            node = node[token]
        return expand(node, root)
    raise KeyError(f"Unresolvable reference {key}")


def expand(value, root):
    if isinstance(value, dict):
        return {k: expand(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [expand(v, root) for v in value]
    if isinstance(value, str) and (match := REF.match(value)):
        return resolve(match.group("key"), root)
    return value


def main() -> int:
    root = json.loads(STRINGS.read_text())
    expanded = expand(root, root)
    EN.write_text(json.dumps(expanded, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"wrote {EN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
