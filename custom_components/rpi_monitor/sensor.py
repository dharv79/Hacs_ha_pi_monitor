"""Sensor platform for Raspberry Pi Monitor."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfFrequency,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DISPLAY_NAME,
    DEFAULT_DISPLAY_NAME,
    DOMAIN,
    KEY_BOOT_TIME,
    KEY_CPU_FREQ_CURRENT,
    KEY_CPU_FREQ_VCGENCMD,
    KEY_CPU_LOAD_1,
    KEY_CPU_LOAD_5,
    KEY_CPU_LOAD_15,
    KEY_CPU_USAGE_CORE,
    KEY_CPU_USAGE_TOTAL,
    KEY_DISK_FREE_GB,
    KEY_DISK_TOTAL_GB,
    KEY_DISK_USAGE_PCT,
    KEY_DISK_USED_GB,
    KEY_NET_BYTES_RECV,
    KEY_NET_BYTES_SENT,
    KEY_NET_RATE_RECV,
    KEY_NET_RATE_SEND,
    KEY_PROCESS_COUNT,
    KEY_RAM_AVAILABLE_MB,
    KEY_RAM_TOTAL_MB,
    KEY_RAM_USAGE_PCT,
    KEY_RAM_USED_MB,
    KEY_SWAP_USAGE_PCT,
    KEY_SWAP_USED_MB,
    KEY_TEMP_CPU,
    KEY_TEMP_GPU,
    KEY_THERMAL_THROTTLE_OCCURRED,
    KEY_THROTTLE_ACTIVE,
    KEY_UNDERVOLTAGE_NOW,
    KEY_UNDERVOLTAGE_OCCURRED,
    KEY_UPTIME_SECONDS,
    MANUFACTURER,
    MODEL,
)
from .coordinator import RpiMonitorCoordinator


@dataclass(frozen=True, kw_only=True)
class RpiSensorEntityDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with RPi-specific flags."""

    vcgencmd_required: bool = False


