# Telelumen Clean API Documentation

## Overview

This is a complete rewrite of the Telelumen API with clean code architecture, proper error handling, and modern Python practices. It replaces the complex `api_tng.py` with a maintainable, readable solution.

**Version:** 2.0 (Clean Architecture)  
**Created:** February 4, 2026  
**Author:** Théo Poujol

---

## Why a Rewrite?

### Problems with Original API

1. **Poor Code Structure**
   - Global variables everywhere
   - Mixed concerns (connection, discovery, commands all tangled)
   - Hard-coded values scattered throughout

2. **Error Handling Issues**
   - Excessive exception catching with no useful messages
   - Silent failures
   - Non-verbose error reporting

3. **Maintainability**
   - Complex telnet connection management
   - Difficult to debug
   - Hard to extend or modify

4. **Usability**
   - Inconsistent interface
   - Unclear function purposes
   - No clear separation between low-level and high-level operations

### New Clean API Benefits

✅ **Clean Architecture** - Proper separation of concerns  
✅ **Static Class Interface** - Easy to use, no instantiation needed  
✅ **Meaningful Errors** - Clear, actionable error messages  
✅ **Type Hints** - Better IDE support and code clarity  
✅ **Configuration-Based** - No hard-coded values  
✅ **Thread-Safe** - Proper locking for concurrent operations  
✅ **Extensible** - Easy to add new features  
✅ **Well-Documented** - Clear docstrings and examples

---

## Architecture

### Class Structure

```
TelelumenAPI (Main Static Interface)
│
├── APIConfig (Configuration)
├── Logger (Logging System)
├── Discovery (Network Discovery)
├── LuminaireConnection (Connection Management)
└── Luminaire (Device Representation)
```

### Design Principles

1. **Single Responsibility** - Each class has one clear purpose
2. **Static Interface** - Main API is static for simplicity
3. **Encapsulation** - Connection details hidden from users
4. **Configuration** - Centralized settings management
5. **Error Transparency** - Clear exceptions with context

---

## Quick Start

### Basic Usage

```python
from telelumen_api import TelelumenAPI

# Configure (optional)
TelelumenAPI.configure(verbose=True, debug=False)

# Discover luminaires
luminaires = TelelumenAPI.discover()

if luminaires:
    lum = luminaires[0]
    
    # Turn on at 75% brightness
    TelelumenAPI.light_on(lum, brightness=0.75)
    
    # Get temperature
    temp = lum.get_temperature()
    print(f"Temperature: {temp}°C")
    
    # Turn off
    TelelumenAPI.light_off(lum)
    
    # Disconnect
    TelelumenAPI.disconnect(lum)
```

### Using the Wrapper

```python
from telelumen_wrapper_clean import Telelumen

# Interactive connection
lum = Telelumen.connect_from_list()

if lum:
    # Simple control
    Telelumen.light_on(lum, brightness=0.5)
    Telelumen.light_off(lum)
    Telelumen.disconnect(lum)
```

---

## API Reference

### TelelumenAPI Class

The main static interface for all operations.

#### Configuration

##### `configure(verbose=None, debug=None, connection_timeout=None, discovery_networks=None)`

Configure API settings.

**Parameters:**
- `verbose` (bool): Enable/disable verbose logging
- `debug` (bool): Enable/disable debug logging
- `connection_timeout` (float): Connection timeout in seconds
- `discovery_networks` (List[str]): Networks to search

**Example:**
```python
TelelumenAPI.configure(
    verbose=True,
    debug=False,
    connection_timeout=15.0,
    discovery_networks=['192.168.1.', '192.168.2.']
)
```

#### Discovery & Connection

##### `discover(networks=None) -> List[Luminaire]`

Discover all luminaires on the network.

**Parameters:**
- `networks` (List[str], optional): Networks to search

**Returns:**
- List of Luminaire objects

**Example:**
```python
# Search all default networks
luminaires = TelelumenAPI.discover()

# Search specific networks
luminaires = TelelumenAPI.discover(['192.168.1.'])

for lum in luminaires:
    print(f"{lum.ip_address}: {lum.serial_number}")
```

##### `connect(ip_address) -> Luminaire`

Connect to a luminaire by IP address.

