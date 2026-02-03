"""
Created on Tuesday 27 January 2026
Last modified on Monday 02 February 2026

@author: Théo Poujol

info:
    Telelumen Wrapper to facilitate luminaire discovery and connection.
"""

import api.api_tng as api


class Telelumen:
    """Wrapper class for Telelumen luminaire operations."""
    
    @staticmethod
    def discover_luminaires() -> list | None:
        """Discover all available luminaires on the network."""
        try:
            print("=== Discovering luminaires ===")
            lum_list = api.discover()
            
            if len(lum_list) == 0:
                print("No luminaires found")
                return None    
            
            print(f"-> Found {len(lum_list)} luminaire(s)\n")
            for lum in lum_list:
                serial = lum.get_electronic_serial_number()
                print(f"  IP: {lum.address} | Serial: {serial}")    
            return lum_list
        except:
            return None
    
    @staticmethod
    def connect_from_list(choice=None) -> api.Luminaire | list | None:
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
            - None or empty list if connection failed
        """
        try:
            lum_list = Telelumen.discover_luminaires()
            
            if lum_list is None or len(lum_list) == 0:
                print("No luminaires found")
                return None
            
            # Display list of luminaires
            print(f"\nFound {len(lum_list)} luminaire(s):")
            for i, lum in enumerate(lum_list):
                serial = lum.get_luminaire_serial_number()
                print(f"  [{i}] IP: {lum.address} | Serial: {serial}")
            
            # Get user choice if not provided
            if choice is None:
                user_input = input(f"\nEnter luminaire index (0-{len(lum_list)-1}) or 'all' to connect to all: ")
                choice = 'all' if user_input.lower() == 'all' else int(user_input)
            
            # Connect to all luminaires
            if str(choice).lower() == 'all':
                print(f"\nConnecting to all luminaires...")
                connected_luminaires = []
                
                for i, lum in enumerate(lum_list):
                    serial = lum.get_luminaire_serial_number()
                    print(f"\n[{i}] Connecting to {lum.address} / {serial}")
                    
                    result = api.openLuminaire(lum.address, api.luminairePort)
                    if result == 0:
                        print(f"  -> Connection established")
                        connected_luminaires.append(lum)
                    else:
                        print(f"  -> Connection failed")
                
                print(f"\n-> Successfully connected to {len(connected_luminaires)}/{len(lum_list)} luminaire(s)\n")
                return connected_luminaires
            
            # Connect to specific luminaire by index
            else:
                index = int(choice)
                if index < 0 or index >= len(lum_list):
                    print(f"Invalid index: {index}")
                    return None
                
                selected_lum = lum_list[index]
                print(f"\nTrying to connect to {selected_lum.address} / {selected_lum.get_luminaire_serial_number()}")
                
                result = api.openLuminaire(selected_lum.address, api.luminairePort)
                if result == 0:
                    print("-> Connection established\n")
                    return selected_lum
                else:
                    print("-> Connection failed\n")
                    return None
                
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def connect_by_ip(ip_address: str, port: int = None) -> api.Luminaire | None:
        """
        Connect to a specific luminaire by IP address.
        
        Args:
            ip_address: IP address of the luminaire (e.g., "192.168.1.100")
            port: Port number. If None, uses default luminaire port.
        
        Returns:
            Luminaire object if connection successful, None otherwise
        """
        try:
            if port is None:
                port = api.luminairePort
            
            print(f"Trying to connect to luminaire at {ip_address}:{port}")
            
            result = api.openLuminaire(ip_address, port)
            if result == 0:
                lum = api.Luminaire(ip_address)
                serial = lum.get_luminaire_serial_number()
                print(f"-> Connection established to {ip_address} / {serial}\n")
                return lum
            else:
                print(f"-> Connection failed to {ip_address}\n")
                return None
                
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def connect_by_serial(serial_number: str) -> api.Luminaire | None:
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
            lum_list = Telelumen.discover_luminaires()
            
            if lum_list is None or len(lum_list) == 0:
                print("No luminaires found")
                return None
            
            # Search for luminaire with matching serial number
            for lum in lum_list:
                lum_serial = lum.get_luminaire_serial_number()
                if lum_serial == serial_number:
                    print(f"Found luminaire at {lum.address}")
                    print(f"Trying to connect to {lum.address} / {serial_number}")
                    
                    result = api.openLuminaire(lum.address, api.luminairePort)
                    if result == 0:
                        print("-> Connection established\n")
                        return lum
                    else:
                        print("-> Connection failed\n")
                        return None
            
            print(f"-> No luminaire found with serial number: {serial_number}\n")
            return None
            
        except Exception as e:
            print(f"-> Connection failed: {e}\n")
            return None
    
    @staticmethod
    def disconnect(lum: api.Luminaire | list) -> int:
        """
        Disconnect from luminaire(s).
        
        Args:
            lum: Single Luminaire object or list of Luminaire objects
        
        Returns:
            0 on success, -1 on failure
        """
        try:
            if isinstance(lum, list):
                return api.closeList(lum)
            return api.closeLuminaire(lum.address)
        except:
            return -1
        
    @staticmethod
    def get_temperature(lum: api.Luminaire) -> float | None:
        """
        Get the temperature of the luminaire.
        
        Args:
            lum: Luminaire object
        
        Returns:
            Temperature in Celsius if successful, None otherwise
        """
        try:
            temp = lum.get_temperature()
            return temp
        except:
            return None

    @staticmethod
    def light_off(lum: api.Luminaire) -> int | None :
        """
        Turn off the luminaire by setting all drive levels to 0.
        
        Args:
            lum: Luminaire object
        
        Returns:
            0 on success, -1 on failure
        """
        try:
            return lum.go_dark()
        except:
            return None
        
    @staticmethod
    def light_on(lum: api.Luminaire, brightness: float = 1.0) -> int | None:
        """
        Turn on the luminaire by setting all drive levels to the specified brightness.
        
        Args:
            lum: Luminaire object
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            0 on success, -1 on failure
        """
        try:
            num_channels = lum.get_number_of_channels()
            drive_levels = [brightness] * num_channels
            return lum.set_drive_levels(drive_levels)
        except:
            return None
        
    @staticmethod
    def set_brightness(lum: api.Luminaire, brightness: float) -> int | None:
        """
        Set the brightness of the luminaire by adjusting all drive levels.
        
        Args:
            lum: Luminaire object
            brightness: Brightness level (0.0 to 1.0)
        
        Returns:
            0 on success, -1 on failure
        """
        try:
            num_channels = lum.get_number_of_channels()
            drive_levels = [brightness] * num_channels
            return lum.set_drive_levels(drive_levels)
        except:
            return None
        
    @staticmethod
    def from13to24(vec):
    #[UV1, UV2, V1, V2, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, DR1, DR2, FR1, FR2, FR3, IR1, IR2]

        return [.0, .0, .0, .0, vec[0], vec[1], vec[2], vec[3], vec[4], vec[5], vec[6], vec[7], vec[8], vec[9] , vec[10], vec[11], vec[12], .0, .0, .0, .0, .0, .0, .0]
    
    @staticmethod
    def set_intensities(lum: api.Luminaire, intensities: list) -> int:
        """
        Set the intensities of the luminaire channels.
        
        Args:
            lum: Luminaire object
            intensities: List of intensity levels (0.0 to 1.0) for each channel
        
        Returns:
            0 on success, -1 on failure
        """
        try:
            return lum.set_drive_levels(Telelumen.from13to24(intensities))
        except:
            return -1

if __name__ == "__main__":
    lum = Telelumen.connect_from_list()
    if lum is not None:
        Telelumen.disconnect(lum)