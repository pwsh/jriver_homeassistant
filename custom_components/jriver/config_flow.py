"""Config flow for the JRiver Media Center integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_BROWSE_PATHS,
    CONF_DEVICE_PER_ZONE,
    CONF_DEVICE_ZONES,
    CONF_DSP_PRESETS,
    CONF_EXTRA_FIELDS,
    CONF_POLL_INTERVAL,
    CONF_TURN_OFF_BEHAVIOUR,
    CONF_USE_WOL,
    DEFAULT_BROWSE_PATHS,
    DEFAULT_DEVICE_PER_ZONE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_TIMEOUT,
    DEFAULT_TURN_OFF_BEHAVIOUR,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    TurnOffBehaviour,
)
from .mcws import (
    CannotConnectError,
    InvalidAccessKeyError,
    InvalidAuthError,
    InvalidRequestError,
    MediaServer,
    MediaServerError,
    load_media_server,
    parse_browse_paths_from_text,
)

_LOGGER = logging.getLogger(__name__)

MAC_PATTERN = re.compile(r"[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\1[0-9a-f]{2}){4}$")

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
MAC_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiple=True))
PATHS_SELECTOR = TextSelector(
    TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True, multiple=True)
)
PRESETS_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT, multiple=True))
POLL_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=MIN_POLL_INTERVAL,
        max=MAX_POLL_INTERVAL,
        step=1,
        mode=NumberSelectorMode.BOX,
        unit_of_measurement="s",
    )
)
TURN_OFF_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[b.value for b in TurnOffBehaviour],
        mode=SelectSelectorMode.DROPDOWN,
        translation_key="turn_off_behaviour",
    )
)


class CannotConnect(HomeAssistantError):
    """Unable to reach the server."""


class InvalidAuth(HomeAssistantError):
    """The credentials were rejected."""


class InvalidRequest(HomeAssistantError):
    """The server rejected the request."""


class InternalError(HomeAssistantError):
    """The server failed unexpectedly."""


class InvalidAccessKey(HomeAssistantError):
    """The access key could not be resolved."""


ERROR_REASONS: dict[type[Exception], str] = {
    InvalidAccessKey: "invalid_access_key",
    InvalidAuth: "invalid_auth",
    CannotConnect: "cannot_connect",
    TimeoutError: "timeout_connect",
    InvalidRequest: "unknown",
    InternalError: "unknown",
}


def invalid_mac(mac: str) -> bool:
    """Return True if the given MAC address is malformed."""
    return not MAC_PATTERN.match(mac.lower())


async def connect_to_media_server(
    hass: HomeAssistant, data: dict[str, Any]
) -> tuple[MediaServer, list[str]]:
    """Connect to Media Center, translating client errors to flow errors."""
    try:
        return await load_media_server(
            access_key=data.get(CONF_API_KEY, ""),
            host=data.get(CONF_HOST, ""),
            port=data.get(CONF_PORT, DEFAULT_PORT),
            username=data.get(CONF_USERNAME),
            password=data.get(CONF_PASSWORD),
            use_ssl=data.get(CONF_SSL, False),
            session=async_get_clientsession(hass),
            timeout=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        )
    except InvalidAuthError as error:
        raise InvalidAuth from error
    except InvalidAccessKeyError as error:
        raise InvalidAccessKey from error
    except CannotConnectError as error:
        raise CannotConnect from error
    except InvalidRequestError as error:
        raise InvalidRequest from error
    except MediaServerError as error:
        raise InternalError from error


class JRiverConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JRiver Media Center."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialise the flow."""
        self._access_key: str = ""
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._friendly_name: str = ""
        self._expect_wol: bool = False
        self._mac_addresses: list[str] = []
        self._username: str | None = None
        self._password: str | None = None
        self._ssl: bool = DEFAULT_SSL
        self._device_per_zone: bool = DEFAULT_DEVICE_PER_ZONE
        self._browse_paths: list[str] = []
        self._device_zones: list[str] = []
        self._extra_fields: list[str] = []
        self._ms: MediaServer | None = None
        self._zone_names: list[str] = []
        self._library_fields: list[str] = []

    # -- initial setup ---------------------------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect the server location."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._access_key = user_input.get(CONF_API_KEY, "")
            self._host = user_input.get(CONF_HOST, "")
            self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
            self._ssl = user_input.get(CONF_SSL, DEFAULT_SSL)
            self._friendly_name = user_input.get(CONF_NAME, "")

            try:
                await self._async_connect()
            except InvalidAuth:
                return await self.async_step_credentials()
            except AbortFlow:
                raise
            except Exception as err:  # noqa: BLE001
                errors["base"] = self._reason_for(err)
            else:
                await self._async_set_unique_id()
                return await self.async_step_macs()

        return self._show_user_form(errors)

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect credentials when the server demands them."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input.get(CONF_USERNAME)
            self._password = user_input.get(CONF_PASSWORD)
            try:
                await self._async_connect()
            except AbortFlow:
                raise
            except Exception as err:  # noqa: BLE001
                errors["base"] = self._reason_for(err)
            else:
                await self._async_set_unique_id()
                return await self.async_step_macs()

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME, description={"suggested_value": self._username}
                    ): str,
                    vol.Optional(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_macs(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect the MAC addresses used for wake on LAN."""
        errors: dict[str, str] = {}
        if user_input is not None:
            macs = user_input.get(CONF_MAC, [])
            self._expect_wol = user_input[CONF_USE_WOL]
            if self._expect_wol and not macs:
                errors["base"] = "no_mac_addresses"
            elif any(invalid_mac(m) for m in macs):
                errors["base"] = "invalid_mac"
            else:
                self._mac_addresses = (
                    [m.replace("-", ":").lower() for m in macs] if self._expect_wol else []
                )
                return await self.async_step_paths()

        return self.async_show_form(
            step_id="macs",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USE_WOL, default=self._expect_wol): bool,
                    vol.Optional(CONF_MAC, default=self._mac_addresses): MAC_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_paths(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect the browse paths, only needed for MC < 32.0.6."""
        errors: dict[str, str] = {}

        if self._supports_browse_rules:
            return await self._async_next_after_paths()

        if not self._browse_paths:
            self._browse_paths = sorted(DEFAULT_BROWSE_PATHS)

        if user_input is not None:
            self._browse_paths = user_input.get(CONF_BROWSE_PATHS, [])
            if not self._browse_paths:
                errors["base"] = "no_paths"
            elif parse_browse_paths_from_text(self._browse_paths) is None:
                errors["base"] = "invalid_paths"
            else:
                return await self._async_next_after_paths()

        return self.async_show_form(
            step_id="paths",
            data_schema=vol.Schema(
                {vol.Required(CONF_BROWSE_PATHS, default=self._browse_paths): PATHS_SELECTOR}
            ),
            errors=errors,
        )

    async def _async_next_after_paths(self) -> ConfigFlowResult:
        """Ask about zones when there is more than one."""
        assert self._ms is not None
        self._zone_names = [z.name for z in await self._ms.get_zones()]
        if len(self._zone_names) > 1:
            return await self.async_step_zones()
        return await self.async_step_select_playback_fields()

    async def async_step_zones(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask whether zones should become separate devices."""
        if user_input is not None:
            self._device_per_zone = user_input[CONF_DEVICE_PER_ZONE]
            if self._device_per_zone:
                return await self.async_step_select_zones()
            return await self.async_step_select_playback_fields()

        return self.async_show_form(
            step_id="zones",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_PER_ZONE, default=self._device_per_zone): bool}
            ),
            errors={},
        )

    async def async_step_select_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose which zones become devices."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._device_zones = user_input[CONF_DEVICE_ZONES]
            if not self._device_zones:
                errors["base"] = "no_zones"
            else:
                return await self.async_step_select_playback_fields()

        return self.async_show_form(
            step_id="select_zones",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_ZONES, default=self._device_zones or self._zone_names
                    ): SelectSelector(SelectSelectorConfig(multiple=True, options=self._zone_names))
                }
            ),
            errors=errors,
        )

    async def async_step_select_playback_fields(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the extra library fields to expose."""
        if user_input is not None:
            self._extra_fields = user_input.get(CONF_EXTRA_FIELDS, [])
            return self.async_create_entry(
                title=self._friendly_name or self._host,
                data=self._entry_data(),
                options=self._entry_options(),
            )

        await self._async_load_library_fields()

        return self.async_show_form(
            step_id="select_playback_fields",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EXTRA_FIELDS, default=self._extra_fields): SelectSelector(
                        SelectSelectorConfig(multiple=True, options=self._library_fields)
                    )
                }
            ),
            errors={},
        )

    # -- reauth ----------------------------------------------------------

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Start a reauthentication flow."""
        self._username = entry_data.get(CONF_USERNAME)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for fresh credentials."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            data = {**entry.data, **user_input}
            try:
                await connect_to_media_server(self.hass, data)
            except AbortFlow:
                raise
            except Exception as err:  # noqa: BLE001
                errors["base"] = self._reason_for(err)
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME,
                        description={"suggested_value": entry.data.get(CONF_USERNAME)},
                    ): str,
                    vol.Optional(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
            description_placeholders={"name": entry.title},
        )

    # -- reconfigure -----------------------------------------------------

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change where the server lives."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            self._access_key = user_input.get(CONF_API_KEY, "")
            self._host = user_input.get(CONF_HOST, "")
            self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
            self._ssl = user_input.get(CONF_SSL, DEFAULT_SSL)
            self._friendly_name = user_input.get(CONF_NAME, "")
            self._username = entry.data.get(CONF_USERNAME)
            self._password = entry.data.get(CONF_PASSWORD)
            try:
                await self._async_connect()
            except AbortFlow:
                raise
            except Exception as err:  # noqa: BLE001
                errors["base"] = self._reason_for(err)
            else:
                await self.async_set_unique_id(self._resolve_unique_id())
                self._abort_if_unique_id_mismatch(reason="wrong_server")
                return self.async_update_reload_and_abort(
                    entry,
                    title=self._friendly_name or self._host,
                    data_updates={
                        CONF_API_KEY: self._access_key,
                        CONF_HOST: self._host,
                        CONF_PORT: self._port,
                        CONF_SSL: self._ssl,
                        CONF_NAME: self._friendly_name,
                        CONF_MAC: self._mac_addresses or entry.data.get(CONF_MAC, []),
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_API_KEY, default=entry.data.get(CONF_API_KEY, "")): str,
                    vol.Optional(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
                    vol.Optional(CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
                    vol.Optional(CONF_NAME, default=entry.data.get(CONF_NAME, "")): str,
                    vol.Required(CONF_SSL, default=entry.data.get(CONF_SSL, DEFAULT_SSL)): bool,
                }
            ),
            errors=errors,
        )

    # -- helpers ---------------------------------------------------------

    @property
    def _supports_browse_rules(self) -> bool:
        if self._ms is None or self._ms.media_server_info is None:
            return False
        return bool(self._ms.media_server_info.supports_browse_rules)

    @staticmethod
    def _reason_for(err: Exception) -> str:
        for error_type, reason in ERROR_REASONS.items():
            if isinstance(err, error_type):
                return reason
        _LOGGER.exception("Unexpected exception", exc_info=err)
        return "unknown"

    async def _async_connect(self) -> None:
        """Connect and capture what the server tells us about itself."""
        self._ms, macs = await connect_to_media_server(self.hass, self._entry_data())
        self._host = self._ms.host
        self._port = self._ms.port
        info = self._ms.media_server_info
        if not self._friendly_name and info:
            self._friendly_name = info.name
        if macs:
            self._mac_addresses = macs
            self._expect_wol = True

    def _resolve_unique_id(self) -> str:
        """Prefer the server access key, fall back to host and port."""
        info = self._ms.media_server_info if self._ms else None
        if info and info.access_key:
            return info.access_key
        if self._access_key:
            return self._access_key
        return f"{self._host}:{self._port}"

    async def _async_set_unique_id(self) -> None:
        await self.async_set_unique_id(self._resolve_unique_id())
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host, CONF_PORT: self._port})

    async def _async_load_library_fields(self) -> None:
        if not self._library_fields and self._ms is not None:
            try:
                self._library_fields = sorted(f.name for f in await self._ms.get_library_fields())
            except MediaServerError as err:
                _LOGGER.debug("Unable to load library fields: %r", err)
                self._library_fields = []

    @callback
    def _show_user_form(self, errors: dict[str, str]) -> ConfigFlowResult:
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_API_KEY, default=self._access_key): str,
                    vol.Optional(CONF_HOST, default=self._host): str,
                    vol.Optional(CONF_PORT, default=self._port or DEFAULT_PORT): int,
                    vol.Optional(CONF_NAME, default=self._friendly_name): str,
                    vol.Required(CONF_SSL, default=self._ssl): bool,
                }
            ),
            errors=errors,
        )

    @callback
    def _entry_data(self) -> dict[str, Any]:
        return {
            CONF_API_KEY: self._access_key,
            CONF_NAME: self._friendly_name,
            CONF_HOST: self._host,
            CONF_PORT: self._port,
            CONF_MAC: self._mac_addresses,
            CONF_USERNAME: self._username,
            CONF_PASSWORD: self._password,
            CONF_SSL: self._ssl,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

    @callback
    def _entry_options(self) -> dict[str, Any]:
        return {
            CONF_BROWSE_PATHS: self._browse_paths,
            CONF_DEVICE_PER_ZONE: self._device_per_zone,
            CONF_DEVICE_ZONES: self._device_zones,
            CONF_EXTRA_FIELDS: self._extra_fields,
            CONF_USE_WOL: self._expect_wol,
            CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
            CONF_TURN_OFF_BEHAVIOUR: DEFAULT_TURN_OFF_BEHAVIOUR.value,
            CONF_DSP_PRESETS: [],
        }

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> JRiverOptionsFlowHandler:
        """Return the options flow."""
        return JRiverOptionsFlowHandler()


class JRiverOptionsFlowHandler(OptionsFlow):
    """Change how an existing entry behaves."""

    def __init__(self) -> None:
        """Initialise the options flow."""
        self._ms: MediaServer | None = None
        self._zone_names: list[str] = []
        self._library_fields: list[str] = []
        self._options: dict[str, Any] = {}

    def _existing(self, key: str, default: Any = None) -> Any:
        if key in self.config_entry.options:
            return self.config_entry.options[key]
        if key in self.config_entry.data:
            return self.config_entry.data[key]
        return default

    async def _async_connect(self) -> str | None:
        """Connect to the server, returning an error reason on failure."""
        if self._ms is not None:
            return None
        try:
            self._ms, _ = await connect_to_media_server(self.hass, dict(self.config_entry.data))
        except AbortFlow:
            raise
        except Exception as err:  # noqa: BLE001
            return JRiverConfigFlow._reason_for(err)
        self._zone_names = [z.name for z in await self._ms.get_zones()]
        return None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Set the polling, power and DSP options."""
        errors: dict[str, str] = {}
        if (reason := await self._async_connect()) is not None:
            errors["base"] = reason

        if user_input is not None and not errors:
            self._options.update(
                {
                    CONF_POLL_INTERVAL: int(user_input[CONF_POLL_INTERVAL]),
                    CONF_TURN_OFF_BEHAVIOUR: user_input[CONF_TURN_OFF_BEHAVIOUR],
                    CONF_DSP_PRESETS: user_input.get(CONF_DSP_PRESETS, []),
                }
            )
            return await self.async_step_zones()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=self._existing(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): POLL_SELECTOR,
                    vol.Required(
                        CONF_TURN_OFF_BEHAVIOUR,
                        default=self._existing(
                            CONF_TURN_OFF_BEHAVIOUR, DEFAULT_TURN_OFF_BEHAVIOUR.value
                        ),
                    ): TURN_OFF_SELECTOR,
                    vol.Optional(
                        CONF_DSP_PRESETS, default=self._existing(CONF_DSP_PRESETS, [])
                    ): PRESETS_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_zones(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose the zone topology."""
        errors: dict[str, str] = {}
        if user_input is not None:
            per_zone = user_input[CONF_DEVICE_PER_ZONE]
            zones = user_input.get(CONF_DEVICE_ZONES, [])
            if per_zone and not zones:
                errors["base"] = "no_zones"
            else:
                self._options[CONF_DEVICE_PER_ZONE] = per_zone
                self._options[CONF_DEVICE_ZONES] = zones
                return await self.async_step_paths()

        return self.async_show_form(
            step_id="zones",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_PER_ZONE,
                        default=self._existing(CONF_DEVICE_PER_ZONE, DEFAULT_DEVICE_PER_ZONE),
                    ): bool,
                    vol.Optional(
                        CONF_DEVICE_ZONES,
                        default=self._existing(CONF_DEVICE_ZONES, []) or [],
                    ): SelectSelector(
                        SelectSelectorConfig(multiple=True, options=self._zone_names)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_paths(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect browse paths for servers without Browse/Rules."""
        info = self._ms.media_server_info if self._ms else None
        if info is not None and info.supports_browse_rules:
            self._options[CONF_BROWSE_PATHS] = self._existing(CONF_BROWSE_PATHS, [])
            return await self.async_step_macs()

        errors: dict[str, str] = {}
        existing = self._existing(CONF_BROWSE_PATHS, []) or sorted(DEFAULT_BROWSE_PATHS)
        if user_input is not None:
            paths = user_input.get(CONF_BROWSE_PATHS, [])
            if not paths:
                errors["base"] = "no_paths"
            elif parse_browse_paths_from_text(paths) is None:
                errors["base"] = "invalid_paths"
            else:
                self._options[CONF_BROWSE_PATHS] = paths
                return await self.async_step_macs()

        return self.async_show_form(
            step_id="paths",
            data_schema=vol.Schema(
                {vol.Required(CONF_BROWSE_PATHS, default=existing): PATHS_SELECTOR}
            ),
            errors=errors,
        )

    async def async_step_macs(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect the wake on LAN MAC addresses."""
        errors: dict[str, str] = {}
        if user_input is not None:
            macs = user_input.get(CONF_MAC, [])
            use_wol = user_input[CONF_USE_WOL]
            if use_wol and not macs:
                errors["base"] = "no_mac_addresses"
            elif any(invalid_mac(m) for m in macs):
                errors["base"] = "invalid_mac"
            else:
                self._options[CONF_USE_WOL] = use_wol
                self._options[CONF_MAC] = (
                    [m.replace("-", ":").lower() for m in macs] if use_wol else []
                )
                return await self.async_step_fields()

        return self.async_show_form(
            step_id="macs",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USE_WOL, default=self._existing(CONF_USE_WOL, False)): bool,
                    vol.Optional(
                        CONF_MAC, default=self._existing(CONF_MAC, []) or []
                    ): MAC_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_fields(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose the extra library fields and save."""
        if user_input is not None:
            self._options[CONF_EXTRA_FIELDS] = user_input.get(CONF_EXTRA_FIELDS, [])
            return self.async_create_entry(title="", data=self._options)

        if not self._library_fields and self._ms is not None:
            try:
                self._library_fields = sorted(f.name for f in await self._ms.get_library_fields())
            except MediaServerError as err:
                _LOGGER.debug("Unable to load library fields: %r", err)

        return self.async_show_form(
            step_id="fields",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EXTRA_FIELDS,
                        default=self._existing(CONF_EXTRA_FIELDS, []) or [],
                    ): SelectSelector(
                        SelectSelectorConfig(multiple=True, options=self._library_fields)
                    )
                }
            ),
            errors={},
        )
