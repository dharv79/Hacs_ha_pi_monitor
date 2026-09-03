"""DataUpdateCoordinator for Raspberry Pi Monitor."""
from __future__ import annotations

import logging
import subprocess
import time
from datetime import timedelta
from typing import Any

import psutil

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
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
    KEY_POWER_AMPS_IN,
    KEY_POWER_VOLTS_IN,
    KEY_POWER_WATTS,
    KEY_TEMP_CPU,
    KEY_TEMP_GPU,
    KEY_THERMAL_THROTTLE_OCCURRED,
    KEY_THROTTLE_ACTIVE,
    KEY_UNDERVOLTAGE_NOW,
    KEY_UNDERVOLTAGE_OCCURRED,
    KEY_UPTIME_SECONDS,
    THROTTLE_BIT_FREQ_CAP_NOW,
    THROTTLE_BIT_THROTTLED_NOW,
    THROTTLE_BIT_THROTTLED_OCCURRED,
    THROTTLE_BIT_UNDERVOLTAGE_NOW,
    THROTTLE_BIT_UNDERVOLTAGE_OCCURRED,
)

_LOGGER = logging.getLogger(__name__)

_VCGENCMD_PATHS = ["/usr/bin/vcgencmd", "/opt/vc/bin/vcgencmd"]


