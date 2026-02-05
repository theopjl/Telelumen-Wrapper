"""
Telelumen Wrapper - Using Clean API

Created on February 4, 2026
@author: Théo Poujol

A simplified wrapper using the new clean Telelumen API.
Maintains backward compatibility with the original wrapper interface.
"""

from typing import Optional, List
from api.telelumen_api import TelelumenAPI, Luminaire, Logger


class Telelumen:
    """
    Simplified wrapper class for Telelumen luminaire operations.
    
    This wrapper uses the new clean API architecture while maintaining
    a simple static interface for easy use.
    """
    
    @staticmethod
    def discover_luminaires() -> Optional[List[Luminaire]]:
        """
        Discover all available luminaires on the network.
        
        Returns:
            List of Luminaire objects if found, None otherwise
        """
        try:
            print("=== Discovering luminaires ===")
            luminaires = TelelumenAPI.discover()
            
            if not luminaires:
                print("No luminaires found")
                return None
            
            print(f"-> Found {len(luminaires)} luminaire(s)\n")
            for lum in luminaires:
                print(f"  IP: {lum.ip_address} | Serial: {lum.serial_number}")
            
            return luminaires
        
        except Exception as e:
            print(f"Discovery failed: {e}")
            return None
    
    @staticmethod
    def connect_from_list(choice=None) -> Optional[Luminaire | List[Luminaire]]:
        """
        List available luminaires and connect to one or all of them.
        
        Args:
            choice (str/int, optional): 
                - Integer (0 to n): Index of the luminaire to connect to
                - "all": Connect to all luminaires
                - None: Will prompt user to choose
        
        Returns:
            - Single Luminaire object if connecting to one luminaire
            - List of Luminaire objects if connecting to all
            - None if connection failed
        """
        try:
            luminaires = Telelumen.discover_luminaires()
            
            if not luminaires:
                print("No luminaires found")
                return None
            
            # Display list of luminaires
            print(f"\nFound {len(luminaires)} luminaire(s):")
            for i, lum in enumerate(luminaires):
                print(f"  [{i}] IP: {lum.ip_address} | Serial: {lum.serial_number}")
            
            # Get user choice if not provided
            if choice is None:
                user_input = input(
                    f"\nEnter luminaire index (0-{len(luminaires)-1}) or 'all' to connect to all: "
                )
                choice = 'all' if user_input.lower() == 'all' else int(user_input)
            
            # Connect to all luminaires
            if str(choice).lower() == 'all':
                print(f"\nConnecting to all luminaires...")
                return luminaires  # Already connected from discovery
            
            # Connect to specific luminaire by index
            else:
                index = int(choice)
                if index < 0 or index >= len(luminaires):
                    print(f"Invalid index: {index}")
                    return None
                
                selected_lum = luminaires[index]
                print(f"-> Selected {selected_lum.ip_address}\n")
                return selected_lum
        
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def connect_by_ip(ip_address: str, port: int = None) -> Optional[Luminaire]:
        """
        Connect to a specific luminaire by IP address.
        
        Args:
            ip_address: IP address of the luminaire (e.g., "192.168.1.100")
            port: Port number (optional, uses default if None)
        
        Returns:
            Luminaire object if connection successful, None otherwise
        """
        try:
            print(f"Trying to connect to luminaire at {ip_address}...")
            
            luminaire = TelelumenAPI.connect(ip_address)
            
            print(f"-> Connection established to {ip_address} / {luminaire.serial_number}\n")
            return luminaire
        
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def connect_by_serial(serial_number: str) -> Optional[Luminaire]:
        """
        Connect to a specific luminaire by its serial number.
        First discovers all luminaires, then connects to the one with matching serial.
        
        Args:
            serial_number: Serial number of the luminaire
        
        Returns:
            Luminaire object if connection successful, None otherwise
        """
        try:
            print(f"Searching for luminaire with serial number: {serial_number}")
            luminaires = Telelumen.discover_luminaires()
            
            if not luminaires:
                print("No luminaires found")
                return None
            
            # Search for luminaire with matching serial number
            for lum in luminaires:
                if lum.serial_number == serial_number:
                    print(f"Found luminaire at {lum.ip_address}")
                    print("-> Connection established\n")
                    return lum
            
            print(f"-> No luminaire found with serial number: {serial_number}\n")
            return None
        
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def disconnect(lum: Luminaire) -> bool:
        """
        Disconnect from a single luminaire.
        
        Args:
            lum: Luminaire object
        
        Returns:
            True on success, False on failure
        """
        try:
            return TelelumenAPI.disconnect(lum)
        except Exception as e:
            print(f"Disconnect failed: {e}")
            return False
    
    @staticmethod
    def get_temperature(lum: Luminaire) -> Optional[float]:
        """
        Get the temperature of a single luminaire.
        
        Args:
            lum: Luminaire object
        
        Returns:
            Temperature in Celsius, or None if not available
        """
        try:
            return lum.get_temperature()
        except Exception as e:
            print(f"Failed to get temperature: {e}")
            return None
    
    @staticmethod
    def light_off(lum: Luminaire) -> bool:
        """
        Turn off a single luminaire by setting all drive levels to 0.
        
        Args:
            lum: Luminaire object
        
        Returns:
            True on success, False on failure
        """
        try:
            return TelelumenAPI.light_off(lum)
        except Exception as e:
            print(f"Failed to turn off light: {e}")
            return False
    
    @staticmethod
    def light_on(lum: Luminaire, brightness: float = 1.0) -> bool:
        """
        Turn on a single luminaire by setting all drive levels to the specified brightness.
        
        Args:
            lum: Luminaire object
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            True on success, False on failure
        """
        try:
            return TelelumenAPI.light_on(lum, brightness)
        except Exception as e:
            print(f"Failed to turn on light: {e}")
            return False
    
    @staticmethod
    def set_brightness(lum: Luminaire, brightness: float) -> bool:
        """
        Set the brightness of a single luminaire by adjusting all drive levels.
        
        Args:
            lum: Luminaire object
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            True on success, False on failure
        """
        try:
            return TelelumenAPI.set_brightness(lum, brightness)
        except Exception as e:
            print(f"Failed to set brightness: {e}")
            return False
    
    @staticmethod
    def from13to24(vec: List[float]) -> List[float]:
        """
        Convert 13-channel vector to 24-channel vector.
        
        Channel mapping:
        [UV1, UV2, V1, V2, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, DR1, DR2, FR1, FR2, FR3, IR1, IR2]
        
        Args:
            vec: 13-element list of channel values
        
        Returns:
            24-element list with proper channel mapping
        """
        return [
            0.0, 0.0, 0.0, 0.0,  # UV1, UV2, V1, V2
            vec[0], vec[1],       # RB1, RB2
            vec[2], vec[3],       # B1, B2
            vec[4],               # C
            vec[5], vec[6],       # G1, G2
            vec[7],               # L
            vec[8],               # PC-A
            vec[9],               # A
            vec[10],              # OR
            vec[11], vec[12],     # R1, R2
            0.0, 0.0,             # DR1, DR2
            0.0, 0.0, 0.0,        # FR1, FR2, FR3
            0.0, 0.0              # IR1, IR2
        ]
    
    @staticmethod
    def set_intensities(lum: Luminaire, intensities: List[float]) -> bool:
        """
        Set the intensities of a single luminaire's channels using 13-channel input.
        
        Args:
            lum: Luminaire object
            intensities: List of 13 intensity levels (0.0 to 1.0) for each channel
        
        Returns:
            True on success, False on failure
        """
        try:
            drive_levels = Telelumen.from13to24(intensities)
            return lum.set_drive_levels(drive_levels)
        except Exception as e:
            print(f"Failed to set intensities: {e}")
            return False
    
    @staticmethod
    def get_info(lum: Luminaire) -> dict:
        """
        Get comprehensive information about a single luminaire.
        
        Args:
            lum: Luminaire object
        
        Returns:
            Dictionary with device information
        """
        try:
            return TelelumenAPI.get_info(lum)
        except Exception as e:
            print(f"Failed to get info: {e}")
            return {}
    
    # ========================================================================
    # MULTI-LUMINAIRE OPERATIONS
    # ========================================================================
    
    @staticmethod
    def disconnect_all(luminaires: List[Luminaire]) -> int:
        """
        Disconnect from multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
        
        Returns:
            Number of successfully disconnected luminaires
        """
        count = 0
        for lum in luminaires:
            if Telelumen.disconnect(lum):
                count += 1
        return count
    
    @staticmethod
    def get_temperature_all(luminaires: List[Luminaire]) -> List[Optional[float]]:
        """
        Get temperature from multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
        
        Returns:
            List of temperature values (None for luminaires without temperature support)
        """
        return [Telelumen.get_temperature(lum) for lum in luminaires]
    
    @staticmethod
    def light_off_all(luminaires: List[Luminaire]) -> int:
        """
        Turn off multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
        
        Returns:
            Number of successfully turned off luminaires
        """
        count = 0
        for lum in luminaires:
            if Telelumen.light_off(lum):
                count += 1
        return count
    
    @staticmethod
    def light_on_all(luminaires: List[Luminaire], brightness: float = 1.0) -> int:
        """
        Turn on multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            Number of successfully turned on luminaires
        """
        count = 0
        for lum in luminaires:
            if Telelumen.light_on(lum, brightness):
                count += 1
        return count
    
    @staticmethod
    def set_brightness_all(luminaires: List[Luminaire], brightness: float) -> int:
        """
        Set brightness for multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            Number of successfully updated luminaires
        """
        count = 0
        for lum in luminaires:
            if Telelumen.set_brightness(lum, brightness):
                count += 1
        return count
    
    @staticmethod
    def set_intensities_all(luminaires: List[Luminaire], intensities: List[float]) -> int:
        """
        Set intensities for multiple luminaires using 13-channel input.
        
        Args:
            luminaires: List of Luminaire objects
            intensities: List of 13 intensity levels (0.0 to 1.0) for each channel
        
        Returns:
            Number of successfully updated luminaires
        """
        count = 0
        for lum in luminaires:
            if Telelumen.set_intensities(lum, intensities):
                count += 1
        return count
    
    @staticmethod
    def get_info_all(luminaires: List[Luminaire]) -> List[dict]:
        """
        Get information from multiple luminaires.
        
        Args:
            luminaires: List of Luminaire objects
        
        Returns:
            List of dictionaries with device information
        """
        return [Telelumen.get_info(lum) for lum in luminaires]


    @staticmethod
    def reset(luminaire : Luminaire) -> bool:
        """
        Reset a single luminaire to factory settings.
        
        Args:
            luminaire: Luminaire object
        
        Returns:
            True on success, False on failure
        """
        try:
            return luminaire.reset()
        except Exception as e:
            print(f"Failed to reset luminaire: {e}")
            return False
    
    @staticmethod
    def reset_all(luminaires : List[Luminaire]) -> bool:
        """
        Reset a single luminaire to factory settings.
        
        Args:
            luminaire: Luminaire object
        
        Returns:
            True on success, False on failure
        """
        try:
            for luminaire in luminaires:
                luminaire.reset()
            return True
        except Exception as e:
            print(f"Failed to reset luminaire: {e}")
            return False