**Parameters:**
- `ip_address` (str): IP address

**Returns:**
- Connected Luminaire object

**Raises:**
- `ConnectionError`: If connection fails

**Example:**
```python
try:
    lum = TelelumenAPI.connect('192.168.1.100')
    print(f"Connected to {lum.serial_number}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

##### `disconnect(luminaire) -> bool`

Disconnect from a luminaire.

**Parameters:**
- `luminaire` (Luminaire): Luminaire to disconnect

**Returns:**
- True if successful

**Example:**
```python
TelelumenAPI.disconnect(lum)
```

##### `disconnect_all() -> int`

Disconnect from all connected luminaires.

**Returns:**
- Number of luminaires disconnected

**Example:**
```python
count = TelelumenAPI.disconnect_all()
print(f"Disconnected from {count} luminaire(s)")
```

#### Lighting Control

##### `light_on(luminaire, brightness=1.0) -> bool`

Turn on luminaire at specified brightness.

**Parameters:**
- `luminaire` (Luminaire): Target luminaire
- `brightness` (float): Brightness (0.0 to 1.0)

**Returns:**
- True if successful

**Example:**
```python
TelelumenAPI.light_on(lum, brightness=0.8)
```

##### `light_off(luminaire) -> bool`

Turn off luminaire.

**Parameters:**
- `luminaire` (Luminaire): Target luminaire

**Returns:**
- True if successful

**Example:**
```python
TelelumenAPI.light_off(lum)
```

##### `set_brightness(luminaire, brightness) -> bool`

Set brightness for all channels.

**Parameters:**
- `luminaire` (Luminaire): Target luminaire
- `brightness` (float): Brightness (0.0 to 1.0)

**Returns:**
- True if successful

**Example:**
```python
# Fade from bright to dark
for i in range(10, -1, -1):
    brightness = i / 10.0
    TelelumenAPI.set_brightness(lum, brightness)
    time.sleep(0.2)
```

#### Information

##### `get_info(luminaire) -> Dict`

Get comprehensive information about a luminaire.

**Parameters:**
- `luminaire` (Luminaire): Target luminaire

**Returns:**
- Dictionary with device information

**Example:**
```python
info = TelelumenAPI.get_info(lum)
print(f"IP: {info['ip_address']}")
print(f"Type: {info['luminaire_type']}")
print(f"Serial: {info['serial_number']}")
print(f"Firmware: {info['firmware_version']}")
print(f"Temperature: {info['temperature']}°C")
```

---

### Luminaire Class

Represents a single luminaire device.

#### Properties

- `ip_address` (str): IP address
- `serial_number` (str): Luminaire serial number
- `electronic_serial` (str): Electronic serial number
- `firmware_version` (str): Firmware version
- `luminaire_type` (LuminaireType): Device type enum
- `mac_address` (str): MAC address
- `last_command_status` (int): Last command status code

#### Connection Methods

##### `connect() -> bool`

Connect to the luminaire.

**Returns:**
- True if successful

**Raises:**
- `ConnectionError`: If connection fails

```python
lum = Luminaire('192.168.1.100')
lum.connect()
```

##### `disconnect() -> bool`

Disconnect from the luminaire.

```python
lum.disconnect()
```

#### Drive Level Methods

##### `get_drive_levels() -> List[float]`

Get normalized drive levels (0.0 to 1.0) for all channels.

**Returns:**
- List of drive level values

```python
levels = lum.get_drive_levels()
print(f"Channel 0: {levels[0]*100}%")
```

##### `set_drive_levels(levels) -> bool`

Set drive levels for all channels.

**Parameters:**
- `levels` (List[float]): List of values (0.0 to 1.0)

**Returns:**
- True if successful

```python
# Set custom levels
levels = [0.8, 0.6, 0.4, 0.2, 0.0, 0.0, 0.0, 0.0]
lum.set_drive_levels(levels)
```

##### `set_drive_level(channel, level) -> bool`

Set drive level for a single channel.

**Parameters:**
- `channel` (int): Channel number (0-based)
- `level` (float): Value (0.0 to 1.0)

**Returns:**
- True if successful

```python
# Set channel 3 to 60%
lum.set_drive_level(3, 0.6)
```

#### Control Methods

##### `go_dark() -> bool`

Turn off all LEDs.

```python
lum.go_dark()
```

##### `reset() -> bool`

Reset (reboot) the luminaire.

```python
lum.reset()
```

#### Temperature

##### `get_temperature() -> Optional[float]`

Get luminaire temperature in Celsius.

**Returns:**
- Temperature or None if not supported

```python
temp = lum.get_temperature()
if temp:
    print(f"Temperature: {temp}°C")
    if temp > 65:
        print("Warning: High temperature!")
