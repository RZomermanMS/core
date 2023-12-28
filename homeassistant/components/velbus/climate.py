"""Support for Velbus thermostat."""
from __future__ import annotations

from typing import Any

from velbusaio.channels import Temperature as VelbusTemp

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PRESET_MODES
from .entity import VelbusEntity, api_call

THERMOSTAT_MODE_MAP: dict[str, HVACMode] = {
    """Set up Velbus switch based on config_entry."""
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
}
THERMOSTAT_INV_MODE_MAP = {v: k for k, v in THERMOSTAT_MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velbus switch based on config_entry."""
    await hass.data[DOMAIN][entry.entry_id]["tsk"]
    cntrl = hass.data[DOMAIN][entry.entry_id]["cntrl"]
    async_add_entities(VelbusClimate(channel) for channel in cntrl.get_all("climate"))


class VelbusClimate(VelbusEntity, ClimateEntity):
    """Representation of a Velbus thermostat."""

    _channel: VelbusTemp
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL]
    _attr_preset_modes = list(PRESET_MODES)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._channel.get_climate_target()

    @property
    def preset_mode(self) -> str | None:
        """Return the current Preset for this channel."""
        return next(
            (
                key
                for key, val in PRESET_MODES.items()
                if val == self._channel.get_climate_preset()
            ),
            None,
        )

    @property
    def current_temperature(self) -> int | None:
        """Return the current temperature."""
        return self._channel.get_state()

        @property
    def hvac_mode(self) -> HVACMode:
        """Return the current hvac mode based on cool_mode message."""
        if (mode := self._channel.get_cool_mode()) is None:
            return
        elif mode is True:
            return HVACMode.COOL
        elif mode is False:
            return HVACMode.HEAT

    @api_call
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperatures."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self._channel.set_temp(temp)
        self.async_write_ha_state()

    @api_call
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the new preset mode."""
        await self._channel.set_preset(PRESET_MODES[preset_mode])
        self.async_write_ha_state()

    @api_call
    async def async_set_hvac_mode(self, **kwargs: str) -> None:
        """Set the hvac mode."""
        if (mode := kwargs.get("hvac_mode")) is None:
            return
        await self._channel.set_mode(mode)
        self.async_write_ha_state()
