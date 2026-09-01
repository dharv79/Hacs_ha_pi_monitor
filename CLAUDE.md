# CLAUDE.md — Raspberry Pi Monitor for Home Assistant

## Project Overview

A HACS custom integration (`domain: rpi_monitor`) that monitors the Raspberry Pi running Home Assistant. All data is collected locally via `psutil` and the optional `vcgencmd` CLI tool. No network requests are made.

## Repository Layout

```
Hacs_ha_pi_monitor/
├── hacs.json                          HACS store metadata
├── README.md                          User-facing docs
├── CLAUDE.md                          This file
└── custom_components/
    └── rpi_monitor/
        ├── __init__.py                Entry point: async_setup_entry / async_unload_entry
        ├── manifest.json              HA integration manifest (requirements, version, etc.)
        ├── const.py                   All constants and sensor key strings
        ├── coordinator.py             DataUpdateCoordinator — all data collection lives here
        ├── config_flow.py             UI setup flow + options flow (update interval)
        ├── sensor.py                  Sensor entity descriptions + RpiSensor class
        ├── brand/
        │   ├── icon.png               256×256 Raspberry Pi logo (HA 2026.3+ auto-discovery)
        │   ├── icon@2x.png            512×512 retina version
        │   └── logo.png              256×256 logo variant
        └── translations/
            └── en.json                UI strings for config/options flow
```

## Architecture

### Data flow

```
async_setup_entry (__init__.py)
  └─ RpiMonitorCoordinator.async_setup()     detect vcgencmd once
  └─ coordinator.async_config_entry_first_refresh()
        └─ _async_update_data()
              └─ hass.async_add_executor_job(_fetch_all_sync)
                    ├─ psutil calls (CPU, mem, disk, temp, net, uptime)
                    └─ vcgencmd subprocess calls (GPU temp, throttle, ARM clock)
  └─ async_forward_entry_setups → sensor.py
        └─ async_setup_entry → creates ~30+ RpiSensor entities
              └─ each entity reads coordinator.data[key] on update
```

### Key design decisions

- **Single executor call per poll** — `_fetch_all_sync` collects everything in one thread; no per-sensor blocking.
- **`cpu_percent(interval=None)`** — non-blocking; first poll returns 0.0, accurate from second poll onward.
- **Network rates** — calculated from delta between successive polls using `time.monotonic()`. First poll returns `None` (renders as "unavailable" in HA, self-corrects next poll).
- **vcgencmd graceful degradation** — detected once at startup via `_detect_vcgencmd()`. If absent, sensors with `vcgencmd_required=True` are simply never registered. Individual per-poll subprocess calls are each wrapped with a 3-second timeout.
- **Single HA device** — all sensors grouped under one device (device name configurable, defaults to "Raspberry Pi").
- **Single instance enforcement** — `async_set_unique_id(DOMAIN)` + `_abort_if_unique_id_configured()` in config flow.

## Sensor Keys (`const.py`)

All coordinator data dict keys are defined in `const.py` and shared between `coordinator.py` and `sensor.py`. Per-core keys use a format string: `KEY_CPU_USAGE_CORE = "cpu_usage_core_{}"` → `"cpu_usage_core_0"`, `"cpu_usage_core_1"`, etc.

## Adding New Sensors

1. Add a `KEY_*` constant to `const.py`
2. Populate the value in `coordinator.py` → `_fetch_all_sync()`
3. Add a `RpiSensorEntityDescription(...)` to `SENSOR_DESCRIPTIONS` in `sensor.py`
4. If it requires `vcgencmd`, set `vcgencmd_required=True`

## Config & Options

- **Config flow**: collects `display_name` (str) and `update_interval` (int, 10–3600 s)
- **Options flow**: allows changing `update_interval` after setup; triggers a full reload via `_async_reload_entry`
- Config data lives in `entry.data`; options override via `entry.options` (options take precedence in `__init__.py`)

## Brand / Icons

Icons live in `custom_components/rpi_monitor/brand/`. HA 2026.3.0+ serves them automatically via the brands proxy API — no submission to `github.com/home-assistant/brands` needed for local display.

For HACS store display (if submitting to HACS default repository), the domain must also be added to `https://github.com/home-assistant/brands` under `custom_integrations/rpi_monitor/`.

## Testing Locally

### Install into a running HA instance

```bash
cp -r custom_components/rpi_monitor /path/to/ha/config/custom_components/
# Restart Home Assistant
```

### Check logs for integration startup

```
Settings → System → Logs → filter "rpi_monitor"
```

Look for:
- `vcgencmd found at /usr/bin/vcgencmd` (or "not found")
- Any `UpdateFailed` errors from the coordinator

### Verify sensors

After setup, `Settings → Devices & Services → Raspberry Pi Monitor → {device name}` should show ~30 entities (fewer if vcgencmd is absent).

### Manual psutil test (on the Pi)

```bash
python3 -c "
import psutil, time
print('CPU:', psutil.cpu_percent(interval=1))
print('Mem:', psutil.virtual_memory().percent)
print('Disk:', psutil.disk_usage('/').percent)
temps = psutil.sensors_temperatures()
print('Temps:', temps)
"
```

### Manual vcgencmd test

```bash
vcgencmd measure_temp        # GPU temp
vcgencmd get_throttled       # throttle hex bitmask
vcgencmd measure_clock arm   # ARM CPU frequency
```

## Dependencies

| Dependency | Source | Purpose |
|------------|--------|---------|
| `psutil>=5.9.0` | PyPI (auto-installed by HA) | CPU, memory, disk, temp, network |
| `vcgencmd` | System binary (`libraspberrypi-bin`) | GPU temp, throttle state, ARM clock |

## Versioning

Version is set in `custom_components/rpi_monitor/manifest.json`. Use semantic versioning (`MAJOR.MINOR.PATCH`). Bump on every user-facing release.

## Branch Strategy

- `main` — stable, HACS-installable
- Feature branches → merge to `main` via PR

## Code Output & Efficiency Directives

- Output only modified functions or specific blocks; never rewrite entire files unless fundamentally restructuring them.
- Do not echo back code, errors, or logs provided in the prompt.
- Omit boilerplate, import statements, and setup code unless they are being modified.
- Provide code edits directly without introductory or concluding explanations.
- **Workflow Requirement:** Whenever a complex task is completed or before starting a completely new substantive task in this session, explicitly remind the user to run `/compact` to compress the chat history.
