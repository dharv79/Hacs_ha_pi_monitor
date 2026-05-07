# Raspberry Pi Monitor for Home Assistant

A HACS custom integration that exposes Raspberry Pi system metrics as Home Assistant sensors — CPU, memory, storage, temperatures, network, and Raspberry Pi-specific diagnostics.

## Features

- **CPU** — overall usage %, per-core usage %, frequency (MHz), load averages (1/5/15 min)
- **Memory** — RAM and swap usage %, used/available/total (MB)
- **Storage** — root filesystem usage %, used/free/total (GB)
- **Temperatures** — CPU temperature (°C) and GPU temperature (°C via `vcgencmd`)
- **Network** — cumulative bytes sent/received (MB) and live upload/download rates (MB/s)
- **System** — uptime, last boot timestamp, process count
- **RPi-specific** — throttle state, undervoltage detection, sticky "occurred since boot" flags (requires `vcgencmd`)

All monitoring is local — the integration reads directly from the machine running Home Assistant.

## Requirements

- Home Assistant 2023.1.0 or later
- `psutil` — installed automatically by HA on first load
- `vcgencmd` — optional; RPi-specific sensors are simply not created if absent

## Installation

### Via HACS (recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations** → three-dot menu → **Custom repositories**
3. Add `https://github.com/dharv79/Hacs_ha_pi_monitor` as type **Integration**
4. Search for **Raspberry Pi Monitor** and click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **Raspberry Pi Monitor** and follow the setup wizard

### Manual

Copy `custom_components/rpi_monitor/` into your HA `config/custom_components/` directory, then restart Home Assistant.

## Configuration

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| Display name | Raspberry Pi | — | Name shown in the device registry |
| Update interval | 30 s | 10–3600 s | How often metrics are polled |

Change the update interval after setup via the integration's **Configure** button.

## Sensors

### CPU

| Entity | Unit | Notes |
|--------|------|-------|
| CPU Usage | % | Overall usage across all cores |
| CPU Core N Usage | % | Per logical core (auto-detected count) |
| CPU Frequency | MHz | Current scaling frequency (psutil) |
| CPU Frequency (vcgencmd) | MHz | ARM clock via vcgencmd *(requires vcgencmd)* |
| Load Average (1 min) | — | Unix 1-minute load average |
| Load Average (5 min) | — | Unix 5-minute load average |
| Load Average (15 min) | — | Unix 15-minute load average |

### Memory

| Entity | Unit |
|--------|------|
| RAM Usage | % |
| RAM Used | MB |
| RAM Available | MB |
| RAM Total | MB |
| Swap Usage | % |
| Swap Used | MB |

### Storage

| Entity | Unit |
|--------|------|
| Disk Usage | % |
| Disk Used | GB |
| Disk Free | GB |
| Disk Total | GB |

### Temperature

| Entity | Unit | Notes |
|--------|------|-------|
| CPU Temperature | °C | Via psutil or `/sys/class/thermal/thermal_zone0/temp` |
| GPU Temperature | °C | Via `vcgencmd measure_temp` *(requires vcgencmd)* |

On Raspberry Pi, the CPU and GPU share the same SoC thermal sensor so values will typically be identical.

### Network

| Entity | Unit | Notes |
|--------|------|-------|
| Network Bytes Sent | MB | Cumulative since boot |
| Network Bytes Received | MB | Cumulative since boot |
| Network Upload Rate | MB/s | Calculated between polls |
| Network Download Rate | MB/s | Calculated between polls |

### System

| Entity | Unit |
|--------|------|
| System Uptime | seconds |
| Last Boot | timestamp |
| Process Count | — |

### Raspberry Pi Specific *(requires vcgencmd)*

| Entity | Notes |
|--------|-------|
| CPU Throttled | `on` when currently throttled or frequency-capped |
| Undervoltage Detected | `on` when supply voltage is currently low |
| Undervoltage Occurred (Since Boot) | `on` if undervoltage has occurred since last boot |
| Thermal Throttle Occurred (Since Boot) | `on` if thermal throttling has occurred since last boot |

## Troubleshooting

**No RPi-specific sensors appear**

`vcgencmd` was not found. On Raspberry Pi OS install it with:
```bash
sudo apt install libraspberrypi-bin
```
Then reload the integration.

**All sensors show Unavailable**

Check Home Assistant logs for errors under `custom_components.rpi_monitor`. The most common cause is `psutil` failing to install — check HA has internet access on first boot.

**CPU temperature always unavailable**

Ensure `/sys/class/thermal/thermal_zone0/temp` is readable, or that `psutil.sensors_temperatures()` returns data on your OS.

**Network rates show Unavailable on first poll**

This is normal — rates require two data points to calculate a delta. They will become available on the second poll (one update interval after startup).