SENSOR_DESCRIPTIONS: tuple[RpiSensorEntityDescription, ...] = (
    # --- CPU ---
    RpiSensorEntityDescription(
        key=KEY_CPU_USAGE_TOTAL,
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cpu-64-bit",
    ),
    RpiSensorEntityDescription(
        key=KEY_CPU_FREQ_CURRENT,
        name="CPU Frequency",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    RpiSensorEntityDescription(
        key=KEY_CPU_FREQ_VCGENCMD,
        name="CPU Frequency (vcgencmd)",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        vcgencmd_required=True,
    ),
    RpiSensorEntityDescription(
        key=KEY_CPU_LOAD_1,
        name="Load Average (1 min)",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
    ),
    RpiSensorEntityDescription(
        key=KEY_CPU_LOAD_5,
        name="Load Average (5 min)",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
    ),
    RpiSensorEntityDescription(
        key=KEY_CPU_LOAD_15,
        name="Load Average (15 min)",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
    ),
    # --- Memory ---
    RpiSensorEntityDescription(
        key=KEY_RAM_USAGE_PCT,
        name="RAM Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
    ),
    RpiSensorEntityDescription(
        key=KEY_RAM_USED_MB,
        name="RAM Used",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
    ),
    RpiSensorEntityDescription(
        key=KEY_RAM_AVAILABLE_MB,
        name="RAM Available",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
    ),
    RpiSensorEntityDescription(
        key=KEY_RAM_TOTAL_MB,
        name="RAM Total",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
    ),
    RpiSensorEntityDescription(
        key=KEY_SWAP_USAGE_PCT,
        name="Swap Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    RpiSensorEntityDescription(
        key=KEY_SWAP_USED_MB,
        name="Swap Used",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    # --- Disk ---
    RpiSensorEntityDescription(
        key=KEY_DISK_USAGE_PCT,
        name="Disk Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    RpiSensorEntityDescription(
        key=KEY_DISK_USED_GB,
        name="Disk Used",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    RpiSensorEntityDescription(
        key=KEY_DISK_FREE_GB,
        name="Disk Free",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    RpiSensorEntityDescription(
        key=KEY_DISK_TOTAL_GB,
        name="Disk Total",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
    ),
    # --- Temperature ---
    RpiSensorEntityDescription(
        key=KEY_TEMP_CPU,
        name="CPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    RpiSensorEntityDescription(
        key=KEY_TEMP_GPU,
        name="GPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        vcgencmd_required=True,
    ),
    # --- Network cumulative ---
    RpiSensorEntityDescription(
        key=KEY_NET_BYTES_SENT,
        name="Network Bytes Sent",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:upload-network",
    ),
    RpiSensorEntityDescription(
        key=KEY_NET_BYTES_RECV,
        name="Network Bytes Received",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:download-network",
    ),
    # --- Network rates ---
    RpiSensorEntityDescription(
        key=KEY_NET_RATE_SEND,
        name="Network Upload Rate",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload",
    ),
    RpiSensorEntityDescription(
        key=KEY_NET_RATE_RECV,
        name="Network Download Rate",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
    ),
    # --- System ---
    RpiSensorEntityDescription(
        key=KEY_UPTIME_SECONDS,
        name="System Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
    ),
    RpiSensorEntityDescription(
        key=KEY_PROCESS_COUNT,
        name="Process Count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:format-list-numbered",
    ),
    RpiSensorEntityDescription(
        key=KEY_BOOT_TIME,
        name="Last Boot",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:restart",
    ),
    # --- RPi-specific (vcgencmd) ---
    RpiSensorEntityDescription(
        key=KEY_THROTTLE_ACTIVE,
        name="CPU Throttled",
        icon="mdi:alert-circle",
        vcgencmd_required=True,
    ),
    RpiSensorEntityDescription(
        key=KEY_UNDERVOLTAGE_NOW,
        name="Undervoltage Detected",
        icon="mdi:flash-alert",
        vcgencmd_required=True,
    ),
    RpiSensorEntityDescription(
        key=KEY_UNDERVOLTAGE_OCCURRED,
        name="Undervoltage Occurred (Since Boot)",
        icon="mdi:flash-alert",
        vcgencmd_required=True,
    ),
    RpiSensorEntityDescription(
        key=KEY_THERMAL_THROTTLE_OCCURRED,
        name="Thermal Throttle Occurred (Since Boot)",
        icon="mdi:thermometer-alert",
        vcgencmd_required=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all sensor entities."""
    coordinator: RpiMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    display_name = entry.data.get(CONF_DISPLAY_NAME, DEFAULT_DISPLAY_NAME)

    entities: list[RpiSensor] = []

    for description in SENSOR_DESCRIPTIONS:
        if description.vcgencmd_required and not coordinator.vcgencmd_available:
            continue
        entities.append(RpiSensor(coordinator, entry, description, display_name))

    # Dynamically add one sensor per logical CPU core
    for core_idx in range(coordinator.num_cores):
        entities.append(
            RpiSensor(
                coordinator,
                entry,
                RpiSensorEntityDescription(
                    key=KEY_CPU_USAGE_CORE.format(core_idx),
                    name=f"CPU Core {core_idx} Usage",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    icon="mdi:cpu-64-bit",
                ),
                display_name,
            )
        )

    async_add_entities(entities)


class RpiSensor(CoordinatorEntity[RpiMonitorCoordinator], SensorEntity):
    """A single sensor entity backed by the coordinator."""

    entity_description: RpiSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RpiMonitorCoordinator,
        entry: ConfigEntry,
        description: RpiSensorEntityDescription,
        display_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=display_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        if self.entity_description.key == KEY_BOOT_TIME:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, bool):
            return "on" if value else "off"
        return value

    @property
    def available(self) -> bool:
        if not super().available or self.coordinator.data is None:
            return False
        return self.coordinator.data.get(self.entity_description.key) is not None