```

#### Script Playback

##### `play_script(filename, wait=False) -> bool`

Play a script file.

**Parameters:**
- `filename` (str): Script filename
- `wait` (bool): Load but wait for resume()

**Returns:**
- True if successful

```python
# Play immediately
lum.play_script('sunset.lsp')

# Load and wait
lum.play_script('sunrise.lsp', wait=True)
lum.resume()
```

##### `pause() -> bool`

Pause script playback.

```python
lum.pause()
```

##### `resume() -> bool`

Resume script playback.

```python
lum.resume()
```

##### `stop() -> bool`

Stop script playback.

```python
lum.stop()
```

#### File Management

##### `get_directory() -> List[str]`

Get list of files on luminaire.

**Returns:**
- List of filenames

```python
files = lum.get_directory()
for filename in files:
    print(f"  - {filename}")
```

---

### APIConfig Class

Centralized configuration.

#### Properties

```python
@dataclass
class APIConfig:
    # Network
    DEFAULT_PORT: int = 57007
    DISCONNECT_PORT: int = 57011
    UDP_PORT: int = 57000
    
    # Timeouts
    CONNECTION_TIMEOUT: float = 10.0
    COMMAND_TIMEOUT: float = 5.0
    DISCOVERY_TIMEOUT: float = 30.0
    
    # Retries
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 0.5
    
    # Discovery
    DISCOVERY_NETWORKS: List[str] = [...]
    SCAN_START_IP: int = 2
    SCAN_END_IP: int = 254
    
    # File transfer
    FILE_BLOCK_SIZE: int = 512
    MAX_FILE_RETRIES: int = 10
    
    # Logging
    VERBOSE: bool = True
    DEBUG: bool = False
```

#### Usage

```python
from telelumen_api import APIConfig

# Create custom config
config = APIConfig()
config.CONNECTION_TIMEOUT = 20.0
config.VERBOSE = False

# Use with API
TelelumenAPI._config = config
```

---

### Logger Class

Simple logging system.

#### Methods

```python
Logger.info("Information message")
Logger.debug("Debug message")  # Only if debug=True
Logger.warning("Warning message")
Logger.error("Error message")
Logger.success("Success message")
```

#### Configuration

```python
Logger.verbose = True  # Enable/disable verbose
Logger.debug = True    # Enable/disable debug
```

---

### Enumerations

#### LuminaireType

```python
class LuminaireType(Enum):
    OCTA = "Octa"
    PENTA = "Penta"
    LIGHT_REPLICATOR = "LightReplicator"
    UNKNOWN = "Unknown"
```

#### ConnectionState

```python
class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
```

---

### Exceptions

All exceptions inherit from `TelelumenError`.

#### Exception Hierarchy

```
TelelumenError
├── ConnectionError
├── CommandError
├── DiscoveryError
└── FileTransferError
```

#### Usage

```python
from telelumen_api import ConnectionError, CommandError

try:
    lum = TelelumenAPI.connect('192.168.1.100')
except ConnectionError as e:
    print(f"Connection failed: {e}")

try:
    lum.set_drive_levels([0.5] * 24)
except CommandError as e:
    print(f"Command failed: {e}")
```

---

## Complete Examples

### Example 1: Multi-Luminaire Control

```python
from telelumen_api import TelelumenAPI
import time

# Configure
TelelumenAPI.configure(verbose=True)

# Discover
luminaires = TelelumenAPI.discover()

if not luminaires:
    print("No luminaires found!")
    exit(1)

print(f"\nFound {len(luminaires)} luminaire(s)")

# Control all luminaires
for lum in luminaires:
    print(f"\nControlling {lum.ip_address}...")
    
    # Turn on at 80%
    TelelumenAPI.light_on(lum, brightness=0.8)

