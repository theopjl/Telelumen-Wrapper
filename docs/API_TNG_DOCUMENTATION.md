# Telelumen API (api_tng.py) Documentation

## Overview

The `api_tng.py` is the official Telelumen LLC Python API for controlling Telelumen lighting booths (luminaires). This API provides low-level and high-level interfaces to discover, connect to, and control various Telelumen luminaire models over a network.

**Version:** 4.12 (Python 3 compatible)  
**Copyright:** (c) 2020-2021 Telelumen LLC. All rights reserved.

---

## Table of Contents

1. [Supported Devices](#supported-devices)
2. [Dependencies](#dependencies)
3. [Quick Start](#quick-start)
4. [Core Classes](#core-classes)
5. [Global Functions](#global-functions)
6. [Network & Discovery](#network--discovery)
7. [Communication Protocols](#communication-protocols)
8. [File Operations](#file-operations)
9. [Error Handling](#error-handling)
10. [Constants](#constants)

---

## Supported Devices

- **Octa** - Full-featured luminaire
- **Penta** - Full-featured luminaire  
- **Light Replicator (LR)** - Legacy device with limited command support

---

## Dependencies

### Required
```python
paho.mqtt.client  # For MQTT communication
telnetlib         # For TCP/IP connections
socket            # For network operations
```

### Optional
```python
netifaces         # For automatic network interface detection (fallback available)
```

### Standard Library
```python
sys, threading, datetime, array, struct, json, binascii, copy, time, re
```

---

## Quick Start

### Basic Usage Example

```python
import api_tng as api

# 1. Discover all luminaires on the network
luminaires = api.discover()

if len(luminaires) > 0:
    # 2. Connect to the first luminaire
    lum = luminaires[0]
    print(f"Connected to: {lum.address}")
    
    # 3. Get luminaire information
    serial = lum.get_luminaire_serial_number()
    version = lum.get_version()
    print(f"Serial: {serial}, Version: {version}")
    
    # 4. Control the luminaire
    lum.play("script_name.lsp")
    
    # 5. Set drive levels (brightness)
    drive_levels = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # 50% brightness
    lum.set_drive_levels(drive_levels)
    
    # 6. Close connection
    api.closeLuminaire(lum.address)
```

### Discover on Specific Network

```python
import api_tng as api

# Discover luminaires on a specific Class C network
api.set_network('192.168.1.')
luminaires = api.discover('192.168.1.')
```

---

## Core Classes

### Class: `Luminaire`

The main class representing a Telelumen luminaire device.

#### Constructor

```python
Luminaire(link_address, link_type='ip')
```

**Parameters:**
- `link_address` (str): IP address of the luminaire (e.g., "192.168.1.100")
- `link_type` (str): Connection type. Currently supports `'ip'` (Ethernet) or `'dmx'`

**Attributes:**
- `address` - IP address of the luminaire
- `fw_ver` - Firmware version
- `electronic_serial_number` - Electronic serial number
- `luminaire_serial_number` - Luminaire serial number
- `lumtype` - Type of luminaire ('Octa', 'Penta', or 'LightReplicator')
- `last_message_status` - Status code from last command (0 = success)

#### Device Information Methods

##### `get_version()`
Returns the firmware version string.

```python
version = lum.get_version()
# Returns: "v4.12.3" (example)
```

##### `get_electronic_serial_number()`
Returns the electronic serial number.

```python
esn = lum.get_electronic_serial_number()
# Returns: "12345678" (example)
```

##### `get_luminaire_serial_number()`
Returns the luminaire serial number.

```python
serial = lum.get_luminaire_serial_number()
# Returns: "TL-2021-001" (example)
```

##### `get_luminaire_type()`
Returns the luminaire type.

```python
lum_type = lum.get_luminaire_type()
# Returns: "Octa", "Penta", or "LightReplicator"
```

##### `get_ip_address()` / `get_ip()`
Returns the IP address of the luminaire.

```python
ip = lum.get_ip()
# Returns: "192.168.1.100"
```

##### `get_mac()`
Returns the MAC address.

```python
mac = lum.get_mac()
# Returns: "AA:BB:CC:DD:EE:FF"
```

##### `get_ip_extras()`
Returns detailed IP configuration information.

```python
info = lum.get_ip_extras()
# Returns: Complete IP configuration string
```

##### `get_channel_map()`
Returns the channel mapping configuration.

```python
channel_map = lum.get_channel_map()
# Returns: Channel map string
```

##### `get_chipset()`
Returns chipset information (not supported on Light Replicator).

```python
chipset = lum.get_chipset()
# Returns: Chipset identifier
```

##### `get_temperature()`
Returns the current temperature in Celsius (not supported on Light Replicator).

```python
temp = lum.get_temperature()
# Returns: "45.2" (example)
```

##### `get_uptime()`
Returns system uptime (not supported on Light Replicator).

```python
uptime = lum.get_uptime()
# Returns: Uptime string
```

#### File System Methods

##### `get_directory()`
Returns list of files on the luminaire.

```python
files = lum.get_directory()
# Returns: ['script1.lsp', 'script2.lsp', ...]
```

##### `get_used_blocks()`
Returns number of storage blocks in use.

```python
used = lum.get_used_blocks()
# Returns: 150 (example)
```

##### `get_free_blocks()`
Returns number of free storage blocks.

```python
free = lum.get_free_blocks()
# Returns: 1879 (example, total is typically 2029)
```

##### `send_file(inpath, outfn, idle_after_load=True)`
Upload a file to the luminaire.

**Parameters:**
- `inpath` (str): Full local file path
- `outfn` (str): Filename on luminaire (no path)
- `idle_after_load` (bool): If True, luminaire stays idle after upload

**Returns:** 0 on success, error code otherwise

```python
status = lum.send_file('/home/user/script.lsp', 'script.lsp')
if status == 0:
    print("File uploaded successfully")
```

##### `receive_file(luminaire_filename, filesys_filename)`
Download a file from the luminaire.

**Parameters:**
- `luminaire_filename` (str): Filename on luminaire
- `filesys_filename` (str): Local destination path

**Returns:** 0 on success, -1 on failure

```python
status = lum.receive_file('script.lsp', '/home/user/downloaded_script.lsp')
```

##### `delete(filename)`
Delete a file from the luminaire.

**Parameters:**
- `filename` (str): Name of file to delete

**Returns:** Status code (0 = success, 9 = file not found)

```python
status = lum.delete('old_script.lsp')
```

##### `format()`
Format the luminaire's file system. **⚠️ WARNING: This is non-reversible!**

Takes approximately 2-6 minutes to complete.

```python
lum.format()  # Use with extreme caution!
```

##### `get_lrc(filename)`
Get the LRC (Longitudinal Redundancy Check) of a file.

**Parameters:**
- `filename` (str): Filename on luminaire

**Returns:** Integer LRC value

```python
lrc = lum.get_lrc('script.lsp')
# Returns: 0x12345678 (example)
```

#### Playback Control Methods

##### `play(filename, wait=False)`
Play a script file.

**Parameters:**
- `filename` (str): Script filename. Empty string plays current script
- `wait` (bool): If True, loads script but waits for `resume()` to start

**Returns:** Status code

```python
# Play immediately
lum.play('sunset.lsp')

# Load but wait (paused state)
lum.play('sunset.lsp', wait=True)
lum.resume()  # Start playback
```

##### `pause()`
Pause current script playback.

```python
lum.pause()
```

##### `resume()`
Resume paused script playback.

```python
lum.resume()
```

##### `stop()`
Stop script playback and go dark.

```python
lum.stop()
```

##### `go_dark()`
Turn off all channels (all LEDs off).

```python
lum.go_dark()
```

##### `get_current_script()`
Get the name of currently playing script (not supported on Light Replicator).

```python
current = lum.get_current_script()
# Returns: "sunset.lsp"
```

##### `play_first_script()`
Play the first script in the file list.

```python
lum.play_first_script()
```

##### `play_last_script()`
Play the last script in the file list.

```python
lum.play_last_script()
```

##### `play_next_script()`
Play the next script in sequence.

```python
lum.play_next_script()
```

##### `play_previous_script()`
Play the previous script in sequence.

```python
lum.play_previous_script()
```

#### Drive Level Methods

Drive levels control the intensity of each LED channel, ranging from 0.0 (off) to 1.0 (full brightness).

##### `get_drive_levels()`
Get normalized drive levels (0.0 to 1.0) for all channels.

**Returns:** List of floats

```python
levels = lum.get_drive_levels()
# Returns: [0.5, 0.3, 0.8, 0.0, 1.0, 0.6, 0.4, 0.2]
```

##### `get_drive_levels_raw()`
Get raw drive level values (0 to 65535).

**Returns:** List of integers

```python
raw_levels = lum.get_drive_levels_raw()
# Returns: [32767, 19660, 52428, 0, 65535, ...]
```

##### `set_drive_levels(drive_vector_fractional)`
Set normalized drive levels for all channels.

**Parameters:**
- `drive_vector_fractional` (list): List of floats (0.0 to 1.0)

**Returns:** Status code

```python
# Set all channels to different levels
levels = [1.0, 0.8, 0.6, 0.4, 0.2, 0.0, 0.5, 0.7]
lum.set_drive_levels(levels)
```

##### `set_drive_levels_raw(drive_vector)`
Set raw drive levels for all channels.

**Parameters:**
- `drive_vector` (list): List of integers (0 to 65535)

**Returns:** Status code

```python
raw_levels = [65535, 32767, 16384, 8192, 4096, 2048, 1024, 512]
lum.set_drive_levels_raw(raw_levels)
```

##### `set_drive_level(channel, level)`
Set drive level for a single channel.

**Parameters:**
- `channel` (int): Channel number (0-based)
- `level` (float): Intensity value (0.0 to 1.0)

**Returns:** Status code

```python
# Set channel 0 to 75% brightness
lum.set_drive_level(0, 0.75)
```

#### Streaming Methods

Streaming allows synchronized playback across multiple luminaires.

##### `get_stream_info()`
Get streaming configuration information.

**Returns:** String with streaming details

```python
info = lum.get_stream_info()
```

##### `get_stream_channel()`
Get the current streaming channel number.

**Returns:** Integer channel number (0 if not streaming)

```python
channel = lum.get_stream_channel()
# Returns: 1-255 if streaming, 0 if not
```

##### `get_stream_enabled()`
Check if streaming is enabled.

**Returns:** Boolean

```python
is_streaming = lum.get_stream_enabled()
# Returns: True or False
```

##### `get_stream_leader()`
Check if this luminaire is the stream leader.

**Returns:** Boolean

```python
is_leader = lum.get_stream_leader()
# Returns: True or False
```

##### `stream_join(channel)`
Join a streaming channel.

**Parameters:**
- `channel` (int): Channel number (1-255)

**Returns:** Boolean (False on success, True on error)

```python
# Join streaming channel 1
lum.stream_join(1)
```

##### `stream_quit()`
Leave the current streaming channel.

**Returns:** Boolean (False on success, True on error)

```python
lum.stream_quit()
```

##### `stream_leader(leader)`
Set or unset this luminaire as the stream leader.

**Parameters:**
- `leader` (bool): True to become leader, False to relinquish

**Returns:** Boolean (False on success, True on error)

```python
# Become the stream leader
lum.stream_leader(True)

# Stop being the stream leader
lum.stream_leader(False)
```

#### Low-Level Methods

##### `send_message(cmd)`
Send a command and receive response.

**Parameters:**
- `cmd` (str): Command string (without terminator)

**Returns:** Response string (without status code)

```python
response = lum.send_message('VER')
# Returns: "v4.12.3"
```

##### `send_message_raw(cmd)`
Send a command without waiting for response.

**Parameters:**
- `cmd` (str): Command string

```python
lum.send_message_raw('RESET')
```

##### `get_last_message_status()`
Get status code from last command.

**Returns:** Integer status code (0 = success)

```python
status = lum.get_last_message_status()
if status == 0:
    print("Command successful")
```

##### `reset()`
Reset (reboot) the luminaire.

```python
lum.reset()
```

---

### Class: `UDPmsg`

UDP-based communication class for connectionless messaging (alternative to telnet).

#### Constructor

```python
UDPmsg(timeout=0.1, port=57000)
```

**Parameters:**
- `timeout` (float): Socket timeout in seconds
- `port` (int): UDP port number

#### Methods

##### `sendto(dst_ip, msg)`
Send a message to specified IP address. **Must be called first before other methods.**

**Parameters:**
- `dst_ip` (str): Destination IP address
- `msg` (str): Message string

**Returns:** 0 on success, -1 on error

```python
udp = api.UDPmsg()
udp.sendto('192.168.1.100', 'NS')  # Get serial number
```

##### `send(msg)`
Send message to previously established destination.

**Parameters:**
- `msg` (str): Message string

```python
udp.send('VER')  # Get version
```

##### `getfrom()`
Receive response from luminaire.

**Returns:** Tuple of (data, (source_ip, source_port))

```python
data, addr = udp.getfrom()
print(f"Received: {data} from {addr[0]}")
```

##### `set_my_ip(ip)`
Manually set source IP address.

**Parameters:**
- `ip` (str): Source IP address

```python
udp.set_my_ip('192.168.1.50')
```

---

### Class: `mqttMessage`

MQTT-based messaging for power control and other pub/sub operations.

#### Constructor

```python
mqttMessage(ip, port=1883)
```

**Parameters:**
- `ip` (str): MQTT broker IP address
- `port` (int): MQTT broker port (default: 1883)

```python
mqtt = api.mqttMessage('192.168.1.10')
```

#### Methods

##### `publish_message(topic, payload)`
Publish a message to MQTT topic.

```python
mqtt.publish_message('/status', 'online')
```

##### `subscribe_message(topic, qos=1)`
Subscribe to MQTT topic.

```python
mqtt.subscribe_message('/power', qos=1)
```

##### `power_on(num)`
Turn on power outlet.

**Parameters:**
- `num` (int): Outlet number

```python
mqtt.power_on(1)
```

##### `power_off(num)`
Turn off power outlet.

**Parameters:**
- `num` (int): Outlet number

```python
mqtt.power_off(1)
```

---

## Global Functions

### Discovery Functions

#### `discover(override_net=None)`

**Main discovery function.** Discovers all Telelumen luminaires on the network.

**Parameters:**
- `override_net` (str, optional): Specific Class C network to search (e.g., "192.168.1." or "192.168.1")

**Returns:** List of `Luminaire` objects

**Example:**
```python
import api_tng as api

# Search all candidate networks
luminaires = api.discover()

# Search specific network
luminaires = api.discover('192.168.1.')

print(f"Found {len(luminaires)} luminaire(s)")
for lum in luminaires:
    print(f"  - {lum.address}: {lum.get_luminaire_serial_number()}")
```

#### `set_network(ip_network)`

Set the Class C network to search for luminaires.

**Parameters:**
- `ip_network` (str): Network prefix (e.g., "192.168.1" or "192.168.1.")

**Returns:** List of network candidates

**Example:**
```python
api.set_network('192.168.11.')
luminaires = api.discover()
```

---

### Connection Functions

#### `openLuminaire(ip, port)`

Open connection to a luminaire.

**Parameters:**
- `ip` (str): IP address
- `port` (int): Port number (usually `api.luminairePort` = 57007)

**Returns:** 0 on success, -1 on failure

**Example:**
```python
result = api.openLuminaire('192.168.1.100', api.luminairePort)
if result == 0:
    print("Connected!")
```

#### `closeLuminaire(ip)`

Close connection to a luminaire.

**Parameters:**
- `ip` (str): IP address

**Returns:** 0 on success, -1 on failure

**Example:**
```python
api.closeLuminaire('192.168.1.100')
```

#### `closeList(lum)`

Close connections to multiple luminaires.

**Parameters:**
- `lum` (list): List of `Luminaire` objects

**Example:**
```python
luminaires = api.discover()
# ... use luminaires ...
api.closeList(luminaires)
```

#### `closeListIp(hostlist)`

Close connections by IP address list.

**Parameters:**
- `hostlist` (list): List of IP addresses

**Example:**
```python
api.closeListIp(['192.168.1.100', '192.168.1.101'])
```

---

### Communication Functions

#### `sendMessage(ip, outMsg)`

Send message and wait for reply.

**Parameters:**
- `ip` (str): IP address
- `outMsg` (str): Command string

**Returns:** Response string

**Example:**
```python
response = api.sendMessage('192.168.1.100', 'VER')
print(f"Version: {response}")
```

#### `sendMessageRaw(ip, outMsg)`

Send message without waiting for reply.

**Parameters:**
- `ip` (str): IP address
- `outMsg` (str): Command string

**Returns:** 0 on success, -1 on failure

#### `sendMessageRetries(ip, retries, outMsg)`

Send message with automatic retries.

**Parameters:**
- `ip` (str): IP address
- `retries` (int): Number of retry attempts
- `outMsg` (str): Command string

**Returns:** Response string

#### `sendMessageParallel(hostip_list, outmsg, tries=3, timeout=2.0)`

Send messages to multiple luminaires in parallel.

**Parameters:**
- `hostip_list` (list or str): List of IP addresses or single IP
- `outmsg` (str or list): Single message or list of messages (one per luminaire)
- `tries` (int): Number of retry attempts
- `timeout` (float): Timeout in seconds

**Returns:** Tuple of (failed_list, [(ip, response), ...])

**Example:**
```python
ips = ['192.168.1.100', '192.168.1.101', '192.168.1.102']
failed, responses = api.sendMessageParallel(ips, 'VER', tries=3, timeout=2.0)

for ip, response in responses:
    print(f"{ip}: {response}")
```

---

### File Transfer Functions

#### `legacy_send_file_lrc(ip, inpath, outfn, reliable=True, wait=True)`

Send file with optional LRC error checking.

**Parameters:**
- `ip` (str): IP address
- `inpath` (str): Local file path
- `outfn` (str): Remote filename
- `reliable` (bool): Use LRC error checking (not supported on Light Replicator)
- `wait` (bool): Keep luminaire idle after upload

**Returns:** 0 on success, -1 on failure

#### `receive_file(ip, luminaire_filename, filesys_filename)`

Receive file from Octa/Penta.

**Parameters:**
- `ip` (str): IP address
- `luminaire_filename` (str): Filename on luminaire
- `filesys_filename` (str): Local destination path

**Returns:** 0 on success, -1 on failure

#### `receive_file_lr(ip, luminaire_filename, filesys_filename)`

Receive file from Light Replicator (legacy).

**Parameters:** Same as `receive_file()`

#### `compute_file_lrc(fn)`

Compute LRC checksum of a local file.

**Parameters:**
- `fn` (str): Local file path

**Returns:** 32-bit LRC value

---

### Utility Functions

#### `trace_on()` / `trace_off()`

Enable/disable file logging.

```python
api.trace_on()   # Enable logging
api.trace_off()  # Disable logging
```

#### `console_trace_on()` / `console_trace_off()`

Enable/disable console debug output.

```python
api.console_trace_on()   # Print debug to console
api.console_trace_off()  # Disable console debug
```

#### `logit(msg)`

Write custom message to log.

**Parameters:**
- `msg` (str): Message to log

```python
api.logit("Custom debug message")
```

---

## Network & Discovery

### Network Scanning

The API searches multiple Class C networks by default:

```python
network_candidate_list = [
    '192.168.0.', '192.168.1.', '192.168.2.', '192.168.3.',
    '192.168.4.', '192.168.5.', '192.168.6.', '192.168.7.',
    '192.168.8.', '192.168.9.', '192.168.10.', '192.168.11.'
]
```

Discovery scans IP addresses from `.2` to `.253` on each network.

### Discovery Process

1. Creates threads for parallel scanning
2. Attempts connection to each IP
3. Queries serial number to verify luminaire
4. Returns list of `Luminaire` objects

**Typical discovery time:** 10-30 seconds depending on network size

---

## Communication Protocols

### Telnet (TCP/IP)

- **Primary protocol** for reliable command/response
- **Port:** 57007 (default)
- **Connection timeout:** 6.0 seconds
- Commands are ASCII strings terminated with `\r`
- Responses terminated with `;`

### UDP

- **Alternative protocol** for connectionless messaging
- **Port:** 57000 (default)
- Packet format includes 10-byte header
- Useful for streaming and broadcast operations

### MQTT

- **Port:** 1883 (default, unencrypted)
- Used for power control and pub/sub messaging
- Requires separate MQTT broker

---

## File Operations

### File Format

Scripts are typically `.lsp` (Light Script) files containing lighting sequences.

### Upload Process

1. File is split into 512-byte blocks
2. Each block sent with optional LRC checksum
3. Luminaire validates each block (if LRC enabled)
4. Invalid blocks are automatically retransmitted

### Download Process

1. Open file on luminaire
2. Read in 512-byte blocks
3. Verify LRC checksum for each block
4. Write to local filesystem

### File System Capacity

- **Total blocks:** ~2029
- **Block size:** 512 bytes
- **Total capacity:** ~1 MB

---

## Error Handling

### Status Codes

Commands return integer status codes:

- **0** = Success
- **1** = General error (varies by command)
- **9** = File not found
- **11** = No response from luminaire
- **42** = Invalid LRC checksum

### Exception Handling

The API uses extensive try-except blocks with logging:

```python
try:
    lum.play('script.lsp')
except:
    print("Error occurred")
    # Check last_message_status
    if lum.last_message_status != 0:
        print(f"Error code: {lum.last_message_status}")
```

### Best Practices

```python
# Always check return values
status = lum.delete('old_file.lsp')
if status == 9:
    print("File not found - already deleted?")
elif status == 0:
    print("File deleted successfully")

# Check connection before operations
result = api.openLuminaire(ip, api.luminairePort)
if result == 0:
    # Connection successful - proceed
    lum = api.Luminaire(ip)
    # ... operations ...
    api.closeLuminaire(ip)
else:
    print("Connection failed")
```

---

## Constants

### Ports

```python
luminairePort = 57007              # Main telnet port
disconnectRequestPort = 57011      # Disconnect request port
LUMINAIRE_UDP_PORT = 57000         # UDP messaging port
DEFAULT_BROKER_PORT = 1883         # MQTT broker port
```

### Timeouts

```python
TELNET_CONNECTION_TIMEOUT = 6.0    # Telnet connection timeout (seconds)
maxDiscoverTime = 3.6              # Discovery timeout per network
RECEIVE_RETRIES = 10               # File receive retry attempts
```

### Limits

```python
MAX_PACKET_SIZE = 1400             # UDP packet size limit
```

---

## Complete Example: Multi-Luminaire Control

```python
import api_tng as api
import time

# Enable debug logging
api.trace_on()
api.console_trace_on()

# Discover all luminaires
print("Discovering luminaires...")
luminaires = api.discover()

if len(luminaires) == 0:
    print("No luminaires found!")
    exit(1)

print(f"\nFound {len(luminaires)} luminaire(s):")
for lum in luminaires:
    print(f"  IP: {lum.address}")
    print(f"    Type: {lum.lumtype}")
    print(f"    Serial: {lum.get_luminaire_serial_number()}")
    print(f"    Version: {lum.fw_ver}")
    print()

# Work with first luminaire
lum = luminaires[0]

# Get file list
print("Files on luminaire:")
files = lum.get_directory()
for f in files:
    print(f"  - {f}")

# Upload a script
print("\nUploading script...")
status = lum.send_file('/path/to/local/script.lsp', 'test.lsp')
if status == 0:
    print("Upload successful!")

# Play the script
print("\nPlaying script...")
lum.play('test.lsp')
time.sleep(5)

# Pause playback
print("Pausing...")
lum.pause()
time.sleep(2)

# Resume playback
print("Resuming...")
lum.resume()
time.sleep(5)

# Set manual drive levels
print("\nSetting manual drive levels...")
lum.stop()  # Stop script first
drive_levels = [0.5] * 8  # 50% on all 8 channels
lum.set_drive_levels(drive_levels)
time.sleep(3)

# Fade to dark
print("Fading to dark...")
for brightness in range(50, -1, -5):
    levels = [brightness/100.0] * 8
    lum.set_drive_levels(levels)
    time.sleep(0.1)

# Go completely dark
lum.go_dark()

# Close all connections
print("\nClosing connections...")
api.closeList(luminaires)

print("Done!")
```

---

## Troubleshooting

### Common Issues

#### No Luminaires Discovered

- Check network connectivity
- Verify luminaires are powered on
- Wait 20-60 seconds after luminaire power-on for network initialization
- Try specifying network explicitly: `api.discover('192.168.1.')`
- Check if luminaires are on a different network

#### Connection Refused

- Luminaire may already be connected to another application
- Close other applications using the luminaires
- Try the disconnect request port (57011) first

#### File Upload Fails

- Check available space: `lum.get_free_blocks()`
- Verify file format is compatible
- For Light Replicator, disable LRC: `reliable=False`

#### Commands Return Error Codes

- Check `lum.last_message_status`
- Verify command is supported on your luminaire type
- Some commands not supported on Light Replicator (legacy)

---

## Notes

### Light Replicator Differences

The Light Replicator is a legacy device with some command differences:

- Uses different command syntax for some operations
- No LRC support for file transfers
- Limited streaming capabilities
- Different drive level encoding (PWM + AM pairs)
- Fewer diagnostic commands

The API handles these differences automatically based on detected luminaire type.

### Thread Safety

- Discovery uses threading internally
- Parallel messaging creates temporary threads
- Not recommended to call API functions from multiple threads simultaneously
- Use separate `UDPmsg` objects for concurrent UDP operations

---

## Version History

- **v4.12** - September 8, 2021 - Ported to Python 3
- **v4.11** - January 31, 2021 - Added exception tracking
- **v4.10** - August 5, 2020 - Added UDP and LSO support
- **v4.00** - March 20, 2020 - Full rewrite

---

## Copyright & License

**(c) 2020-2021 Telelumen LLC. All rights reserved.**

This is proprietary software provided by Telelumen LLC. Use is subject to Telelumen's licensing terms.

---

## Support

For additional support, contact Telelumen LLC or refer to the official Telelumen documentation.

---

*This documentation is a reference guide for the api_tng.py API. For wrapper simplifications, see the `telelumen_wrapper.py` documentation.*
