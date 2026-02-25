# Telelumen API — Clean Architecture Documentation

## Overview

`api/telelumen_api.py` is a complete rewrite of the manufacturer's `api_tng.py` with a modern, maintainable architecture. It provides the same network-level behaviour as the original (same discovery algorithm, same command protocol) while exposing a clean, type-hinted Python interface.

**Author:** Théo Poujol  
**Created:** February 4, 2026  
**Last Modified:** February 25, 2026

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Configuration — `APIConfig`](#configuration--apiconfig)
4. [Enumerations](#enumerations)
5. [Exceptions](#exceptions)
6. [Logger](#logger)
7. [LuminaireConnection](#luminaireconnection)
8. [Luminaire](#luminaire)
9. [Discovery](#discovery)
10. [TelelumenAPI](#telelumenapi)
11. [Quick Start](#quick-start)
12. [Usage Examples](#usage-examples)
13. [Discovery Internals](#discovery-internals)
14. [Comparison with api_tng](#comparison-with-api_tng)

---

## Architecture Overview

```
TelelumenAPI          ← static facade, entry point for user code
    │
    ├── Discovery     ← network scan, returns Luminaire objects
    │       └── LuminaireConnection (raw telnet, reused after scan)
    │
    └── Luminaire     ← represents one device, holds its connection
            └── LuminaireConnection (telnet wrapper)
```

All classes are self-contained. `TelelumenAPI` is the recommended entry point for everyday use. `Luminaire` objects can also be used directly after discovery.

---

## File Structure

```
Telelumen-Wrapper/
├── api/
│   └── telelumen_api.py       # This API
├── docs/
│   ├── CLEAN_API_DOCUMENTATION.md        # This file
│   └── TELELUMEN_WRAPPER_DOCUMENTATION.md
├── examples/
│   ├── blink.py
│   ├── day_simulation.py
│   ├── light_off.py
│   └── light_on.py
├── telelumen_wrapper_clean.py # Wrapper using this API
├── requirements.txt
└── README.md
```

### Import

```python
from api.telelumen_api import TelelumenAPI, Luminaire, LuminaireType, APIConfig
```

---

## Configuration — `APIConfig`

`APIConfig` is a `@dataclass` that centralises every tunable parameter. Pass an instance to `Discovery.discover()` or `TelelumenAPI.configure()` when non-default values are needed.

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `DEFAULT_PORT` | `int` | `57007` | Main telnet port |
| `DISCONNECT_PORT` | `int` | `57011` | Wake/ARP port (Pass 1 of discovery) |
| `UDP_PORT` | `int` | `57000` | UDP port (reserved) |
| `CONNECTION_TIMEOUT` | `float` | `10.0` | Telnet connection timeout (seconds) |
| `COMMAND_TIMEOUT` | `float` | `5.0` | Per-command read timeout (seconds) |
| `DISCOVERY_TIMEOUT` | `float` | `30.0` | Maximum total discovery time (seconds) |
| `MAX_RETRIES` | `int` | `3` | Command retry count |
| `RETRY_DELAY` | `float` | `0.5` | Delay between retries (seconds) |
| `DISCOVERY_NETWORKS` | `List[str]` | See below | Networks to scan |
| `SCAN_START_IP` | `int` | `2` | First host octet to probe |
| `SCAN_END_IP` | `int` | `254` | Last host octet to probe (exclusive) |
| `FILE_BLOCK_SIZE` | `int` | `512` | File transfer block size (bytes) |
| `MAX_FILE_RETRIES` | `int` | `10` | File transfer retry count |
| `VERBOSE` | `bool` | `True` | Enable `[INFO]` / `[SUCCESS]` logging |
| `DEBUG` | `bool` | `False` | Enable `[DEBUG]` logging |

**Default `DISCOVERY_NETWORKS`:**
```
192.168.0.  192.168.1.  192.168.2.  192.168.3.
192.168.4.  192.168.5.  192.168.6.  192.168.7.
192.168.8.  192.168.9.  192.168.10. 192.168.11.
```

### Example

```python
from api.telelumen_api import APIConfig, TelelumenAPI

TelelumenAPI.configure(
    verbose=True,
    discovery_networks=['192.168.1.', '192.168.2.']
)
```

---

## Enumerations

### `LuminaireType`

Auto-detected after connection by sending the `ID` command.

| Value | String | Description |
|---|---|---|
| `LuminaireType.OCTA` | `"Octa"` | Octa luminaire (8-channel) |
| `LuminaireType.PENTA` | `"Penta"` | Penta luminaire (8-channel) |
| `LuminaireType.LIGHT_REPLICATOR` | `"LightReplicator"` | Light Replicator (24-channel) |
| `LuminaireType.UNKNOWN` | `"Unknown"` | Detection failed |

### `ConnectionState`

Internal state tracked by `LuminaireConnection`.

| Value | Description |
|---|---|
| `DISCONNECTED` | No active connection |
| `CONNECTING` | Handshake in progress |
| `CONNECTED` | Ready to send commands |
| `ERROR` | Connection failed |

---

## Exceptions

All exceptions inherit from `TelelumenError`.

| Exception | Raised when |
|---|---|
| `TelelumenError` | Base class |
| `ConnectionError` | TCP connection fails or is refused |
| `CommandError` | Command send/receive fails or times out |
| `DiscoveryError` | Discovery-level failure |
| `FileTransferError` | File upload/download fails |

```python
from api.telelumen_api import TelelumenAPI, ConnectionError, CommandError

try:
    lum = TelelumenAPI.connect("192.168.1.100")
except ConnectionError as e:
    print(f"Could not connect: {e}")
```

---

## Logger

`Logger` is a simple class-level logger. Output is prefixed by severity.

| Method | Prefix | Controlled by |
|---|---|---|
| `Logger.info(msg)` | `[INFO]` | `Logger.verbose` |
| `Logger.debug(msg)` | `[DEBUG]` | `Logger.debug` |
| `Logger.warning(msg)` | `[WARNING]` | `Logger.verbose` |
| `Logger.success(msg)` | `[SUCCESS]` | `Logger.verbose` |
| `Logger.error(msg)` | `[ERROR]` | always printed |

Configure via `TelelumenAPI.configure()` — do not set `Logger.verbose` directly.

---

## LuminaireConnection

Low-level telnet wrapper. You normally do **not** need to use this class directly — `Luminaire` and `Discovery` manage it internally.

### Constructor

```python
LuminaireConnection(ip_address: str, port: int, timeout: float)
```

### Methods

#### `connect() -> bool`
Opens the telnet connection. Raises `ConnectionError` on failure. Thread-safe (internal `threading.Lock`).

#### `disconnect() -> bool`
Closes the connection. Returns `True` on success.

#### `send_command(command: str, wait_for_response: bool = True) -> Optional[str]`
Sends `command\r` and reads until the `;` terminator. Returns raw response string.  
Raises `CommandError` on timeout or socket error.

#### `is_connected() -> bool`
Returns `True` if state is `CONNECTED` and the telnet object is alive.

---

## Luminaire

Represents one physical luminaire. Created by `Discovery.discover()` or `TelelumenAPI.connect()`.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `ip_address` | `str` | IP address |
| `luminaire_type` | `LuminaireType` | Detected device type |
| `serial_number` | `Optional[str]` | Luminaire serial number (`GETSERNO`) |
| `electronic_serial` | `Optional[str]` | Electronic serial (`NS`) |
| `firmware_version` | `Optional[str]` | Firmware version (`VER`) |
| `mac_address` | `Optional[str]` | MAC address (`GETIP`) |
| `last_command_status` | `int` | Status code of the last command |
| `connection` | `Optional[LuminaireConnection]` | Active connection |
| `config` | `APIConfig` | Configuration used |

### Connection Methods

#### `connect() -> bool`
Creates a `LuminaireConnection` to `DEFAULT_PORT` and calls `_initialize_device_info()`.

#### `disconnect() -> bool`
Closes the connection.

### Device Info Methods

After connection, device info is initialised automatically by `_initialize_device_info()`. Each command (`VER`, `NS`, `ID`, `GETSERNO`) is executed in its own independent `try/except` — a failure on one does not prevent the others from running.

#### `get_temperature() -> Optional[float]`
Returns temperature in °C, or `None` if unsupported (Light Replicator) or on error.

```python
temp = lum.get_temperature()
if temp is not None:
    print(f"{temp}°C")
```

#### `get_mac_address() -> Optional[str]`
Returns MAC address string from `GETIP` response.

### Drive Level Control

Channel values are always normalised floats in `[0.0, 1.0]`.

#### `get_drive_levels() -> List[float]`
Returns current drive levels for all channels.

- **Octa/Penta:** reads 16-bit hex values via `PS?`, divides by 65535
- **Light Replicator:** reads PWM/AM pairs via `PS?`, converts to intensity

#### `set_drive_levels(levels: List[float]) -> bool`
Sets all channels at once.

- **Octa/Penta:** sends `PS` + 16-bit hex values
- **Light Replicator:** sends `PA` + PWM/AM hex pairs

```python
# Set 8 channels for Octa at 50%
lum.set_drive_levels([0.5] * 8)

# Per-channel control for a 24-channel Light Replicator
levels = [0.0] * 24
levels[6] = 0.8   # Channel 6 (Blue-Cyan) at 80%
lum.set_drive_levels(levels)
```

#### `set_drive_level(channel: int, level: float) -> bool`
Sets a single channel (0-based index).

- **Octa/Penta:** sends `P{channel:02d}{value:04X}`
- **Light Replicator:** sends `PC{channel:02d}{pwm:04X}{am:02X}`

### Lighting Control

#### `go_dark() -> bool`
Turns off all LEDs immediately.
- Octa/Penta: sends `DARK`
- Light Replicator: sends `B`

#### `reset() -> bool`
Reboots the luminaire firmware (`RESET` command).

### Script Playback

#### `play_script(filename: str, wait: bool = False) -> bool`
Plays a script file stored on the luminaire.

| Device | Command sent |
|---|---|
| Light Replicator | `SETPAT=<filename>` |
| Octa/Penta (immediate) | `PLAY <filename>` |
| Octa/Penta (paused) | `PLAYPAUSED <filename>` |

```python
lum.play_script("sunset.lsp")
lum.play_script("sunrise.lsp", wait=True)  # Load but don't start
lum.resume()                                # Start manually
```

#### `pause() -> bool`
Pauses current script (`PAUSE` / `Q5` for LR).

#### `resume() -> bool`
Resumes a paused script (`RESUME` / `Q2` for LR).

#### `stop() -> bool`
Stops script playback (`STOP` / `Q8` + `go_dark()` for LR).

### File Management

#### `get_directory() -> List[str]`
Returns a list of filenames stored on the luminaire.

```python
files = lum.get_directory()
for f in files:
    print(f)
```

### String Representation

```python
print(lum)
# Luminaire(ip=192.168.1.42, type=Octa, serial=TL-2021-001)
```

---

## Discovery

`Discovery` handles finding luminaires on the network. Its algorithm is a faithful port of `api_tng.__discover_all()` / `__discover_one()`.

### How It Works

Discovery runs two sequential passes per network, each scanning IPs 2–253 in parallel (one thread per IP, matching the original `api_tng` behaviour):

```
For each network prefix (e.g. "192.168.1."):
  Pass 1 — Port 57011 (DISCONNECT_PORT)
      → 252 threads probe every IP
      → Forces ARP table population, wakes the luminaire network stack
      → Connections are expected to be refused or time out (side-effect is what matters)

  Pass 2 — Port 57007 (DEFAULT_PORT)
      → 252 threads probe every IP again
      → Thread sends 'NS', checks for valid serial number response
      → Valid luminaires: kept open in _telnet_connections
      → Invalid IPs: connection closed immediately

  If any luminaires found on this network → stop, return results
  Otherwise → move to next network
```

After both passes, live telnet connections are **reused** directly by wrapping them into `LuminaireConnection` objects — no second TCP handshake is needed.

### Thread Safety

Shared state (`_luminaire_list`, `_telnet_connections`, `_refused_list`) is protected by `Discovery._lock` (`threading.Lock`). Each thread acquires the lock only for the brief list update — actual network I/O runs in parallel.

### Public Method

#### `Discovery.discover(networks=None, config=None) -> List[Luminaire]`

```python
luminaires = Discovery.discover()
luminaires = Discovery.discover(networks=['192.168.1.'])
```

Returns a list of fully connected and initialised `Luminaire` objects.

### Internal Methods (not for direct use)

| Method | Mirrors | Purpose |
|---|---|---|
| `_open_connection(ip, port)` | `openConnection()` | Raw telnet connect |
| `_open_luminaire(ip, port)` | `openLuminaire()` | Connect wrapper |
| `_get_reply(ip)` | `getReply()` | Read until `;` |
| `_send_message(ip, msg)` | `sendMessage()` | Write + read reply |
| `_close_connection(ip)` | `closeLuminaire()` | Close and discard |
| `_get_serial_number(ip)` | `__get_serial_number()` | Send `NS`, return reply |
| `_add_luminaire(ip)` | `addLuminaire()` | Thread-safe list append |
| `_remove_luminaire(ip)` | `removeLuminaire()` | Thread-safe list remove |
| `_discovery_poll(addr, port)` | `__discoveryPoll()` | Per-thread probe |
| `_is_alive(tasks)` | `is_alive()` | Check if any thread running |
| `_discover_one(net, port)` | `__discover_one()` | Full threaded scan of one network/port |
| `_discover_all(networks, config)` | `__discover_all()` | Two-pass scan across all networks |

---

## TelelumenAPI

Static facade class — the recommended entry point for all user code. Manages a registry of active connections (`_connections` dict).

### Configuration

#### `TelelumenAPI.configure(verbose, debug, connection_timeout, discovery_networks)`

```python
TelelumenAPI.configure(
    verbose=True,
    debug=False,
    connection_timeout=10.0,
    discovery_networks=['192.168.1.', '192.168.2.']
)
```

All parameters are optional — only provided ones are updated.

### Discovery & Connection

#### `TelelumenAPI.discover(networks=None) -> List[Luminaire]`

Discovers all luminaires on the network. Delegates to `Discovery.discover()`.

```python
luminaires = TelelumenAPI.discover()
luminaires = TelelumenAPI.discover(networks=['192.168.1.'])
```

#### `TelelumenAPI.connect(ip_address: str) -> Luminaire`

Direct connection by IP, skipping discovery. Returns a cached connection if already connected.

```python
lum = TelelumenAPI.connect("192.168.1.42")
```

Raises `ConnectionError` on failure.

#### `TelelumenAPI.disconnect(luminaire: Luminaire) -> bool`

Closes the connection and removes it from the internal registry.

```python
TelelumenAPI.disconnect(lum)
```

#### `TelelumenAPI.disconnect_all() -> int`

Disconnects from all registered luminaires. Returns the count disconnected.

```python
count = TelelumenAPI.disconnect_all()
print(f"Disconnected {count} luminaire(s)")
```

### Convenience Methods

#### `TelelumenAPI.light_on(luminaire, brightness=1.0) -> bool`

Sets all channels to `brightness`. Equivalent to `set_brightness`.

```python
TelelumenAPI.light_on(lum)            # Full brightness
TelelumenAPI.light_on(lum, 0.5)      # 50%
```

#### `TelelumenAPI.light_off(luminaire) -> bool`

Calls `luminaire.go_dark()`.

```python
TelelumenAPI.light_off(lum)
```

#### `TelelumenAPI.set_brightness(luminaire, brightness) -> bool`

Reads current channel count, then calls `set_drive_levels([brightness] * n)`.  
Falls back to 24 channels (Octa/Penta) or 32 channels (Light Replicator) if `get_drive_levels()` fails.

```python
TelelumenAPI.set_brightness(lum, 0.75)
```

#### `TelelumenAPI.get_info(luminaire) -> Dict[str, any]`

Returns a dictionary of all available device information:

```python
info = TelelumenAPI.get_info(lum)
# {
#   'ip_address':        '192.168.1.42',
#   'serial_number':     'TL-2021-001',
#   'electronic_serial': '0x...',
#   'firmware_version':  '4.12',
#   'luminaire_type':    'Octa',
#   'mac_address':       'AA:BB:CC:DD:EE:FF',
#   'temperature':       38.5,
#   'connected':         True
# }
```

---

## Quick Start

```python
from api.telelumen_api import TelelumenAPI

# 1. (Optional) configure before discovery
TelelumenAPI.configure(verbose=True)

# 2. Discover all luminaires on the LAN
luminaires = TelelumenAPI.discover()

if not luminaires:
    print("No luminaires found.")
    exit()

# 3. Work with the first one
lum = luminaires[0]
print(lum)  # Luminaire(ip=192.168.1.42, type=Octa, serial=TL-2021-001)

# 4. Control
TelelumenAPI.light_on(lum, brightness=0.8)

import time
time.sleep(2)

TelelumenAPI.light_off(lum)

# 5. Disconnect
TelelumenAPI.disconnect_all()
```

---

## Usage Examples

### Connect directly by IP

```python
from api.telelumen_api import TelelumenAPI

lum = TelelumenAPI.connect("192.168.1.42")
TelelumenAPI.light_on(lum, brightness=0.5)
TelelumenAPI.disconnect(lum)
```

### Per-channel colour control

```python
from api.telelumen_api import TelelumenAPI

luminaires = TelelumenAPI.discover()
lum = luminaires[0]

# Warm white for Octa (8 channels: RB, B, Cy, G, Lime, Amber, Orange, Red)
lum.set_drive_levels([0.0, 0.0, 0.0, 0.1, 0.0, 0.6, 0.5, 0.4])

import time; time.sleep(3)

# Cool blue for night simulation
lum.set_drive_levels([0.06, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0])

time.sleep(3)
TelelumenAPI.light_off(lum)
TelelumenAPI.disconnect_all()
```

### Multi-luminaire control

```python
from api.telelumen_api import TelelumenAPI
import time

luminaires = TelelumenAPI.discover()
print(f"Found {len(luminaires)} luminaire(s)")

for lum in luminaires:
    TelelumenAPI.light_on(lum, brightness=0.7)

time.sleep(5)

for lum in luminaires:
    TelelumenAPI.light_off(lum)

TelelumenAPI.disconnect_all()
```

### Script playback

```python
from api.telelumen_api import TelelumenAPI
import time

lum = TelelumenAPI.connect("192.168.1.42")

lum.play_script("sunrise.lsp")
time.sleep(60)

lum.stop()
TelelumenAPI.disconnect(lum)
```

### Temperature monitoring

```python
from api.telelumen_api import TelelumenAPI, LuminaireType
import time

lum = TelelumenAPI.connect("192.168.1.42")
TelelumenAPI.light_on(lum, brightness=1.0)

for _ in range(12):
    temp = lum.get_temperature()
    if temp is not None:
        print(f"Temperature: {temp:.1f}°C")
        if temp > 65.0:
            print("Warning: overheating — reducing brightness")
            TelelumenAPI.set_brightness(lum, 0.5)
    time.sleep(5)

TelelumenAPI.light_off(lum)
TelelumenAPI.disconnect(lum)
```

### Restrict discovery to one network

```python
from api.telelumen_api import TelelumenAPI

TelelumenAPI.configure(discovery_networks=['192.168.1.'])
luminaires = TelelumenAPI.discover()
```

---

## Discovery Internals

### Two-Pass Algorithm (identical to `api_tng`)

```
_discover_all(networks, config)
    for each net in networks:
        _discover_one(net, port=57011)    # Pass 1 — ARP wake
        lumlist = _discover_one(net, port=57007)  # Pass 2 — real scan
        if lumlist: return lumlist
    return []

_discover_one(net, port)
    reset internal state
    create 252 threads (one per IP 2..253): target = _discovery_poll(i, port)
    start all threads
    while _is_alive(threads): sleep(1.0)
    return sorted _luminaire_list

_discovery_poll(address, port)
    ip = _luminaire_network + str(address)
    if _open_luminaire(ip, port):
        sn = _get_serial_number(ip)   # sends 'NS'
        if sn: _add_luminaire(ip), keep connection open
        else:  _remove_luminaire(ip), _close_connection(ip)
    else:
        _remove_luminaire(ip)  (connection was never opened)
```

### Connection Reuse

After Pass 2, valid luminaire connections remain open in `Discovery._telnet_connections`. The public `discover()` method wraps each raw `telnetlib.Telnet` object directly into a `LuminaireConnection(state=CONNECTED)` — avoiding a redundant TCP handshake.

### Timeout Reference

| Setting | Value | Applies to |
|---|---|---|
| `Discovery.TELNET_CONNECTION_TIMEOUT` | `6.0 s` | Each probed IP (Pass 1 & 2) |
| `APIConfig.CONNECTION_TIMEOUT` | `10.0 s` | `Luminaire.connect()` direct connect |
| `APIConfig.COMMAND_TIMEOUT` | `5.0 s` | `send_command()` read timeout |

---

## Comparison with `api_tng`

| Feature | `api_tng.py` | `telelumen_api.py` |
|---|---|---|
| API style | Module-level functions | Classes + static methods |
| Discovery | `__discover_all()` → IP list | `Discovery.discover()` → `Luminaire` objects |
| Discovery algorithm | Two-pass threaded | Two-pass threaded (same) |
| Connection reuse | No (connection lost after discovery) | Yes (telnet objects reused) |
| Type hints | None | Full (`Optional`, `List`, `Dict`, `Tuple`) |
| Error handling | `try/except` with silent returns | Typed exceptions |
| Device info init | Single `try/except` (stops on first failure) | Independent `try/except` per command |
| Luminaire type | String `lumtype` attribute | `LuminaireType` enum |
| Thread safety | Global mutable state, no locks | `threading.Lock` on shared state |

### Equivalent operations

```python
# --- api_tng ---
import old.api_tng as api

luminaires = api.discover()     # returns IP strings
lum = luminaires[0]
api.openLuminaire(lum.address, api.luminairePort)
lum.go_dark()
api.closeLuminaire(lum.address)

# --- telelumen_api ---
from api.telelumen_api import TelelumenAPI

luminaires = TelelumenAPI.discover()   # returns Luminaire objects
lum = luminaires[0]
TelelumenAPI.light_off(lum)
TelelumenAPI.disconnect(lum)
```

---

## Module Exports (`__all__`)

```python
from api.telelumen_api import (
    TelelumenAPI,
    Luminaire,
    LuminaireType,
    APIConfig,
    TelelumenError,
    ConnectionError,
    CommandError,
    DiscoveryError,
    FileTransferError,
    Logger
)
```

---

**Last Updated:** February 25, 2026  
**Version:** 2.0
