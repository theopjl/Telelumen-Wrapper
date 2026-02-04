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
        """Initialize device information after connection."""
        try:
            self.firmware_version = self._get_version()
            self.electronic_serial = self._get_electronic_serial()
            self.luminaire_type = self._detect_luminaire_type()
            self.serial_number = self._get_serial_number()
        except Exception as e:
            Logger.warning(f"Failed to initialize device info: {e}")
    
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
    """Handles luminaire discovery on the network."""
    
    @staticmethod
    def discover(
        networks: Optional[List[str]] = None,
        config: Optional[APIConfig] = None
    ) -> List[Luminaire]:
        """
        Discover all luminaires on specified networks.
        
        Args:
            networks: List of network prefixes to search (e.g., ['192.168.1.'])
            config: Optional API configuration
        
        Returns:
            List of discovered Luminaire objects
        """
        config = config or APIConfig()
        networks = networks or config.DISCOVERY_NETWORKS
        
        Logger.info(f"Discovering luminaires on {len(networks)} network(s)...")
        
        discovered_luminaires = []
        
        for network in networks:
            Logger.debug(f"Scanning network {network}...")
            luminaires = Discovery._scan_network(network, config)
            
            if luminaires:
                Logger.info(f"Found {len(luminaires)} luminaire(s) on {network}")
                discovered_luminaires.extend(luminaires)
                # Stop searching other networks once we find luminaires on this network
                Logger.info(f"Stopping discovery - luminaires found on {network}")
                break
            else:
                Logger.debug(f"No luminaires found on {network}")
        
        Logger.success(f"Discovery complete: {len(discovered_luminaires)} luminaire(s) found")
        return discovered_luminaires
    
    @staticmethod
    def _scan_network(network: str, config: APIConfig) -> List[Luminaire]:
        """Scan a single network for luminaires."""
        luminaires = []
        threads = []
        lock = threading.Lock()
        
        def check_ip(ip: str):
            """Check if IP has a luminaire."""
            try:
                # Try to connect
                connection = LuminaireConnection(
                    ip,
                    config.DEFAULT_PORT,
                    config.CONNECTION_TIMEOUT
                )
                
                if connection.connect():
                    # Verify it's a luminaire by getting serial number
                    try:
                        response = connection.send_command('NS')
                        if response and ';' in response:
                            # Valid luminaire found
                            luminaire = Luminaire(ip, config)
                            luminaire.connection = connection
                            luminaire._initialize_device_info()
                            print(ip)
                            

                            with lock:
                                luminaires.append(luminaire)
                            
                            Logger.debug(f"Found luminaire at {ip}")
                    except:
                        connection.disconnect()
            except:
                pass  # Not a luminaire or not reachable
        
        # Create threads for parallel scanning
        for i in range(config.SCAN_START_IP, config.SCAN_END_IP):
            ip = f"{network}{i}"
            thread = threading.Thread(target=check_ip, args=(ip,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads with timeout
        start_time = time.time()
        for thread in threads:
            remaining = config.DISCOVERY_TIMEOUT - (time.time() - start_time)
            if remaining > 0:
                thread.join(timeout=remaining)
        
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
