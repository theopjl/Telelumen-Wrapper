"""
Telelumen API - Clean Architecture Version

Created on February 4, 2026
@author: Théo Poujol

A clean, maintainable rewrite of the Telelumen API with proper architecture,
error handling, and encapsulation.

Features:
- Clean code architecture with proper separation of concerns
- Static class encapsulation (TelelumenAPI)
- Proper error handling with meaningful messages
- Configuration-based instead of hardcoded values
- Easy to maintain and extend
- Type hints for better IDE support
"""

from __future__ import annotations
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import socket
import telnetlib
import threading
import time
import re
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class APIConfig:
    """Central configuration for the Telelumen API."""
    
    # Network settings
    DEFAULT_PORT: int = 57007
    DISCONNECT_PORT: int = 57011
    UDP_PORT: int = 57000
    
    # Timeouts
    CONNECTION_TIMEOUT: float = 10.0
    COMMAND_TIMEOUT: float = 5.0
    DISCOVERY_TIMEOUT: float = 30.0
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 0.5
    
    # Discovery settings
    DISCOVERY_NETWORKS: List[str] = None
    SCAN_START_IP: int = 2
    SCAN_END_IP: int = 254
    
    # File transfer
    FILE_BLOCK_SIZE: int = 512
    MAX_FILE_RETRIES: int = 10
    
    # Logging
    VERBOSE: bool = True
    DEBUG: bool = False
    
    def __post_init__(self):
        if self.DISCOVERY_NETWORKS is None:
            self.DISCOVERY_NETWORKS = [
                '192.168.0.', '192.168.1.', '192.168.2.', 
                '192.168.3.', '192.168.4.', '192.168.5.',
                '192.168.6.', '192.168.7.', '192.168.8.',
                '192.168.9.', '192.168.10.', '192.168.11.'
            ]


class LuminaireType(Enum):
    """Enumeration of supported luminaire types."""
    OCTA = "Octa"
    PENTA = "Penta"
    LIGHT_REPLICATOR = "LightReplicator"
    UNKNOWN = "Unknown"


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class TelelumenError(Exception):
    """Base exception for Telelumen API errors."""
    pass


class ConnectionError(TelelumenError):
    """Raised when connection fails."""
    pass


class CommandError(TelelumenError):
    """Raised when a command fails."""
    pass


class DiscoveryError(TelelumenError):
    """Raised when discovery fails."""
    pass


class FileTransferError(TelelumenError):
    """Raised when file transfer fails."""
    pass


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class LuminaireConnection:
    """Manages telnet connection to a single luminaire."""
    
    def __init__(self, ip_address: str, port: int, timeout: float):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.telnet: Optional[telnetlib.Telnet] = None
        self.state = ConnectionState.DISCONNECTED
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """
        Establish connection to luminaire.
        
        Returns:
            True if connected successfully, False otherwise
        
        Raises:
            ConnectionError: If connection fails
        """
        with self._lock:
            if self.state == ConnectionState.CONNECTED:
                return True
            
            try:
                self.state = ConnectionState.CONNECTING
                self.telnet = telnetlib.Telnet(
                    self.ip_address, 
                    self.port, 
                    self.timeout
                )
                self.state = ConnectionState.CONNECTED
                return True
                
            except socket.timeout:
                self.state = ConnectionState.ERROR
                raise ConnectionError(
                    f"Connection timeout to {self.ip_address}:{self.port}"
                )
            except socket.error as e:
                self.state = ConnectionState.ERROR
                if "Connection refused" in str(e):
                    raise ConnectionError(
                        f"Connection refused by {self.ip_address}:{self.port}. "
                        "Device may be busy or not responding."
                    )
                raise ConnectionError(
                    f"Socket error connecting to {self.ip_address}:{self.port}: {e}"
                )
            except Exception as e:
                self.state = ConnectionState.ERROR
                raise ConnectionError(
                    f"Failed to connect to {self.ip_address}:{self.port}: {e}"
                )
    
    def disconnect(self) -> bool:
        """
        Close connection to luminaire.
        
        Returns:
            True if disconnected successfully
        """
        with self._lock:
            try:
                if self.telnet:
                    self.telnet.close()
                    self.telnet = None
                self.state = ConnectionState.DISCONNECTED
                return True
            except Exception as e:
                Logger.error(f"Error disconnecting from {self.ip_address}: {e}")
                return False
    
    def send_command(self, command: str, wait_for_response: bool = True) -> Optional[str]:
        """
        Send a command to the luminaire.
        
        Args:
            command: Command string to send
            wait_for_response: Whether to wait for and return response
        
        Returns:
            Response string if wait_for_response=True, None otherwise
        
        Raises:
            CommandError: If command fails
        """
        if self.state != ConnectionState.CONNECTED or not self.telnet:
            raise CommandError(f"Not connected to {self.ip_address}")
        
        try:
            # Send command with carriage return
            self.telnet.write((command + '\r').encode())
            
            if wait_for_response:
                # Read until semicolon (luminaire response terminator)
                response = self.telnet.read_until(b";", self.timeout).decode()
                return response
            
            return None
            
        except socket.timeout:
            raise CommandError(
                f"Command timeout for '{command}' on {self.ip_address}"
            )
        except Exception as e:
            raise CommandError(
                f"Command '{command}' failed on {self.ip_address}: {e}"
            )
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.state == ConnectionState.CONNECTED and self.telnet is not None