time.sleep(3)

# Fade all luminaires
for brightness in range(10, -1, -1):
    level = brightness / 10.0
    for lum in luminaires:
        TelelumenAPI.set_brightness(lum, level)
    time.sleep(0.2)

# Disconnect all
count = TelelumenAPI.disconnect_all()
print(f"\nDisconnected from {count} luminaire(s)")
```

### Example 2: Temperature Monitoring

```python
from telelumen_api import TelelumenAPI
import time

lum = TelelumenAPI.connect('192.168.1.100')

print("Monitoring temperature for 60 seconds...")

for i in range(12):
    temp = lum.get_temperature()
    
    if temp:
        print(f"[{i*5}s] Temperature: {temp}°C")
        
        # Auto-adjust brightness based on temperature
        if temp > 65:
            print("  High temperature - reducing brightness")
            TelelumenAPI.set_brightness(lum, 0.5)
        elif temp < 50:
            print("  Normal temperature - full brightness OK")
            TelelumenAPI.set_brightness(lum, 1.0)
    
    time.sleep(5)

TelelumenAPI.disconnect(lum)
```

### Example 3: Channel Color Mixing

```python
from telelumen_api import TelelumenAPI
import time

lum = TelelumenAPI.connect('192.168.1.100')

# Define color presets (24 channels)
warm_white = [0.0]*4 + [0.3, 0.3, 0.2, 0.2] + [0.4] + [0.5, 0.5] + [0.0] + [0.8, 0.9, 0.7, 0.8, 0.8] + [0.0]*7
cool_white = [0.0]*4 + [0.8, 0.8, 0.9, 0.9] + [0.6] + [0.5, 0.5] + [0.3] + [0.2, 0.0, 0.0, 0.0, 0.0] + [0.0]*7
daylight  = [0.0]*4 + [0.5, 0.5, 0.6, 0.6] + [0.4] + [0.7, 0.7] + [0.3] + [0.4, 0.2, 0.1, 0.0, 0.0] + [0.0]*7

presets = [
    ("Warm White", warm_white),
    ("Cool White", cool_white),
    ("Daylight", daylight)
]

for name, levels in presets:
    print(f"Setting {name}...")
    lum.set_drive_levels(levels)
    time.sleep(3)

lum.go_dark()
TelelumenAPI.disconnect(lum)
```

### Example 4: Error Handling

```python
from telelumen_api import TelelumenAPI, ConnectionError, CommandError

def safe_control(ip_address: str):
    """Example with comprehensive error handling."""
    
    luminaire = None
    
    try:
        # Try to connect
        print(f"Connecting to {ip_address}...")
        luminaire = TelelumenAPI.connect(ip_address)
        print("Connected!")
        
        # Try to turn on
        if TelelumenAPI.light_on(luminaire, brightness=0.7):
            print("Light turned on at 70%")
        else:
            print("Failed to turn on light")
        
        # Try to get temperature
        temp = luminaire.get_temperature()
        if temp is not None:
            print(f"Temperature: {temp}°C")
        else:
            print("Temperature reading not available")
        
        # Try to turn off
        if TelelumenAPI.light_off(luminaire):
            print("Light turned off")
        
    except ConnectionError as e:
        print(f"Connection error: {e}")
        print("Possible causes:")
        print("  - Luminaire is offline")
        print("  - Wrong IP address")
        print("  - Network issues")
        print("  - Another application is connected")
    
    except CommandError as e:
        print(f"Command error: {e}")
        print("The luminaire is not responding to commands")
    
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    finally:
        # Always disconnect
        if luminaire:
            print("Disconnecting...")
            TelelumenAPI.disconnect(luminaire)

# Use it
safe_control('192.168.1.100')
```

---

## Migration Guide

### From Old API to New API

#### Old Way (api_tng.py)

```python
import api.api_tng as api

# Discover
luminaires = api.discover()
lum = luminaires[0]

# Connect
api.openLuminaire(lum.address, api.luminairePort)

# Control
num_channels = 24
levels = [0.5] * num_channels
lum.set_drive_levels(levels)