if __name__ == "__main__":
    # Example usage
    print("Telelumen Wrapper - Clean API Version\n")
    
    # Connect to luminaire(s)
    result = Telelumen.connect_from_list()
    
    if result is not None:
        # Handle single luminaire
        if not isinstance(result, list):
            print("\n=== Testing Single Luminaire ===")
            lum = result
            
            # Get info
            info = Telelumen.get_info(lum)
            print(f"Type: {info.get('luminaire_type')}")
            print(f"Firmware: {info.get('firmware_version')}")
            
            # Test light control
            # print("\nTurning on at 50%...")
            # Telelumen.light_on(lum, brightness=0.5)
            
            # import time
            # time.sleep(2)
            
            print("Turning off...")
            Telelumen.light_off(lum)
            
            # Disconnect
            print("\n=== Disconnecting ===")
            Telelumen.disconnect(lum)
            print("Done!")
        
        # Handle multiple luminaires
        else:
            print("\n=== Testing Multiple Luminaires ===")
            luminaires = result
            
            # Get info from all
            infos = Telelumen.get_info_all(luminaires)
            for info in infos:
                print(f"  {info.get('ip_address')}: {info.get('luminaire_type')}")
            
            # Test light control on all
            print("\nTurning on all at 50%...")
            # success_count = Telelumen.light_on_all(luminaires, brightness=0.5)
            # print(f"  -> {success_count}/{len(luminaires)} succeeded")
            
            # import time
            # time.sleep(2)
            
            print("\nTurning off all...")
            success_count = Telelumen.light_on_all(luminaires)
            print(f"  -> {success_count}/{len(luminaires)} succeeded")
            
            # Disconnect all
            print("\n=== Disconnecting All ===")
            count = Telelumen.disconnect_all(luminaires)
            print(f"Disconnected {count}/{len(luminaires)} luminaires")
            print("Done!")
