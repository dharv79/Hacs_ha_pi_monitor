"""Constants for the Raspberry Pi Monitor integration."""
from __future__ import annotations

DOMAIN = "rpi_monitor"
MANUFACTURER = "Raspberry Pi Foundation"
MODEL = "Raspberry Pi"

CONF_UPDATE_INTERVAL = "update_interval"
CONF_DISPLAY_NAME = "display_name"

DEFAULT_DISPLAY_NAME = "Raspberry Pi"
DEFAULT_UPDATE_INTERVAL = 30
MIN_UPDATE_INTERVAL = 10
MAX_UPDATE_INTERVAL = 3600

KEY_CPU_USAGE_TOTAL = "cpu_usage_total"
KEY_CPU_USAGE_CORE = "cpu_usage_core_{}"

KEY_CPU_FREQ_CURRENT = "cpu_freq_current"
KEY_CPU_FREQ_VCGENCMD = "cpu_freq_vcgencmd"

KEY_CPU_LOAD_1 = "cpu_load_1"
KEY_CPU_LOAD_5 = "cpu_load_5"
KEY_CPU_LOAD_15 = "cpu_load_15"

KEY_RAM_USAGE_PCT = "ram_usage_pct"
KEY_RAM_USED_MB = "ram_used_mb"
KEY_RAM_AVAILABLE_MB = "ram_available_mb"
KEY_RAM_TOTAL_MB = "ram_total_mb"
KEY_SWAP_USAGE_PCT = "swap_usage_pct"
KEY_SWAP_USED_MB = "swap_used_mb"

KEY_DISK_USAGE_PCT = "disk_usage_pct"
KEY_DISK_USED_GB = "disk_used_gb"
KEY_DISK_FREE_GB = "disk_free_gb"
KEY_DISK_TOTAL_GB = "disk_total_gb"

KEY_TEMP_CPU = "temp_cpu"
KEY_TEMP_GPU = "temp_gpu"

KEY_NET_BYTES_SENT = "net_bytes_sent"
KEY_NET_BYTES_RECV = "net_bytes_recv"
KEY_NET_RATE_SEND = "net_rate_send"
KEY_NET_RATE_RECV = "net_rate_recv"

KEY_UPTIME_SECONDS = "uptime_seconds"
KEY_PROCESS_COUNT = "process_count"
KEY_BOOT_TIME = "boot_time"

KEY_POWER_VOLTS_IN = "power_volts_in"
KEY_POWER_AMPS_IN = "power_amps_in"
KEY_POWER_WATTS = "power_watts"

KEY_THROTTLE_ACTIVE = "throttle_active"
KEY_UNDERVOLTAGE_NOW = "undervoltage_now"
KEY_UNDERVOLTAGE_OCCURRED = "undervoltage_occurred"
KEY_THERMAL_THROTTLE_OCCURRED = "thermal_throttle_occurred"

# Bit positions in vcgencmd get_throttled hex value (from official RPi docs)
THROTTLE_BIT_UNDERVOLTAGE_NOW = 0
THROTTLE_BIT_FREQ_CAP_NOW = 1
THROTTLE_BIT_THROTTLED_NOW = 2
THROTTLE_BIT_SOFT_TEMP_LIMIT_NOW = 3
THROTTLE_BIT_UNDERVOLTAGE_OCCURRED = 16
THROTTLE_BIT_FREQ_CAP_OCCURRED = 17
THROTTLE_BIT_THROTTLED_OCCURRED = 18
THROTTLE_BIT_SOFT_TEMP_OCCURRED = 19
