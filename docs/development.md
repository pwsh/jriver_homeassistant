---
title: Development
nav_order: 11
has_children: true
---

# Development

## Getting set up

```bash
git clone -b v2-rework https://github.com/pwsh/jriver_homeassistant.git
cd jriver_homeassistant

uv venv
. .venv/bin/activate
uv pip install -r requirements-dev.txt
```

`requirements-dev.txt` pulls in `pytest-homeassistant-custom-component` (which brings Home
Assistant itself), `pytest-cov` and `ruff`. The integration has no runtime requirements:
`manifest.json` declares an empty `requirements` list because the MCWS client is vendored.

Python 3.13 or newer is required.

## Checks

```bash
pytest -q
ruff check custom_components tests
ruff format custom_components tests
```

Coverage is configured over `custom_components/jriver`, so `pytest --cov` reports on the
integration rather than the test package.

Ruff runs with `line-length = 100`, target `py313`, and the `E`, `F`, `I`, `UP`, `B`, `ASYNC`
and `W` rule sets. Two per-file exemptions exist: the vendored client takes an explicit
timeout by design (`ASYNC109`), and the client tests embed captured MCWS payloads verbatim
(`E501`).

## Translations

`strings.json` is the source of truth and uses Home Assistant's `[%key:common::…%]`
placeholder references. `translations/en.json` is generated from it.

```bash
# expand the placeholders in strings.json into translations/en.json
python scripts/expand_strings.py

# verify strings.json, translations/*.json and services.yaml agree
python scripts/check_translations.py
```

Run both after any change to `strings.json` or `services.yaml`.

## Layout

```
custom_components/jriver/
  mcws/           vendored MCWS client, no Home Assistant imports
  const.py        domain, config/option keys, defaults, entity kinds, action names
  media_types.py  Media Center media type/sub type -> HA MediaType/MediaClass
  coordinator.py  MediaServerUpdateCoordinator and the frozen MediaServerData snapshot
  models.py       JRiverRuntimeData and the typed JRiverConfigEntry alias
  entity.py       MediaServerEntity base: device topology, unique ids, the @cmd wrapper
  services.py     action schemas, target resolution and the domain action handlers
  browse_media.py the media browser tree
  __init__.py     setup, unload, migration, action registration
  config_flow.py  setup, reauth, reconfigure and the options flow
  media_player.py / remote.py / sensor.py / binary_sensor.py / diagnostics.py
```

See [Architecture]({{ site.baseurl }}/architecture/) for the module layering,
coordinator tiers, device topology and data flow.

## Testing the vendored client

`tests/mcws/` exercises the client against a **fake MCWS server**: a real `aiohttp` test
server, started per test, that answers with canned XML.

`tests/mcws/conftest.py` defines a `FakeMediaServer` holding a `path -> (body, content type,
status)` map. A test registers the responses it needs, points a real `MediaServer` client at
the server's address, and asserts on both the parsed result and the recorded request
parameters. Only `Authenticate` is configured out of the box; everything else must be
registered explicitly, so a call the test did not anticipate fails loudly.

Because these tests need to bind a socket and do not need Home Assistant, the conftest enables
sockets and shadows the Home Assistant autouse fixtures from `tests/conftest.py`.

`tests/` (the top level) tests the Home Assistant side with `MockConfigEntry` and a mocked
`MediaServer`, so no HTTP happens there at all.

## Live smoke test

There is no automated test against a real server. To sanity check the client by hand, write a
short throwaway script that constructs a connection and calls only **read-only** endpoints:

```python
import asyncio

import aiohttp

from custom_components.jriver.mcws import MediaServer, get_mcws_connection


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        connection = get_mcws_connection(
            "mc.local",          # host
            52199,               # port
            username="user",     # omit if Media Network authentication is off
            password="secret",
            ssl=False,
            timeout=10,
            session=session,
        )
        server = MediaServer(connection)
        print(await server.alive())
        zones = await server.get_zones()
        print(zones)
        for zone in zones:
            print(await server.get_playback_info(zone))
        print(await server.get_view_mode())
        print(await server.get_browse_rules())
        await server.close()


asyncio.run(main())
```

Rules for the smoke test:

- **Read only.** `alive`, `get_zones`, `get_view_mode`, `get_playback_info`,
  `get_browse_rules`, `get_library_fields`, `get_audio_path`, `get_current_playlist` and
  `search_files` observe without changing anything. Do not call playback, MCC or DSP methods:
  they will move a real listener's music.
- **Never commit it.** Keep credentials and the real host out of the repository; use an
  environment variable or a local file that is git ignored.
- **Note the server version.** Feature availability differs sharply between Media Center
  versions — `Browse/Rules` needs 32.0.6, and `Playback/Repeat` and `Playback/Shuffle` are
  missing on some builds. Record what you tested against.

The [MCWS reference]({{ site.baseurl }}/mcws-functions/) lists every endpoint the server
exposes, with its parameters, which is the quickest way to find something the client does not
wrap yet.

## Documentation

This site lives in `docs/` and is built by `.github/workflows/pages.yaml` with
`actions/jekyll-build-pages`, using the `just-the-docs` remote theme. Pushes to `main` or
`v2-rework` that touch `docs/**` or the workflow trigger a deploy.

For a local preview:

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Every page needs just-the-docs front matter — a `title` and a `nav_order`, plus `parent` when
nested.
