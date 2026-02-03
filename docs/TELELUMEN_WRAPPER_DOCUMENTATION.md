# Telelumen Wrapper Documentation

## Overview

The Telelumen Wrapper is a simplified Python interface designed to make working with Telelumen lighting booths easier and more intuitive. It provides a clean, user-friendly API that abstracts away the complexity of the manufacturer's `api_tng.py` library, making it accessible to novice programmers and those with limited experience.

**Author:** Théo Poujol  
**Created:** January 27, 2026  
**Last Modified:** February 2, 2026

---

## Purpose

This wrapper was created to address two main challenges:

1. **Network Complexity** - The Telelumen lighting booths can be capricious to connect to over the network
2. **API Complexity** - The manufacturer's `api_tng.py` is comprehensive but complex and difficult to read for newcomers

The wrapper provides:
- Simplified discovery and connection methods
- Clear, intuitive function names
- Automatic error handling
- User-friendly console feedback
- Common operations wrapped in single function calls

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Class Reference](#class-reference)
4. [Usage Examples](#usage-examples)
5. [API Reference](#api-reference)
6. [Comparison with api_tng](#comparison-with-api_tng)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

```bash
# Install required packages
pip install paho-mqtt
```

### File Structure

```
Telelumen-Wrapper/
├── api/
│   └── api_tng.py          # Manufacturer's API
├── telelumen_wrapper.py     # This wrapper
├── requirements.txt         # Dependencies
└── README.md
```

### Import

```python
from telelumen_wrapper import Telelumen
```

---

## Quick Start

### Simple Example: Connect and Control

```python
from telelumen_wrapper import Telelumen

# Discover and connect to a luminaire
lum = Telelumen.connect_from_list()

if lum is not None:
    # Turn on the light at 50% brightness
    Telelumen.light_on(lum, brightness=0.5)
    
    # Get temperature
    temp = Telelumen.get_temperature(lum)
    print(f"Temperature: {temp}°C")
    
    # Turn off the light
    Telelumen.light_off(lum)
    
    # Disconnect
    Telelumen.disconnect(lum)
```

### Interactive Mode

When you run the wrapper directly, it provides an interactive connection interface:

```bash
python telelumen_wrapper.py
```

The wrapper will:
1. Discover all luminaires on the network
2. Display a numbered list with IP addresses and serial numbers
3. Prompt you to choose which luminaire to connect to
4. Establish the connection
5. Automatically disconnect when done

---

## Class Reference

### Class: `Telelumen`

A static wrapper class that provides simplified methods for Telelumen luminaire operations.

**Design Pattern:** All methods are static, so you don't need to instantiate the class. Call methods directly:

```python
Telelumen.discover_luminaires()
Telelumen.connect_by_ip("192.168.1.100")
```

---

## API Reference

### Discovery & Connection Methods

#### `discover_luminaires()`

Discover all available luminaires on the network.

**Returns:**
- `list`: List of Luminaire objects if found
- `None`: If no luminaires found or error occurred

**Example:**
```python
luminaires = Telelumen.discover_luminaires()

if luminaires:
    print(f"Found {len(luminaires)} luminaire(s)")
    for lum in luminaires:
        print(f"  - {lum.address}")
else:
    print("No luminaires found")
```

**Console Output:**
```
=== Discovering luminaires ===
-> Found 2 luminaire(s)

  IP: 192.168.1.100 | Serial: TL-2021-001
  IP: 192.168.1.101 | Serial: TL-2021-002
```

---

#### `connect_from_list(choice=None)`

Interactive method to list available luminaires and connect to one or all of them.

**Parameters:**
- `choice` (str/int, optional):
  - `None` (default): Prompts user for input
  - `0` to `n`: Index of luminaire to connect to
  - `"all"`: Connect to all discovered luminaires

**Returns:**
- `Luminaire`: Single Luminaire object (if connecting to one)
- `list`: List of Luminaire objects (if connecting to all)
- `None`: If connection failed or no luminaires found

**Example 1: Interactive Mode**
```python
lum = Telelumen.connect_from_list()
# User will be prompted to choose
```

**Example 2: Programmatic - Connect to First**
```python
lum = Telelumen.connect_from_list(choice=0)
```

**Example 3: Programmatic - Connect to All**
```python
luminaires = Telelumen.connect_from_list(choice="all")
if luminaires:
    print(f"Connected to {len(luminaires)} luminaire(s)")
```

**Console Output (Interactive):**
```
=== Discovering luminaires ===
-> Found 2 luminaire(s)

  IP: 192.168.1.100 | Serial: TL-2021-001
  IP: 192.168.1.101 | Serial: TL-2021-002

Found 2 luminaire(s):
  [0] IP: 192.168.1.100 | Serial: TL-2021-001
  [1] IP: 192.168.1.101 | Serial: TL-2021-002

Enter luminaire index (0-1) or 'all' to connect to all: 0

Trying to connect to 192.168.1.100 / TL-2021-001
-> Connection established
```

---

#### `connect_by_ip(ip_address, port=None)`

Connect directly to a luminaire using its IP address.

**Parameters:**
- `ip_address` (str): IP address of the luminaire (e.g., "192.168.1.100")
- `port` (int, optional): Port number. If `None`, uses default port (57007)

**Returns:**
- `Luminaire`: Luminaire object if connection successful
- `None`: If connection failed

**Example:**
```python
# Connect using default port
lum = Telelumen.connect_by_ip("192.168.1.100")

# Connect using custom port
lum = Telelumen.connect_by_ip("192.168.1.100", port=57007)

if lum:
    print(f"Connected to {lum.address}")
else:
    print("Connection failed")
```

**Console Output:**
```
Trying to connect to luminaire at 192.168.1.100:57007
-> Connection established to 192.168.1.100 / TL-2021-001
```

**Use Case:** When you already know the IP address and want to skip discovery.

---

#### `connect_by_serial(serial_number)`

Find and connect to a specific luminaire by its serial number.

**Parameters:**
- `serial_number` (str): Serial number of the target luminaire

**Returns:**
- `Luminaire`: Luminaire object if found and connected
- `None`: If not found or connection failed

**Example:**
```python
lum = Telelumen.connect_by_serial("TL-2021-001")

if lum:
    print(f"Connected to luminaire at {lum.address}")
else:
    print("Luminaire not found")
```

**Console Output:**
```
Searching for luminaire with serial number: TL-2021-001
=== Discovering luminaires ===
-> Found 2 luminaire(s)

  IP: 192.168.1.100 | Serial: TL-2021-001
  IP: 192.168.1.101 | Serial: TL-2021-002

Found luminaire at 192.168.1.100
Trying to connect to 192.168.1.100 / TL-2021-001
-> Connection established
```

**Use Case:** When you know the serial number but not the IP address (useful when IP addresses change via DHCP).

---

#### `disconnect(lum)`

Disconnect from luminaire(s) and close connection(s).

**Parameters:**
- `lum`: Single Luminaire object or list of Luminaire objects

**Returns:**
- `0`: Success
- `-1`: Failure

**Example 1: Single Luminaire**
```python
lum = Telelumen.connect_by_ip("192.168.1.100")
# ... do work ...
Telelumen.disconnect(lum)
```

**Example 2: Multiple Luminaires**
```python
luminaires = Telelumen.connect_from_list(choice="all")
# ... do work ...
Telelumen.disconnect(luminaires)
```

**Console Output:**
```
-> Connection closed for 192.168.1.100
```

**Important:** Always disconnect when finished to free resources and allow other applications to connect.

---

### Control Methods

#### `light_on(lum, brightness=1.0)`

Turn on the luminaire with specified brightness.

**Parameters:**
- `lum` (Luminaire): Luminaire object
- `brightness` (float, optional): Brightness level from 0.0 to 1.0 (default: 1.0 = full brightness)

**Returns:**
- `0`: Success
- `None`: Failure

**Example:**
```python
# Turn on at full brightness
Telelumen.light_on(lum)

# Turn on at 50% brightness
Telelumen.light_on(lum, brightness=0.5)

# Turn on at 25% brightness
Telelumen.light_on(lum, brightness=0.25)
```

**Note:** This sets all channels to the same brightness level.

---

#### `light_off(lum)`

Turn off the luminaire (all channels to 0).

**Parameters:**
- `lum` (Luminaire): Luminaire object

**Returns:**
- `0`: Success
- `None`: Failure

**Example:**
```python
Telelumen.light_off(lum)
```

**Equivalent to:** `lum.go_dark()` in the underlying API.

---

#### `set_brightness(lum, brightness)`

Adjust the brightness of all channels.

**Parameters:**
- `lum` (Luminaire): Luminaire object
- `brightness` (float): Brightness level from 0.0 to 1.0

**Returns:**
- `0`: Success
- `None`: Failure

**Example:**
```python
# Fade from bright to dark
import time

for level in range(10, -1, -1):
    brightness = level / 10.0  # 1.0, 0.9, 0.8, ... 0.0
    Telelumen.set_brightness(lum, brightness)
    time.sleep(0.2)
```

**Difference from `light_on()`:** 
- `light_on()` is designed for initial turn-on with optional brightness
- `set_brightness()` is designed for adjusting brightness after the light is already on
- Functionally, they do the same thing

---

#### `set_intensities(lum, intensities)`

Set specific intensity levels for individual channels using a 13-channel input.

**Parameters:**
- `lum` (Luminaire): Luminaire object
- `intensities` (list): List of 13 float values (0.0 to 1.0), one per channel

**Returns:**
- `0`: Success
- `-1`: Failure

**Channel Mapping (13 channels → 24 channels):**

Input (13 channels):
```python
[RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2]
```

Output (24 channels):
```python
[0, 0, 0, 0, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, 0, 0, 0, 0, 0, 0, 0]
```

The mapping is: `[UV1, UV2, V1, V2, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, DR1, DR2, FR1, FR2, FR3, IR1, IR2]`

**Example:**
```python
# Define intensities for 13 channels
intensities = [
    0.8,  # RB1 - Royal Blue 1
    0.8,  # RB2 - Royal Blue 2
    0.6,  # B1  - Blue 1
    0.6,  # B2  - Blue 2
    0.5,  # C   - Cyan
    0.7,  # G1  - Green 1
    0.7,  # G2  - Green 2
    0.4,  # L   - Lime
    0.3,  # PC-A - Phosphor Converted Amber
    0.9,  # A   - Amber
    0.8,  # OR  - Orange
    0.9,  # R1  - Red 1
    0.9   # R2  - Red 2
]

Telelumen.set_intensities(lum, intensities)
```

**Use Case:** When you need fine-grained control over specific LED channels, particularly for color mixing.

---

### Monitoring Methods

#### `get_temperature(lum)`

Get the current temperature of the luminaire in Celsius.

**Parameters:**
- `lum` (Luminaire): Luminaire object

**Returns:**
- `float`: Temperature in Celsius
- `None`: If failed or not supported

**Example:**
```python
temp = Telelumen.get_temperature(lum)

if temp is not None:
    print(f"Current temperature: {temp}°C")
    
    if float(temp) > 60:
        print("Warning: High temperature detected!")
else:
    print("Temperature reading not available")
```

**Note:** Not supported on Light Replicator (legacy device).

---

### Utility Methods

#### `from13to24(vec)`

Convert a 13-element channel vector to a 24-element vector.

**Parameters:**
- `vec` (list): List of 13 float values

**Returns:**
- `list`: List of 24 float values with padding

**Example:**
```python
# 13-channel input
input_channels = [0.8, 0.8, 0.6, 0.6, 0.5, 0.7, 0.7, 0.4, 0.3, 0.9, 0.8, 0.9, 0.9]

# Convert to 24-channel format
output_channels = Telelumen.from13to24(input_channels)

print(len(output_channels))  # Output: 24
```

**Internal Use:** This method is primarily used internally by `set_intensities()`. You typically won't need to call it directly unless you're doing custom channel mapping.

---

## Usage Examples

### Example 1: Simple On/Off Control

```python
from telelumen_wrapper import Telelumen
import time

# Connect to first available luminaire
lum = Telelumen.connect_from_list(choice=0)

if lum:
    # Turn on at full brightness
    print("Turning on...")
    Telelumen.light_on(lum, brightness=1.0)
    time.sleep(2)
    
    # Turn off
    print("Turning off...")
    Telelumen.light_off(lum)
    
    # Disconnect
    Telelumen.disconnect(lum)
```

---

### Example 2: Brightness Ramping

```python
from telelumen_wrapper import Telelumen
import time

lum = Telelumen.connect_from_list(choice=0)

if lum:
    print("Ramping brightness up...")
    # Fade in from 0% to 100%
    for i in range(0, 101, 5):
        brightness = i / 100.0
        Telelumen.set_brightness(lum, brightness)
        time.sleep(0.1)
    
    time.sleep(1)
    
    print("Ramping brightness down...")
    # Fade out from 100% to 0%
    for i in range(100, -1, -5):
        brightness = i / 100.0
        Telelumen.set_brightness(lum, brightness)
        time.sleep(0.1)
    
    Telelumen.disconnect(lum)
```

---

### Example 3: Multi-Luminaire Control

```python
from telelumen_wrapper import Telelumen
import time

# Connect to all luminaires
luminaires = Telelumen.connect_from_list(choice="all")

if luminaires:
    print(f"Controlling {len(luminaires)} luminaire(s)")
    
    # Turn all on at 70% brightness
    for lum in luminaires:
        Telelumen.light_on(lum, brightness=0.7)
    
    time.sleep(3)
    
    # Turn all off
    for lum in luminaires:
        Telelumen.light_off(lum)
    
    # Disconnect all
    Telelumen.disconnect(luminaires)
```

---

### Example 4: Temperature Monitoring

```python
from telelumen_wrapper import Telelumen
import time

lum = Telelumen.connect_by_ip("192.168.1.100")

if lum:
    # Monitor temperature for 30 seconds
    for i in range(6):
        temp = Telelumen.get_temperature(lum)
        
        if temp:
            print(f"Temperature: {temp}°C")
            
            # Warning if too hot
            if float(temp) > 65:
                print("⚠️  High temperature! Reducing brightness...")
                Telelumen.set_brightness(lum, 0.5)
        else:
            print("Temperature unavailable")
        
        time.sleep(5)
    
    Telelumen.disconnect(lum)
```

---

### Example 5: Color Mixing with Channel Control

```python
from telelumen_wrapper import Telelumen
import time

lum = Telelumen.connect_from_list(choice=0)

if lum:
    # Warm white (more red/amber channels)
    print("Setting warm white...")
    warm_white = [
        0.0, 0.0,  # Royal Blue
        0.0, 0.0,  # Blue
        0.0,       # Cyan
        0.3, 0.3,  # Green
        0.0,       # Lime
        0.6,       # PC-Amber
        0.8,       # Amber
        0.6,       # Orange
        0.7, 0.7   # Red
    ]
    Telelumen.set_intensities(lum, warm_white)
    time.sleep(2)
    
    # Cool white (more blue channels)
    print("Setting cool white...")
    cool_white = [
        0.7, 0.7,  # Royal Blue
        0.8, 0.8,  # Blue
        0.5,       # Cyan
        0.4, 0.4,  # Green
        0.0,       # Lime
        0.2,       # PC-Amber
        0.0,       # Amber
        0.0,       # Orange
        0.0, 0.0   # Red
    ]
    Telelumen.set_intensities(lum, cool_white)
    time.sleep(2)
    
    # Daylight simulation
    print("Setting daylight...")
    daylight = [
        0.4, 0.4,  # Royal Blue
        0.5, 0.5,  # Blue
        0.3,       # Cyan
        0.6, 0.6,  # Green
        0.2,       # Lime
        0.3,       # PC-Amber
        0.1,       # Amber
        0.0,       # Orange
        0.0, 0.0   # Red
    ]
    Telelumen.set_intensities(lum, daylight)
    time.sleep(2)
    
    Telelumen.light_off(lum)
    Telelumen.disconnect(lum)
```

---

### Example 6: Error Handling

```python
from telelumen_wrapper import Telelumen

def safe_control():
    """Example with proper error handling."""
    
    # Try to connect
    lum = Telelumen.connect_from_list(choice=0)
    
    if lum is None:
        print("Failed to connect to luminaire")
        return
    
    try:
        # Try to turn on
        result = Telelumen.light_on(lum, brightness=0.8)
        
        if result == 0:
            print("Light turned on successfully")
        else:
            print("Failed to turn on light")
        
        # Try to get temperature
        temp = Telelumen.get_temperature(lum)
        
        if temp is not None:
            print(f"Temperature: {temp}°C")
        else:
            print("Temperature reading failed (may not be supported)")
        
    except Exception as e:
        print(f"Error during operation: {e}")
    
    finally:
        # Always disconnect
        print("Disconnecting...")
        result = Telelumen.disconnect(lum)
        
        if result == 0:
            print("Disconnected successfully")
        else:
            print("Disconnect failed")

# Run the function
safe_control()
```

---

## Comparison with api_tng

The wrapper simplifies common operations:

### Discovery & Connection

**With api_tng:**
```python
import api_tng as api

# Discover
luminaires = api.discover()

# Open connection
if len(luminaires) > 0:
    lum = luminaires[0]
    result = api.openLuminaire(lum.address, api.luminairePort)
    if result == 0:
        # Connected
        pass
```

**With Telelumen Wrapper:**
```python
from telelumen_wrapper import Telelumen

# Discover and connect in one step
lum = Telelumen.connect_from_list(choice=0)
```

### Turning Light On/Off

**With api_tng:**
```python
# Turn off
lum.go_dark()

# Turn on - need to know number of channels
num_channels = lum.get_number_of_channels()
drive_levels = [1.0] * num_channels
lum.set_drive_levels(drive_levels)
```

**With Telelumen Wrapper:**
```python
# Turn off
Telelumen.light_off(lum)

# Turn on
Telelumen.light_on(lum, brightness=1.0)
```

### Disconnecting

**With api_tng:**
```python
api.closeLuminaire(lum.address)
```

**With Telelumen Wrapper:**
```python
Telelumen.disconnect(lum)
```

---

## Best Practices

### 1. Always Disconnect

```python
lum = Telelumen.connect_from_list(choice=0)
try:
    # Your code here
    Telelumen.light_on(lum)
finally:
    # Always disconnect
    Telelumen.disconnect(lum)
```

### 2. Check Return Values

```python
lum = Telelumen.connect_by_ip("192.168.1.100")

if lum is None:
    print("Connection failed")
    return

result = Telelumen.light_on(lum)

if result == 0:
    print("Success")
else:
    print("Failed to turn on")
```

### 3. Use Appropriate Connection Method

- **Interactive/Testing:** `connect_from_list()` (no arguments)
- **Known IP:** `connect_by_ip(ip_address)`
- **Known Serial:** `connect_by_serial(serial_number)`
- **Programmatic:** `connect_from_list(choice=0)` or `connect_from_list(choice="all")`

### 4. Validate Brightness Values

```python
def safe_set_brightness(lum, brightness):
    # Clamp brightness to valid range
    brightness = max(0.0, min(1.0, brightness))
    return Telelumen.set_brightness(lum, brightness)
```

### 5. Handle Multi-Luminaire Operations Properly

```python
luminaires = Telelumen.connect_from_list(choice="all")

if luminaires:
    # Process each
    for lum in luminaires:
        result = Telelumen.light_on(lum, brightness=0.5)
        if result != 0:
            print(f"Failed to turn on {lum.address}")
    
    # Disconnect all at once
    Telelumen.disconnect(luminaires)
```

---

## Troubleshooting

### No Luminaires Found

**Problem:**
```python
luminaires = Telelumen.discover_luminaires()
# Returns None
```

**Solutions:**
1. Verify luminaires are powered on
2. Wait 20-60 seconds after power-on for network initialization
3. Check network connectivity
4. Verify you're on the same network as the luminaires
5. Try specifying network explicitly in the underlying API:
   ```python
   import api.api_tng as api
   api.set_network('192.168.1.')
   luminaires = Telelumen.discover_luminaires()
   ```

### Connection Fails

**Problem:**
```python
lum = Telelumen.connect_by_ip("192.168.1.100")
# Returns None
```

**Solutions:**
1. Verify IP address is correct
2. Check if another application is connected to the luminaire
3. Try disconnecting and reconnecting:
   ```python
   # Close any existing connections
   import api.api_tng as api
   api.closeLuminaire("192.168.1.100")
   
   # Try connecting again
   lum = Telelumen.connect_by_ip("192.168.1.100")
   ```

### Temperature Reading Returns None

**Problem:**
```python
temp = Telelumen.get_temperature(lum)
# Returns None
```

**Solutions:**
1. Check if luminaire type supports temperature reading:
   ```python
   print(f"Luminaire type: {lum.lumtype}")
   # Light Replicator does not support temperature
   ```
2. Verify connection is still active
3. Try reading again after a short delay

### Brightness/Intensity Not Changing

**Problem:**
```python
Telelumen.set_brightness(lum, 0.5)
# Light doesn't change
```

**Solutions:**
1. Check if a script is currently playing:
   ```python
   # Stop any playing scripts first
   lum.stop()
   # Then set brightness
   Telelumen.set_brightness(lum, 0.5)
   ```
2. Verify return value to check for errors:
   ```python
   result = Telelumen.set_brightness(lum, 0.5)
   if result != 0:
       print("Failed to set brightness")
   ```

### Import Error

**Problem:**
```python
from telelumen_wrapper import Telelumen
# ModuleNotFoundError: No module named 'api.api_tng'
```

**Solution:**
Ensure the file structure is correct and the `api` directory exists:
```
Telelumen-Wrapper/
├── api/
│   ├── __init__.py  # May need to create this (can be empty)
│   └── api_tng.py
└── telelumen_wrapper.py
```

---

## Advanced Usage

### Custom Channel Mapping

If you need a different channel mapping than the default 13→24 conversion:

```python
def custom_channel_map(channels):
    """Custom mapping for your specific needs."""
    # Define your own 24-channel mapping
    output = [0.0] * 24
    
    # Example: Map first 10 channels directly
    for i in range(min(10, len(channels))):
        output[i] = channels[i]
    
    return output

# Use custom mapping
lum = Telelumen.connect_from_list(choice=0)
custom_levels = custom_channel_map(your_channel_data)
lum.set_drive_levels(custom_levels)
```

### Integration with Scripts

The wrapper can be used alongside script playback:

```python
from telelumen_wrapper import Telelumen

lum = Telelumen.connect_from_list(choice=0)

# Play a script
lum.play("sunset.lsp")

# Wait for script to finish, then take manual control
import time
time.sleep(60)  # Assume script is 60 seconds

lum.stop()  # Stop script

# Manual control
Telelumen.set_brightness(lum, 0.3)

Telelumen.disconnect(lum)
```

---

## Notes

### Design Philosophy

The wrapper follows these principles:

1. **Simplicity Over Completeness** - Covers common use cases, not every feature
2. **Clear Naming** - Function names describe what they do
3. **Automatic Error Handling** - Try/except blocks handle most errors gracefully
4. **User Feedback** - Console output keeps users informed
5. **Beginner Friendly** - Easy for those with limited Python experience

### When to Use api_tng Directly

Use the underlying `api_tng` API directly when you need:

- File upload/download operations
- Script management (create, delete, list)
- Firmware updates
- Advanced streaming operations
- Custom UDP/MQTT communication
- Direct access to raw drive levels
- Luminaire configuration changes

### Contributing

This wrapper is designed to be extended. To add new functionality:

1. Add a new static method to the `Telelumen` class
2. Use try/except for error handling
3. Return intuitive values (`None` for failure, `0` for success, data for queries)
4. Add console feedback with `print()` where helpful
5. Document your method in this file

---

## Summary

The Telelumen Wrapper provides a simplified interface for:

- ✅ **Discovery** - Find luminaires on the network
- ✅ **Connection** - Connect by IP, serial, or interactively
- ✅ **Basic Control** - On/off, brightness adjustment
- ✅ **Channel Control** - Individual channel intensity setting
- ✅ **Monitoring** - Temperature reading
- ✅ **Multi-Device** - Control multiple luminaires

For advanced features like file management, script control, and streaming, use the underlying `api_tng` API directly.

---

## Quick Reference

```python
# Import
from telelumen_wrapper import Telelumen

# Connect
lum = Telelumen.connect_from_list()           # Interactive
lum = Telelumen.connect_from_list(choice=0)   # First luminaire
lum = Telelumen.connect_by_ip("192.168.1.100")
lum = Telelumen.connect_by_serial("TL-2021-001")

# Control
Telelumen.light_on(lum, brightness=0.8)
Telelumen.light_off(lum)
Telelumen.set_brightness(lum, 0.5)
Telelumen.set_intensities(lum, [0.5]*13)

# Monitor
temp = Telelumen.get_temperature(lum)

# Disconnect
Telelumen.disconnect(lum)
```

---

## See Also

- [API_TNG_DOCUMENTATION.md](API_TNG_DOCUMENTATION.md) - Complete manufacturer API documentation
- [README.md](README.md) - Project overview and setup instructions
- Official Telelumen documentation (if available)

---

**Last Updated:** February 3, 2026  
**Version:** 1.0