class RpiMonitorCoordinator(DataUpdateCoordinator):
    """Polls all RPi system metrics on a schedule."""

    def __init__(self, hass: HomeAssistant, update_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self._vcgencmd_path: str | None = None
        self._vcgencmd_available: bool = False
        self._prev_net_bytes_sent: int | None = None
        self._prev_net_bytes_recv: int | None = None
        self._prev_net_timestamp: float | None = None
        self._num_cores: int = psutil.cpu_count(logical=True) or 4

    async def async_setup(self) -> None:
        """Detect vcgencmd availability once at startup."""
        self._vcgencmd_path = await self.hass.async_add_executor_job(
            self._detect_vcgencmd
        )
        self._vcgencmd_available = self._vcgencmd_path is not None
        if self._vcgencmd_available:
            _LOGGER.info("vcgencmd found at %s — RPi-specific sensors enabled", self._vcgencmd_path)
        else:
            _LOGGER.info("vcgencmd not found — RPi-specific sensors will be unavailable")

    def _detect_vcgencmd(self) -> str | None:
        for path in _VCGENCMD_PATHS:
            try:
                result = subprocess.run(
                    [path, "version"],
                    capture_output=True,
                    timeout=3,
                    check=False,
                )
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._fetch_all_sync)
        except Exception as err:
            raise UpdateFailed(f"Error fetching RPi metrics: {err}") from err

    def _fetch_all_sync(self) -> dict[str, Any]:
        """Collect all metrics in one blocking call (runs in executor thread)."""
        data: dict[str, Any] = {}

        # CPU
        data[KEY_CPU_USAGE_TOTAL] = psutil.cpu_percent(interval=None)
        for i, pct in enumerate(psutil.cpu_percent(percpu=True, interval=None)):
            data[KEY_CPU_USAGE_CORE.format(i)] = pct

        freq = psutil.cpu_freq()
        data[KEY_CPU_FREQ_CURRENT] = round(freq.current, 1) if freq else None

        try:
            load1, load5, load15 = psutil.getloadavg()
            data[KEY_CPU_LOAD_1] = round(load1, 2)
            data[KEY_CPU_LOAD_5] = round(load5, 2)
            data[KEY_CPU_LOAD_15] = round(load15, 2)
        except AttributeError:
            data[KEY_CPU_LOAD_1] = None
            data[KEY_CPU_LOAD_5] = None
            data[KEY_CPU_LOAD_15] = None

        # Memory
        vm = psutil.virtual_memory()
        data[KEY_RAM_USAGE_PCT] = vm.percent
        data[KEY_RAM_USED_MB] = round(vm.used / 1024 / 1024, 1)
        data[KEY_RAM_AVAILABLE_MB] = round(vm.available / 1024 / 1024, 1)
        data[KEY_RAM_TOTAL_MB] = round(vm.total / 1024 / 1024, 1)

        sw = psutil.swap_memory()
        data[KEY_SWAP_USAGE_PCT] = sw.percent
        data[KEY_SWAP_USED_MB] = round(sw.used / 1024 / 1024, 1)

        # Disk (root filesystem)
        disk = psutil.disk_usage("/")
        data[KEY_DISK_USAGE_PCT] = disk.percent
        data[KEY_DISK_USED_GB] = round(disk.used / 1024 / 1024 / 1024, 2)
        data[KEY_DISK_FREE_GB] = round(disk.free / 1024 / 1024 / 1024, 2)
        data[KEY_DISK_TOTAL_GB] = round(disk.total / 1024 / 1024 / 1024, 2)

        # Temperatures
        data[KEY_TEMP_CPU] = self._get_cpu_temp()
        data[KEY_TEMP_GPU] = self._get_gpu_temp()

        # Network
        net = psutil.net_io_counters()
        now = time.monotonic()
        data[KEY_NET_BYTES_SENT] = round(net.bytes_sent / 1024 / 1024, 2)
        data[KEY_NET_BYTES_RECV] = round(net.bytes_recv / 1024 / 1024, 2)

        if self._prev_net_bytes_sent is not None and self._prev_net_timestamp is not None:
            dt = now - self._prev_net_timestamp
            if dt > 0:
                delta_sent = net.bytes_sent - self._prev_net_bytes_sent
                delta_recv = net.bytes_recv - self._prev_net_bytes_recv
                # Guard against counter reset on reboot
                data[KEY_NET_RATE_SEND] = round(max(0, delta_sent) / dt / 1024 / 1024, 4)
                data[KEY_NET_RATE_RECV] = round(max(0, delta_recv) / dt / 1024 / 1024, 4)
            else:
                data[KEY_NET_RATE_SEND] = 0.0
                data[KEY_NET_RATE_RECV] = 0.0
        else:
            data[KEY_NET_RATE_SEND] = None
            data[KEY_NET_RATE_RECV] = None

        self._prev_net_bytes_sent = net.bytes_sent
        self._prev_net_bytes_recv = net.bytes_recv
        self._prev_net_timestamp = now

        # System
        boot_time = psutil.boot_time()
        data[KEY_BOOT_TIME] = boot_time
        data[KEY_UPTIME_SECONDS] = round(time.time() - boot_time)
        data[KEY_PROCESS_COUNT] = len(psutil.pids())

        # RPi-specific (vcgencmd)
        if self._vcgencmd_available:
            self._fetch_vcgencmd(data)
        else:
            data[KEY_THROTTLE_ACTIVE] = None
            data[KEY_UNDERVOLTAGE_NOW] = None
            data[KEY_UNDERVOLTAGE_OCCURRED] = None
            data[KEY_THERMAL_THROTTLE_OCCURRED] = None
            data[KEY_CPU_FREQ_VCGENCMD] = None
            data[KEY_POWER_VOLTS_IN] = None
            data[KEY_POWER_AMPS_IN] = None
            data[KEY_POWER_WATTS] = None

        return data

    def _get_cpu_temp(self) -> float | None:
        """Read CPU temperature: try psutil first, then /sys fallback."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for label in ("cpu_thermal", "coretemp", "k10temp", "acpitz"):
                    if label in temps and temps[label]:
                        return round(temps[label][0].current, 1)
                first_key = next(iter(temps))
                if temps[first_key]:
                    return round(temps[first_key][0].current, 1)
        except (AttributeError, NotImplementedError):
            pass

        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read().strip()) / 1000.0, 1)
        except (OSError, ValueError):
            pass

        return None

    def _get_gpu_temp(self) -> float | None:
        """Read GPU temperature via vcgencmd measure_temp."""
        if not self._vcgencmd_available:
            return None
        try:
            result = subprocess.run(
                [self._vcgencmd_path, "measure_temp"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            raw = result.stdout.strip()
            if raw.startswith("temp="):
                return round(float(raw.split("=")[1].rstrip("'C")), 1)
        except (subprocess.TimeoutExpired, ValueError, OSError):
            pass
        return None

    def _fetch_vcgencmd(self, data: dict[str, Any]) -> None:
        """Populate vcgencmd-derived keys."""
        throttle_bits = self._read_throttle_bits()
        if throttle_bits is not None:
            data[KEY_THROTTLE_ACTIVE] = bool(
                throttle_bits & (1 << THROTTLE_BIT_THROTTLED_NOW)
                or throttle_bits & (1 << THROTTLE_BIT_FREQ_CAP_NOW)
            )
            data[KEY_UNDERVOLTAGE_NOW] = bool(
                throttle_bits & (1 << THROTTLE_BIT_UNDERVOLTAGE_NOW)
            )
            data[KEY_UNDERVOLTAGE_OCCURRED] = bool(
                throttle_bits & (1 << THROTTLE_BIT_UNDERVOLTAGE_OCCURRED)
            )
            data[KEY_THERMAL_THROTTLE_OCCURRED] = bool(
                throttle_bits & (1 << THROTTLE_BIT_THROTTLED_OCCURRED)
            )
        else:
            data[KEY_THROTTLE_ACTIVE] = None
            data[KEY_UNDERVOLTAGE_NOW] = None
            data[KEY_UNDERVOLTAGE_OCCURRED] = None
            data[KEY_THERMAL_THROTTLE_OCCURRED] = None

        data[KEY_CPU_FREQ_VCGENCMD] = self._read_clock_arm()

        pmic = self._read_pmic_adc()
        if pmic:
            volts = pmic.get("EXT5V_V")
            amps = pmic.get("EXT5V_I")
            data[KEY_POWER_VOLTS_IN] = round(volts, 3) if volts is not None else None
            data[KEY_POWER_AMPS_IN] = round(amps, 3) if amps is not None else None
            data[KEY_POWER_WATTS] = round(volts * amps, 2) if (volts is not None and amps is not None) else None
        else:
            data[KEY_POWER_VOLTS_IN] = None
            data[KEY_POWER_AMPS_IN] = None
            data[KEY_POWER_WATTS] = None

    def _read_throttle_bits(self) -> int | None:
        try:
            result = subprocess.run(
                [self._vcgencmd_path, "get_throttled"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            raw = result.stdout.strip()
            if raw.startswith("throttled="):
                return int(raw.split("=")[1], 16)
        except (subprocess.TimeoutExpired, ValueError, OSError):
            pass
        return None

    def _read_pmic_adc(self) -> dict[str, float] | None:
        """Read PMIC ADC values via vcgencmd (Raspberry Pi 5 only)."""
        try:
            result = subprocess.run(
                [self._vcgencmd_path, "pmic_read_adc"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            readings: dict[str, float] = {}
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        readings[parts[0]] = float(parts[1])
                    except ValueError:
                        pass
            return readings if readings else None
        except (subprocess.TimeoutExpired, OSError):
            return None

    def _read_clock_arm(self) -> float | None:
        try:
            result = subprocess.run(
                [self._vcgencmd_path, "measure_clock", "arm"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            raw = result.stdout.strip()
            if "=" in raw:
                return round(int(raw.split("=")[1]) / 1_000_000, 1)
        except (subprocess.TimeoutExpired, ValueError, OSError):
            pass
        return None

    @property
    def num_cores(self) -> int:
        return self._num_cores

    @property
    def vcgencmd_available(self) -> bool:
        return self._vcgencmd_available