# Disconnect
api.closeLuminaire(lum.address)
```

#### New Way (telelumen_api.py)

```python
from telelumen_api import TelelumenAPI

# Discover (automatically connected)
luminaires = TelelumenAPI.discover()
lum = luminaires[0]

# Control (simplified)
TelelumenAPI.set_brightness(lum, 0.5)

# Disconnect
TelelumenAPI.disconnect(lum)
```

### Using the Wrapper

#### Old Wrapper

```python
from telelumen_wrapper import Telelumen

lum = Telelumen.connect_from_list()
Telelumen.light_on(lum, brightness=0.5)
Telelumen.disconnect(lum)
```

#### New Wrapper (Backward Compatible)

```python
from telelumen_wrapper_clean import Telelumen

lum = Telelumen.connect_from_list()  # Same interface!
Telelumen.light_on(lum, brightness=0.5)
Telelumen.disconnect(lum)
```

---

## Advantages Over Old API

### 1. Clear Error Messages

**Old API:**
```
ERROR: api_tng.openConnection(): Connection refused
```

**New API:**
```
[ERROR] Connection refused by 192.168.1.100:57007. 
Device may be busy or not responding.
```

### 2. Simplified Connection

**Old API:**
```python
ip_list = api.discover()
lum = ip_list[0]
result = api.openLuminaire(lum.address, api.luminairePort)
if result == 0:
    # Do stuff
    api.closeLuminaire(lum.address)
```

**New API:**
```python
luminaires = TelelumenAPI.discover()  # Already connected!
lum = luminaires[0]
# Do stuff
TelelumenAPI.disconnect(lum)
```

### 3. Type Safety

**Old API:**
```python
def some_function(lum):  # What is lum?
    pass
```

**New API:**
```python
def some_function(lum: Luminaire) -> bool:  # Clear types!
    pass
```

### 4. Configuration

**Old API:**
```python
# Hardcoded everywhere
TELNET_CONNECTION_TIMEOUT = 6.0
luminairePort = 57007
# etc...
```

**New API:**
```python
# Centralized configuration
TelelumenAPI.configure(
    connection_timeout=10.0,
    discovery_networks=['192.168.1.']
)
```

---

## Best Practices

### 1. Always Use try-except

```python
try:
    lum = TelelumenAPI.connect(ip)
    # Do work
except ConnectionError as e:
    print(f"Failed: {e}")
finally:
    if lum:
        TelelumenAPI.disconnect(lum)
```

### 2. Configure Once at Start

```python
# At the top of your script
TelelumenAPI.configure(
    verbose=True,
    connection_timeout=15.0
)

# Then use throughout
luminaires = TelelumenAPI.discover()
```

### 3. Check Return Values

```python
if TelelumenAPI.light_on(lum, brightness=0.8):
    print("Success!")
else:
    print("Failed to turn on")
```

### 4. Use Type Hints

```python
from telelumen_api import Luminaire, TelelumenAPI
from typing import Optional

def control_luminaire(lum: Luminaire, brightness: float) -> bool:
    """Control a luminaire with type safety."""
    return TelelumenAPI.set_brightness(lum, brightness)
```

---

## Troubleshooting

### Discovery Finds Nothing

```python
# Try specific network
TelelumenAPI.configure(
    discovery_networks=['192.168.1.']
)
luminaires = TelelumenAPI.discover()
```

### Connection Timeout

```python
# Increase timeout
TelelumenAPI.configure(connection_timeout=20.0)
lum = TelelumenAPI.connect('192.168.1.100')
```

### Enable Debug Logging

```python
TelelumenAPI.configure(debug=True)
# Now see detailed debug messages
```

---

## Summary

The new clean API provides:

✅ **Better Architecture** - Proper OOP design  
✅ **Clear Errors** - Meaningful error messages  
✅ **Easy Configuration** - Centralized settings  
✅ **Type Safety** - Full type hints  
✅ **Simple Interface** - Static class for ease of use  
✅ **Thread Safe** - Proper locking  
✅ **Well Documented** - Clear docstrings  
✅ **Maintainable** - Easy to extend and modify  

**Result:** A professional, production-ready API that's easy to use and maintain!

---

**Version:** 2.0  
**Created:** February 4, 2026  
**Author:** Théo Poujol
