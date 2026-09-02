"""Test the JRiver Media Center config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jriver.const import (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_EXTRA_FIELDS,
    CONF_POLL_INTERVAL,
    CONF_TURN_OFF_BEHAVIOUR,
    CONF_USE_WOL,
    DOMAIN,
)
from custom_components.jriver.mcws import (
    CannotConnectError,
    InvalidAccessKeyError,
    InvalidAuthError,
    InvalidRequestError,
    MediaServerError,
)
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ACCESS_KEY, FakeMediaServer, build_entry

TARGET = "custom_components.jriver.config_flow.load_media_server"


def _loader(server: FakeMediaServer, macs: list[str] | None = None):
    return AsyncMock(return_value=(server, macs or []))


async def _start(hass: HomeAssistant) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    return result


async def test_access_key_is_invalid(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """A bad access key produces an error."""
    result = await _start(hass)
    with patch(TARGET, side_effect=InvalidAccessKeyError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "abcdef"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_access_key"}
    assert not mock_setup_entry.mock_calls


@pytest.mark.parametrize(
    ("side_effect", "named_error"),
    [
        (CannotConnectError, "cannot_connect"),
        (TimeoutError, "timeout_connect"),
        (InvalidRequestError, "unknown"),
        (MediaServerError, "unknown"),
        (Exception, "unknown"),
    ],
)
async def test_connection_errors(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, side_effect, named_error
) -> None:
    """Assorted connection errors are reported on the form."""
    result = await _start(hass)
    with patch(TARGET, side_effect=side_effect()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": named_error}
    assert not mock_setup_entry.mock_calls


async def test_invalid_auth_prompts_for_credentials(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """An auth failure moves on to the credentials step."""
    result = await _start(hass)
    with patch(TARGET, side_effect=InvalidAuthError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
    assert result["step_id"] == "credentials"

    with patch(TARGET, side_effect=InvalidAuthError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user", CONF_PASSWORD: "wrong"},
        )
    assert result["errors"] == {"base": "invalid_auth"}

    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "right"}
        )
    assert result["step_id"] == "macs"


async def test_full_flow_modern_server(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """A MC 32+ server skips the manual browse paths step."""
    result = await _start(hass)
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199, CONF_SSL: False}
        )
        assert result["step_id"] == "macs"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USE_WOL: True, CONF_MAC: ["AA-BB-CC-DD-EE-FF"]}
        )
        assert result["step_id"] == "zones"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_PER_ZONE: True}
        )
        assert result["step_id"] == "select_zones"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_ZONES: ["Player"]}
        )
        assert result["step_id"] == "select_playback_fields"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_EXTRA_FIELDS: ["Genre"]}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == ACCESS_KEY
    assert result["data"][CONF_MAC] == ["aa:bb:cc:dd:ee:ff"]
    assert result["data"][CONF_HOST] == "1.1.1.1"
    assert CONF_BROWSE_PATHS not in result["data"]
    assert result["options"][CONF_DEVICE_ZONES] == ["Player"]
    assert result["options"][CONF_EXTRA_FIELDS] == ["Genre"]
    assert result["options"][CONF_POLL_INTERVAL] == 2
    assert result["options"][CONF_TURN_OFF_BEHAVIOUR] == "stop"


async def test_full_flow_old_server_asks_for_paths(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """A server without Browse/Rules asks for the paths."""
    server = FakeMediaServer(version="31.0.10")
    result = await _start(hass)
    with patch(TARGET, _loader(server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USE_WOL: False, CONF_MAC: []}
        )
        assert result["step_id"] == "paths"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BROWSE_PATHS: []}
        )
        assert result["errors"] == {"base": "no_paths"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BROWSE_PATHS: ["Audio,Album|Album"]}
        )
        assert result["step_id"] == "zones"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_PER_ZONE: False}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_EXTRA_FIELDS: []}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_BROWSE_PATHS] == ["Audio,Album|Album"]


async def test_macs_validation(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """The MAC step validates its input."""
    result = await _start(hass)
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USE_WOL: True, CONF_MAC: []}
        )
        assert result["errors"] == {"base": "no_mac_addresses"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USE_WOL: True, CONF_MAC: ["nope"]}
        )
        assert result["errors"] == {"base": "invalid_mac"}


async def test_select_zones_requires_a_zone(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """At least one zone must be picked."""
    result = await _start(hass)
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USE_WOL: False, CONF_MAC: []}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_PER_ZONE: True}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_ZONES: []}
        )
    assert result["errors"] == {"base": "no_zones"}


async def test_duplicate_entry_is_rejected(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """A server that is already configured aborts."""
    build_entry().add_to_hass(hass)
    result = await _start(hass)
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1", CONF_PORT: 52199}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """Reauth updates the stored credentials in place."""
    entry = build_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    with patch(TARGET, side_effect=InvalidAuthError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "wrong"}
        )
    assert result["errors"] == {"base": "invalid_auth"}

    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "user2", CONF_PASSWORD: "right"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_USERNAME] == "user2"
    assert entry.data[CONF_PASSWORD] == "right"


async def test_reconfigure(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """Reconfigure moves the entry to a new address."""
    entry = build_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    fake_server.host = "2.2.2.2"
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 52199,
                CONF_SSL: False,
                CONF_NAME: "Phosphorus",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "2.2.2.2"


async def test_reconfigure_updates_title(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """Reconfigure retitles the entry when the friendly name changes."""
    entry = build_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 52199,
                CONF_SSL: False,
                CONF_NAME: "Upstairs",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_NAME] == "Upstairs"
    assert entry.title == "Upstairs"


async def test_reconfigure_wrong_server(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, fake_server: FakeMediaServer
) -> None:
    """Pointing an entry at a different server aborts."""
    entry = build_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    fake_server.media_server_info.access_key = "somethingelse"
    with patch(TARGET, _loader(fake_server)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "2.2.2.2", CONF_PORT: 52199, CONF_SSL: False},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_server"


async def test_options_flow(
    hass: HomeAssistant, init_integration: MockConfigEntry, fake_server, mock_media_server
) -> None:
    """The options flow walks poll, zones, macs and fields."""
    with patch(TARGET, _loader(mock_media_server)):
        result = await hass.config_entries.options.async_init(init_integration.entry_id)
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_POLL_INTERVAL: 5,
                CONF_TURN_OFF_BEHAVIOUR: "close_program",
                CONF_DSP_PRESETS: ["Night"],
            },
        )
        assert result["step_id"] == "zones"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: ["Player"]},
        )
        assert result["step_id"] == "macs"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_USE_WOL: False, CONF_MAC: []}
        )
        assert result["step_id"] == "fields"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_EXTRA_FIELDS: ["Genre"]}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert init_integration.options[CONF_POLL_INTERVAL] == 5
    assert init_integration.options[CONF_TURN_OFF_BEHAVIOUR] == "close_program"
    assert init_integration.options[CONF_DSP_PRESETS] == ["Night"]
    assert init_integration.options[CONF_DEVICE_ZONES] == ["Player"]
    assert init_integration.options[CONF_EXTRA_FIELDS] == ["Genre"]


async def test_options_flow_connection_failure(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The options flow reports a connection failure."""
    with patch(TARGET, side_effect=CannotConnectError()):
        result = await hass.config_entries.options.async_init(init_integration.entry_id)
    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow_zone_validation(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_media_server
) -> None:
    """Per zone mode needs at least one zone."""
    with patch(TARGET, _loader(mock_media_server)):
        result = await hass.config_entries.options.async_init(init_integration.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_POLL_INTERVAL: 2,
                CONF_TURN_OFF_BEHAVIOUR: "stop",
                CONF_DSP_PRESETS: [],
            },
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_DEVICE_PER_ZONE: True, CONF_DEVICE_ZONES: []}
        )
    assert result["errors"] == {"base": "no_zones"}