# ============================================================================
# LOGGER
# ============================================================================

class Logger:
    """Simple logger for API operations."""
    
    verbose = True
    debug = False
    
    @classmethod
    def info(cls, message: str):
        """Log info message."""
        if cls.verbose:
            print(f"[INFO] {message}")
    
    @classmethod
    def debug(cls, message: str):
        """Log debug message."""
        if cls.debug:
            print(f"[DEBUG] {message}")
    
    @classmethod
    def error(cls, message: str):
        """Log error message."""
        print(f"[ERROR] {message}")
    
    @classmethod
    def warning(cls, message: str):
        """Log warning message."""
        if cls.verbose:
            print(f"[WARNING] {message}")
    
    @classmethod
    def success(cls, message: str):
        """Log success message."""
        if cls.verbose:
            print(f"[SUCCESS] {message}")


# ============================================================================
# LUMINAIRE CLASS
# ============================================================================

class Luminaire:
    """Represents a single Telelumen luminaire device."""
    
    def __init__(self, ip_address: str, config: APIConfig = None):
        """
        Initialize luminaire.
        
        Args:
            ip_address: IP address of the luminaire
            config: Optional API configuration
        """
        self.ip_address = ip_address
        self.config = config or APIConfig()
        self.connection: Optional[LuminaireConnection] = None
        
        # Device information
        self.serial_number: Optional[str] = None
        self.electronic_serial: Optional[str] = None
        self.firmware_version: Optional[str] = None
        self.luminaire_type: LuminaireType = LuminaireType.UNKNOWN
        self.mac_address: Optional[str] = None
        
        # Status
        self.last_command_status: int = 0
    
    def connect(self) -> bool:
        """
        Connect to the luminaire.
        
        Returns:
            True if connection successful
        
        Raises:
            ConnectionError: If connection fails
        """
        if self.connection and self.connection.is_connected():
            return True
        
        self.connection = LuminaireConnection(
            self.ip_address,
            self.config.DEFAULT_PORT,
            self.config.CONNECTION_TIMEOUT
        )
        
        result = self.connection.connect()
        
        if result:
            # Get device info after connecting
            self._initialize_device_info()
            Logger.success(f"Connected to luminaire at {self.ip_address}")
        
        return result
    
    def disconnect(self) -> bool:
        """Disconnect from the luminaire."""
        if self.connection:
            result = self.connection.disconnect()
            if result:
                Logger.info(f"Disconnected from {self.ip_address}")
            return result
        return True
    
    def _initialize_device_info(self):
        """
        Initialize device information after connection.
        Each command is independent: a failure on one does not abort the others.
        """
        try:
            self.firmware_version = self._get_version()
        except Exception as e:
            Logger.warning(f"Failed to get firmware version: {e}")

        try:
            self.electronic_serial = self._get_electronic_serial()
        except Exception as e:
            Logger.warning(f"Failed to get electronic serial: {e}")

        try:
            self.luminaire_type = self._detect_luminaire_type()
        except Exception as e:
            Logger.warning(f"Failed to detect luminaire type: {e}")

        try:
            self.serial_number = self._get_serial_number()
        except Exception as e:
            Logger.warning(f"Failed to get serial number: {e}")
    
    def _send_command(self, command: str) -> Tuple[str, int]:
        """
        Send command and parse response.
        
        Returns:
            Tuple of (response_text, status_code)
        """
        if not self.connection or not self.connection.is_connected():
            raise CommandError("Not connected to luminaire")
        
        response = self.connection.send_command(command)
        
        # Parse response: last line before semicolon is status code
        lines = response.replace('\r\n', '\n').split('\n')
        status_line = lines[-1].rstrip(';')
        
        try:
            status_code = int(status_line)
        except (ValueError, IndexError):
            status_code = -1
        
        # Remove status code from response
        response_text = '\n'.join(lines[:-1])
        
        self.last_command_status = status_code
        return response_text, status_code
    
    # ========================================================================
    # DEVICE INFORMATION
    # ========================================================================
    
    def _get_version(self) -> str:
        """Get firmware version."""
        response, status = self._send_command('VER')
        return response.strip()
    
    def _get_electronic_serial(self) -> str:
        """Get electronic serial number."""
        response, status = self._send_command('NS')
        return response.strip()
    
    def _get_serial_number(self) -> str:
        """Get luminaire serial number."""
        if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
            return self.electronic_serial
        
        response, status = self._send_command('GETSERNO')
        return response.strip()
    
    def _detect_luminaire_type(self) -> LuminaireType:
        """Detect the type of luminaire."""
        try:
            response, status = self._send_command('ID')
            
            # Light Replicator doesn't support ID command
            if 'mV' in response and 'mA' in response:
                return LuminaireType.LIGHT_REPLICATOR
            
            # Parse luminaire type from response
            type_str = response.split(':')[0].strip()
            
            if 'Octa' in type_str:
                return LuminaireType.OCTA
            elif 'Penta' in type_str:
                return LuminaireType.PENTA
            
        except Exception:
            pass
        
        return LuminaireType.UNKNOWN
    
    def get_temperature(self) -> Optional[float]:
        """
        Get luminaire temperature in Celsius.
        
        Returns:
            Temperature value or None if not supported
        """
        if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
            Logger.warning("Temperature not supported on Light Replicator")
            return None
        
        try:
            response, status = self._send_command('TEMPC')
            
            # Parse temperature from response
            match = re.search(r'Temp\(C\):\s*([\d.]+)', response)
            if match:
                return float(match.group(1))
        
        except Exception as e:
            Logger.error(f"Failed to get temperature: {e}")
        
        return None
    
    def get_mac_address(self) -> Optional[str]:
        """Get MAC address."""
        try:
            response, status = self._send_command('GETIP')
            parts = response.split()
            if parts:
                self.mac_address = parts[-1]
                return self.mac_address
        except Exception as e:
            Logger.error(f"Failed to get MAC address: {e}")
        
        return None
    
    # ========================================================================
    # DRIVE LEVEL CONTROL
    # ========================================================================
    
    def get_drive_levels(self) -> List[float]:
        """
        Get normalized drive levels (0.0 to 1.0) for all channels.
        
        Returns:
            List of drive level values
        """
        try:
            response, status = self._send_command('PS?')
            hex_values = response.strip().split(',')
            
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                # Light Replicator uses PWM/AM pairs
                drive_levels = []
                for i in range(0, len(hex_values), 2):
                    pwm = int(hex_values[i], 16)
                    am = int(hex_values[i+1], 16)
                    intensity = float(pwm * am) / 4128705.0
                    drive_levels.append(intensity)
                return drive_levels
            else:
                # Octa/Penta use 16-bit values
                return [int(val, 16) / 65535.0 for val in hex_values]
        
        except Exception as e:
            Logger.error(f"Failed to get drive levels: {e}")
            return []
    
    def set_drive_levels(self, levels: List[float]) -> bool:
        """
        Set drive levels for all channels.
        
        Args:
            levels: List of values from 0.0 to 1.0
        
        Returns:
            True if successful
        """
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                # Convert to PWM/AM pairs
                command = 'PA'
                for level in levels:
                    pwm, am = self._calculate_pwm_am(level)
                    command += f'{pwm:04X}{am:02X}'
            else:
                # Convert to 16-bit hex values
                command = 'PS'
                for level in levels:
                    value = int(level * 65535)
                    command += f'{value:04X}'
            
            response, status = self._send_command(command)
            return status == 0
        
        except Exception as e:
            Logger.error(f"Failed to set drive levels: {e}")
            return False
    
    def set_drive_level(self, channel: int, level: float) -> bool:
        """
        Set drive level for a single channel.
        
        Args:
            channel: Channel number (0-based)
            level: Value from 0.0 to 1.0
        
        Returns:
            True if successful
        """
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                pwm, am = self._calculate_pwm_am(level)
                command = f'PC{channel:02d}{pwm:04X}{am:02X}'
            else:
                value = int(level * 65535)
                command = f'P{channel:02d}{value:04X}'
            
            response, status = self._send_command(command)
            return status == 0
        
        except Exception as e:
            Logger.error(f"Failed to set drive level for channel {channel}: {e}")
            return False
    
    @staticmethod
    def _calculate_pwm_am(intensity: float) -> Tuple[int, int]:
        """Calculate PWM and AM values for Light Replicator."""
        am_bits = 6
        pwm_bits = 16
        am_min = 4
        am_max = (2 ** am_bits) - 1
        pwm_max = (2 ** pwm_bits) - 1
        
        fam = float(am_max) * intensity
        iam = int(round(fam))
        iam = max(am_min, min(am_max, iam))
        
        pwm = int(fam * float(pwm_max) / float(iam))
        
        return pwm, iam
    
    # ========================================================================
    # LIGHTING CONTROL
    # ========================================================================
    
    def go_dark(self) -> bool:
        """Turn off all LEDs."""
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                response, status = self._send_command('B')
            else:
                response, status = self._send_command('DARK')
            
            return status == 0
        
        except Exception as e:
            Logger.error(f"Failed to go dark: {e}")
            return False
    
    def reset(self) -> bool:
        """Reset (reboot) the luminaire."""
        try:
            response, status = self._send_command('RESET')
            return status == 0
        except Exception as e:
            Logger.error(f"Failed to reset: {e}")
            return False
    
    # ========================================================================
    # SCRIPT PLAYBACK
    # ========================================================================
    
    def play_script(self, filename: str, wait: bool = False) -> bool:
        """
        Play a script file.
        
        Args:
            filename: Script filename
            wait: If True, load but wait for resume() to start
        
        Returns:
            True if successful
        """
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                command = f'SETPAT={filename}'
            else:
                if not filename:
                    command = 'PLAY'
                elif wait:
                    command = f'PLAYPAUSED {filename}'
                else:
                    command = f'PLAY {filename}'
            
            response, status = self._send_command(command)
            return status == 0
        
        except Exception as e:
            Logger.error(f"Failed to play script: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause script playback."""
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                command = 'Q5'
            else:
                command = 'PAUSE'
            
            response, status = self._send_command(command)
            return status == 0
        except Exception as e:
            Logger.error(f"Failed to pause: {e}")
            return False
    
    def resume(self) -> bool:
        """Resume script playback."""
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                command = 'Q2'
            else:
                command = 'RESUME'
            
            response, status = self._send_command(command)
            return status == 0
        except Exception as e:
            Logger.error(f"Failed to resume: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop script playback."""
        try:
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                self._send_command('Q8')
                return self.go_dark()
            else:
                response, status = self._send_command('STOP')
                return status == 0
        except Exception as e:
            Logger.error(f"Failed to stop: {e}")
            return False
    
    # ========================================================================
    # FILE MANAGEMENT
    # ========================================================================
    
    def get_directory(self) -> List[str]:
        """Get list of files on luminaire."""
        try:
            response, status = self._send_command('DIR')
            
            if self.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
                lines = response.split('\n')
                files = []
                for line in lines:
                    idx = line.find('`')
                    if idx > 0:
                        files.append(line[:idx])
                return files
            else:
                lines = response.split('\n')
                return lines[1:-3]  # Skip header and footer
        
        except Exception as e:
            Logger.error(f"Failed to get directory: {e}")
            return []
    
    def __repr__(self) -> str:
        """String representation of luminaire."""
        return (
            f"Luminaire(ip={self.ip_address}, "
            f"type={self.luminaire_type.value}, "
            f"serial={self.serial_number})"
        )


# ============================================================================
# DISCOVERY
# ============================================================================

class Discovery:
    """
    Handles luminaire discovery on the network.

    Faithfully ported from api_tng.py with the same internal functions and
    logic.  Threading has been removed: all IP scans run sequentially.
    At the end, IP strings are converted to connected Luminaire objects.
    """

    # Connection timeout identical to the original api_tng constant
    TELNET_CONNECTION_TIMEOUT: float = 6.0

    # --- Internal state (mirrors the module-level globals of api_tng) ---
    _luminaire_network: str = '0.0.0.'
    _luminaire_list: List[str] = []
    _refused_list: List[str] = []
    _telnet_connections: Dict[str, telnetlib.Telnet] = {}
    _lock = threading.Lock()  # Protects shared state during threaded discovery

    # ------------------------------------------------------------------ #
    #  Low-level connection helpers (mirrors openConnection / openLuminaire
    #  / getReply / sendMessage / closeLuminaire from api_tng)
    # ------------------------------------------------------------------ #

    @classmethod
    def _open_connection(cls, ip: str, port: int) -> bool:
        """
        Create a telnet connection to ip:port.
        Returns True on success, False on failure.
        Mirrors api_tng.openConnection().
        """
        try:
            tn = telnetlib.Telnet(ip, port, cls.TELNET_CONNECTION_TIMEOUT)
            with cls._lock:
                cls._telnet_connections[ip] = tn
            Logger.info(f'OK: _open_connection({ip}:{port})')
            return True
        except socket.error as exc:
            if 'Connection refused' in str(exc):
                with cls._lock:
                    cls._refused_list.append(ip)
                #Logger.info(f'FAIL: CONNECTION REFUSED {ip}')
            #Logger.info(f'FAIL: _open_connection({ip}:{port}): {exc}')
            return False
        except Exception as exc:
            #Logger.info(f'FAIL: _open_connection({ip}:{port}): {exc}')
            return False

    @classmethod
    def _open_luminaire(cls, ip: str, port: int) -> bool:
        """
        Open a luminaire connection on the given port.
        Mirrors api_tng.openLuminaire().
        """
        try:
            return cls._open_connection(ip, port)
        except Exception as exc:
            Logger.info(f'_open_luminaire({ip}:{port}) exception: {exc}')
            return False

    @classmethod
    def _get_reply(cls, ip: str) -> str:
        """
        Read a semicolon-terminated reply from the luminaire.
        Mirrors api_tng.getReply().
        """
        try:
            tn = cls._telnet_connections.get(ip)
            if tn:
                return tn.read_until(b';').decode()
        except Exception as exc:
            Logger.info(f'_get_reply({ip}) exception: {exc}')
        return ''

    @classmethod
    def _send_message(cls, ip: str, msg: str) -> str:
        """
        Send a message and return the reply.
        Mirrors api_tng.sendMessage().
        """
        try:
            tn = cls._telnet_connections.get(ip)
            if tn:
                tn.write((msg + '\r').encode())
                return cls._get_reply(ip)
        except Exception as exc:
            Logger.info(f'_send_message({ip}, {msg}) exception: {exc}')
        return ''

    @classmethod
    def _close_connection(cls, ip: str):
        """
        Close and discard the telnet connection for ip.
        Mirrors api_tng.closeLuminaire() (connection part only).
        """
        try:
            tn = cls._telnet_connections.pop(ip, None)
            if tn:
                tn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Discovery helpers (mirrors __get_serial_number / addLuminaire /
    #  removeLuminaire from api_tng)
    # ------------------------------------------------------------------ #

    @classmethod
    def _get_serial_number(cls, ip: str):
        """
        Request the serial number / NS reply from an already-connected ip.
        Returns the response string, or False on failure.
        Mirrors api_tng.__get_serial_number().
        """
        try:
            res = cls._send_message(ip, 'NS')
            return res if res else False
        except Exception as exc:
            Logger.info(f'_get_serial_number({ip}) exception: {exc}')
            return False

    @classmethod
    def _add_luminaire(cls, ip: str):
        """
        Add ip to the discovered list (de-duplicated, sorted).
        Mirrors api_tng.addLuminaire().
        """
        try:
            with cls._lock:
                if ip not in cls._luminaire_list:
                    cls._luminaire_list.append(ip)
                    cls._luminaire_list.sort()
            Logger.info(f'addLuminaire(ip={ip})')
        except Exception as exc:
            Logger.info(f'_add_luminaire({ip}) exception: {exc}')

    @classmethod
    def _remove_luminaire(cls, ip: str):
        """
        Remove ip from the discovered list if present.
        Mirrors api_tng.removeLuminaire().
        """
        try:
            with cls._lock:
                if ip in cls._luminaire_list:
                    cls._luminaire_list.remove(ip)
            #Logger.info(f'removeLuminaire(ip={ip})')
        except Exception as exc:
            Logger.info(f'_remove_luminaire({ip}) exception: {exc}')

    # ------------------------------------------------------------------ #
    #  Discovery poll (mirrors api_tng.__discoveryPoll)
    # ------------------------------------------------------------------ #

    @classmethod
    def _discovery_poll(cls, address: int, port: int):
        """
        Probe one IP address on the given port.
        If the device responds with a valid serial number it is added to
        _luminaire_list and its connection is kept open in _telnet_connections.
        Otherwise the device is removed from the list and the connection is
        closed immediately.
        Mirrors api_tng.__discoveryPoll().
        """
        ip = cls._luminaire_network + str(address)
        valid = False
        try:
            if cls._open_luminaire(ip, port):
                try:
                    sn = cls._get_serial_number(ip)
                    if sn is not False and sn:
                        cls._add_luminaire(ip)
                        valid = True    # Keep connection open
                    else:
                        cls._remove_luminaire(ip)
                except Exception as exc:
                    Logger.info(f'_discovery_poll({ip}) inner exception: {exc}')
                    cls._remove_luminaire(ip)
            else:
                cls._remove_luminaire(ip)
        except Exception as exc:
            Logger.info(f'_discovery_poll({ip}) exception: {exc}')
        finally:
            if not valid:
                cls._close_connection(ip)

    # ------------------------------------------------------------------ #
    #  Core discovery (mirrors api_tng.__discover_one / __discover_all)
    # ------------------------------------------------------------------ #

    @classmethod
    def _is_alive(cls, tasks: List[threading.Thread]) -> bool:
        """
        Return True if any thread in tasks is still running.
        Mirrors api_tng.is_alive().
        """
        try:
            for t in tasks:
                if t.is_alive():
                    return True
            return False
        except Exception as exc:
            Logger.info(f'_is_alive() exception: {exc}')
            return False

    @classmethod
    def _discover_one(cls, net: str, port: int) -> List[str]:
        """
        Scan every IP on *net* for luminaires on the given port.
        Faithfully mirrors api_tng.__discover_one():
          - one thread per IP address (range 2..253 inclusive)
          - all threads created, then all started
          - waits with is_alive() + sleep(1.0) loop until all finish
        """
        # Close any leftover connections from a previous pass
        for ip in list(cls._telnet_connections.keys()):
            cls._close_connection(ip)

        cls._luminaire_list = []
        cls._refused_list = []
        cls._luminaire_network = net

        lower_tid = 2
        upper_tid = 254
        ip_offset = 0

        #Logger.info(
        #    f'_discover_one(net={net}, port={port}): creating threads for IPs '
        #    f'{lower_tid}..{upper_tid - 1}'
        #)

        # --- Create threads (mirrors: for i in range(...): luminaireTask[i] = Thread(...)) ---
        tasks: List[threading.Thread] = [None] * upper_tid
        for i in range(lower_tid, upper_tid):
            tasks[i] = threading.Thread(
                target=cls._discovery_poll,
                args=(i + ip_offset, port),
                daemon=True
            )

        # --- Start threads (mirrors: for i in range(...): luminaireTask[i].start()) ---
        #Logger.info('_discover_one(): starting threads')
        for i in range(lower_tid, upper_tid):
            tasks[i].start()

        # --- Wait for completion (mirrors: while is_alive(...): time.sleep(1.0)) ---
        #Logger.info('_discover_one(): waiting for threads to finish')
        active = [tasks[i] for i in range(lower_tid, upper_tid)]
        while cls._is_alive(active):
            time.sleep(1.0)

        #Logger.info('_discover_one(): all threads finished')
        cls._luminaire_list.sort()
        #Logger.info(f'_discover_one() returns: {cls._luminaire_list}')
        return cls._luminaire_list

    @classmethod
    def _discover_all(
        cls,
        networks: Optional[List[str]] = None,
        config: Optional[APIConfig] = None
    ) -> List[str]:
        """
        Run the full two-pass discovery across all candidate networks.

        Pass 1 — disconnectRequestPort (57011): forces ARP table population
                 and wakes the luminaire network stack (connections are expected
                 to be refused or empty — side-effect is what matters).
        Pass 2 — luminairePort (57007): real connection + NS validation.

        Returns a list of valid luminaire IP strings (same as api_tng
        __discover_all).  Stops after the first network that yields results.
        Mirrors api_tng.__discover_all().
        """
        config = config or APIConfig()
        networks = networks or config.DISCOVERY_NETWORKS

        disconnect_port = config.DISCONNECT_PORT  # 57011
        luminaire_port  = config.DEFAULT_PORT     # 57007

        Logger.info(f'_discover_all: scanning {len(networks)} network(s)')

        for net in networks:
            Logger.info(f'Attempting discover on {net}')
            cls._discover_one(net, disconnect_port)            # Pass 1: ARP wake
            lumlist = cls._discover_one(net, luminaire_port)   # Pass 2: real connect
            if lumlist:
                Logger.info(f'Found luminaires on {net}: {lumlist}')
                return lumlist

        return []

    # ------------------------------------------------------------------ #
    #  Public entry point — returns Luminaire objects
    # ------------------------------------------------------------------ #

    @classmethod
    def discover(
        cls,
        networks: Optional[List[str]] = None,
        config: Optional[APIConfig] = None
    ) -> List[Luminaire]:
        """
        Discover all luminaires on the network and return ready-to-use
        Luminaire objects.

        Internally runs _discover_all() (two-pass, sequential, no threads).
        The raw telnet connections opened during Pass 2 are reused directly —
        no second TCP handshake is needed.

        Args:
            networks: List of network prefixes to search (e.g. ['192.168.1.'])
            config:   Optional API configuration

        Returns:
            List of connected and initialised Luminaire objects
        """
        config = config or APIConfig()

        Logger.info('Discovering luminaires...')
        ip_list = cls._discover_all(networks, config)

        if not ip_list:
            Logger.info('No luminaires found.')
            return []

        luminaires: List[Luminaire] = []
        for ip in ip_list:
            try:
                luminaire = Luminaire(ip, config)

                # Reuse the live telnet connection that _discover_all kept open
                tn = cls._telnet_connections.get(ip)
                if tn:
                    conn = LuminaireConnection(
                        ip, config.DEFAULT_PORT, config.CONNECTION_TIMEOUT
                    )
                    conn.telnet = tn
                    conn.state = ConnectionState.CONNECTED
                    luminaire.connection = conn
                else:
                    # Fallback: open a fresh connection
                    luminaire.connect()

                luminaire._initialize_device_info()
                luminaires.append(luminaire)
                Logger.success(f'Luminaire ready at {ip}')

            except Exception as exc:
                Logger.error(f'Failed to initialise luminaire at {ip}: {exc}')

        Logger.success(
            f'Discovery complete: {len(luminaires)} luminaire(s) found'
        )
        return luminaires


# ============================================================================
# MAIN API CLASS
# ============================================================================

class TelelumenAPI:
    """
    Main static API class for Telelumen luminaire control.
    
    This class provides a clean, static interface for all luminaire operations.
    """
    
    _config = APIConfig()
    _connections: Dict[str, Luminaire] = {}
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    @classmethod
    def configure(
        cls,
        verbose: bool = None,
        debug: bool = None,
        connection_timeout: float = None,
        discovery_networks: List[str] = None
    ):
        """
        Configure API settings.
        
        Args:
            verbose: Enable/disable verbose logging
            debug: Enable/disable debug logging
            connection_timeout: Connection timeout in seconds
            discovery_networks: List of networks to search during discovery
        """
        if verbose is not None:
            cls._config.VERBOSE = verbose
            Logger.verbose = verbose
        
        if debug is not None:
            cls._config.DEBUG = debug
            Logger.debug = debug
        
        if connection_timeout is not None:
            cls._config.CONNECTION_TIMEOUT = connection_timeout
        
        if discovery_networks is not None:
            cls._config.DISCOVERY_NETWORKS = discovery_networks
    
    # ========================================================================
    # DISCOVERY & CONNECTION
    # ========================================================================
    
    @classmethod
    def discover(cls, networks: Optional[List[str]] = None) -> List[Luminaire]:
        """
        Discover all luminaires on the network.
        
        Args:
            networks: Optional list of network prefixes to search
        
        Returns:
            List of discovered Luminaire objects
        """
        return Discovery.discover(networks, cls._config)
    
    @classmethod
    def connect(cls, ip_address: str) -> Luminaire:
        """
        Connect to a luminaire by IP address.
        
        Args:
            ip_address: IP address of the luminaire
        
        Returns:
            Connected Luminaire object
        
        Raises:
            ConnectionError: If connection fails
        """
        # Check if already connected
        if ip_address in cls._connections:
            luminaire = cls._connections[ip_address]
            if luminaire.connection and luminaire.connection.is_connected():
                return luminaire
        
        # Create new connection
        luminaire = Luminaire(ip_address, cls._config)
        luminaire.connect()
        
        cls._connections[ip_address] = luminaire
        return luminaire
    
    @classmethod
    def disconnect(cls, luminaire: Luminaire) -> bool:
        """
        Disconnect from a luminaire.
        
        Args:
            luminaire: Luminaire object to disconnect
        
        Returns:
            True if successful
        """
        result = luminaire.disconnect()
        
        if result and luminaire.ip_address in cls._connections:
            del cls._connections[luminaire.ip_address]
        
        return result
    
    @classmethod
    def disconnect_all(cls) -> int:
        """
        Disconnect from all connected luminaires.
        
        Returns:
            Number of luminaires disconnected
        """
        count = 0
        for luminaire in list(cls._connections.values()):
            if cls.disconnect(luminaire):
                count += 1
        
        return count
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    @classmethod
    def set_brightness(cls, luminaire: Luminaire, brightness: float) -> bool:
        """
        Set brightness for all channels.
        
        Args:
            luminaire: Target luminaire
            brightness: Brightness value (0.0 to 1.0)
        
        Returns:
            True if successful
        """
        # Get current number of channels
        current_levels = luminaire.get_drive_levels()
        if not current_levels:
            # Default to 24 channels for Octa/Penta, 32 for LR
            num_channels = 32 if luminaire.luminaire_type == LuminaireType.LIGHT_REPLICATOR else 24
        else:
            num_channels = len(current_levels)
        
        levels = [brightness] * num_channels
        return luminaire.set_drive_levels(levels)
    
    @classmethod
    def light_on(cls, luminaire: Luminaire, brightness: float = 1.0) -> bool:
        """
        Turn on luminaire at specified brightness.
        
        Args:
            luminaire: Target luminaire
            brightness: Brightness value (0.0 to 1.0)
        
        Returns:
            True if successful
        """
        return cls.set_brightness(luminaire, brightness)
    
    @classmethod
    def light_off(cls, luminaire: Luminaire) -> bool:
        """
        Turn off luminaire.
        
        Args:
            luminaire: Target luminaire
        
        Returns:
            True if successful
        """
        return luminaire.go_dark()
    
    @classmethod
    def get_info(cls, luminaire: Luminaire) -> Dict[str, any]:
        """
        Get comprehensive information about a luminaire.
        
        Args:
            luminaire: Target luminaire
        
        Returns:
            Dictionary with device information
        """
        return {
            'ip_address': luminaire.ip_address,
            'serial_number': luminaire.serial_number,
            'electronic_serial': luminaire.electronic_serial,
            'firmware_version': luminaire.firmware_version,
            'luminaire_type': luminaire.luminaire_type.value,
            'mac_address': luminaire.mac_address,
            'temperature': luminaire.get_temperature(),
            'connected': luminaire.connection.is_connected() if luminaire.connection else False
        }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'TelelumenAPI',
    'Luminaire',
    'LuminaireType',
    'APIConfig',
    'TelelumenError',
    'ConnectionError',
    'CommandError',
    'DiscoveryError',
    'FileTransferError',
    'Logger'
]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Configure API
    TelelumenAPI.configure(verbose=True, debug=False)
    
    # Discover luminaires
    print("\n=== Discovering Luminaires ===")
    luminaires = TelelumenAPI.discover()
    
    if not luminaires:
        print("No luminaires found!")
        exit(0)
    
    print(f"\nFound {len(luminaires)} luminaire(s):")
    for lum in luminaires:
        info = TelelumenAPI.get_info(lum)
        print(f"  - {info['ip_address']}: {info['luminaire_type']} "
              f"(Serial: {info['serial_number']})")
    
    # Test with first luminaire
    lum = luminaires[0]
    print(f"\n=== Testing with {lum.ip_address} ===")
    
    # Turn on at 50%
    print("Setting brightness to 50%...")
    TelelumenAPI.light_on(lum, brightness=0.5)
    time.sleep(2)
    
    # Get temperature
    temp = lum.get_temperature()
    if temp:
        print(f"Temperature: {temp}°C")
    
    # Turn off
    print("Turning off...")
    TelelumenAPI.light_off(lum)
    
    # Disconnect all
    print("\n=== Disconnecting ===")
    count = TelelumenAPI.disconnect_all()
    print(f"Disconnected from {count} luminaire(s)")
