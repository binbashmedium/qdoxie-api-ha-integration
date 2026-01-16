"""Sensors for Doxie status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DoxiePaperlessCoordinator


@dataclass(frozen=True)
class DoxieSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[DoxieSensorEntityDescription, ...] = (
    DoxieSensorEntityDescription(
        key="connected",
        name="Doxie Connected",
        icon="mdi:lan-connect",
        value_fn=lambda data: data.get("hello") is not None,
    ),
    DoxieSensorEntityDescription(
        key="recent_scan",
        name="Doxie Last Scan Path",
        icon="mdi:scanner",
        value_fn=lambda data: data.get("recent_path"),
    ),
    DoxieSensorEntityDescription(
        key="scan_count",
        name="Doxie Scan Count",
        icon="mdi:file-multiple",
        value_fn=lambda data: data.get("scan_count"),
    ),
)

HELLO_ATTRS = (
    "model",
    "name",
    "firmware",
    "firmwareWiFi",
    "hasPassword",
    "MAC",
    "mode",
    "network",
    "ip",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DoxiePaperlessCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        DoxieStatusSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    ]

    # One extra sensor that exposes the hello.json payload as attributes.
    entities.append(DoxieHelloSensor(coordinator, entry))

    async_add_entities(entities)


class DoxieStatusSensor(CoordinatorEntity[DoxiePaperlessCoordinator], SensorEntity):
    entity_description: DoxieSensorEntityDescription

    def __init__(
        self,
        coordinator: DoxiePaperlessCoordinator,
        entry: ConfigEntry,
        description: DoxieSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(data)
        return None


class DoxieHelloSensor(CoordinatorEntity[DoxiePaperlessCoordinator], SensorEntity):
    _attr_icon = "mdi:information"
    _attr_name = "Doxie Info"

    def __init__(self, coordinator: DoxiePaperlessCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_hello"

    @property
    def native_value(self) -> str | None:
        hello = (self.coordinator.data or {}).get("hello")
        if not isinstance(hello, dict):
            return None
        # Use scanner name as main state if available.
        return hello.get("name")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        hello = (self.coordinator.data or {}).get("hello")
        if not isinstance(hello, dict):
            return {}
        return {k: hello.get(k) for k in HELLO_ATTRS if k in hello}
