"""Verify strings.json, translations/*.json and services.yaml agree."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "jriver"


def keys(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from keys(value, f"{prefix}.{key}" if prefix else key)
    else:
        yield prefix


def main() -> int:
    errors: list[str] = []
    strings = json.loads((COMPONENT / "strings.json").read_text())
    string_keys = set(keys(strings))

    for name in ("en", "pt"):
        translation = json.loads((COMPONENT / "translations" / f"{name}.json").read_text())
        translation_keys = set(keys(translation))
        if missing := string_keys - translation_keys:
            errors.append(f"{name}.json missing: {sorted(missing)}")
        if extra := translation_keys - string_keys:
            errors.append(f"{name}.json unexpected: {sorted(extra)}")

    services = yaml.safe_load((COMPONENT / "services.yaml").read_text())
    described = strings["services"]
    if missing := set(services) - set(described):
        errors.append(f"services.yaml services with no strings entry: {sorted(missing)}")
    if extra := set(described) - set(services):
        errors.append(f"strings.json services not in services.yaml: {sorted(extra)}")
    for service, definition in services.items():
        if service not in described:
            continue
        yaml_fields = set((definition or {}).get("fields") or {})
        string_fields = set(described[service].get("fields") or {})
        if diff := yaml_fields ^ string_fields:
            errors.append(f"{service} field mismatch: {sorted(diff)}")

    icons = json.loads((COMPONENT / "icons.json").read_text())
    if diff := set(icons.get("services", {})) ^ set(services):
        errors.append(f"icons.json service mismatch: {sorted(diff)}")

    if errors:
        print("\n".join(errors))
        return 1
    print("translations, services.yaml and icons.json are in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
