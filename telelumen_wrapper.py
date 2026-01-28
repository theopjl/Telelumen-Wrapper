"""
Created on Tuesday 27 January 2026

@author: Théo Poujol

info:
    Telelumen wrapper
"""

import api_tng as api

def discover_luminaires() -> list | None:
    try :
        print("=== Discovering luminaires ===")

        lum_list = api.discover()
        
        if (len(lum_list) == 0 ) : 
            print("No luminaires found")
            return None    
        
        return lum_list
    
    except :
        return None

def connect_luminaire_from_list(choice=None) -> api.Luminaire | list | None:
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
        lum_list = discover_luminaires()
        
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
            user_input = input("\nEnter luminaire index (0-" + str(len(lum_list)-1) + ") or 'all' to connect to all: ")
            if user_input.lower() == 'all':
                choice = 'all'
            else:
                choice = int(user_input)
        
        # Connect to all luminaires
        if choice == 'all' or (isinstance(choice, str) and choice.lower() == 'all'):
            print(f"\nConnecting to all luminaires...")
            connected_luminaires = []
            
            for i, lum in enumerate(lum_list):
                serial = lum.get_luminaire_serial_number()
                print(f"\n[{i}] Connecting to {lum.address} / {serial}")
                
                result = api.openLuminaire(lum.address, api.luminairePort)
                if result == 0:
                    print(f"  -> Connected established")
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


def connect_luminaire_by_ip(ip_address, port=None):
    """
    Connect to a specific luminaire by IP address.
    
    Args:
        ip_address (str): IP address of the luminaire (e.g., "192.168.1.100")
        port (int, optional): Port number. If None, uses default luminaire port.
    
    Returns:
        Luminaire object if connection successful, None otherwise
    """
    try:
        if port is None:
            port = api.luminairePort
        
        print(f"Trying to connect to luminaire at {ip_address}:{port}")
        
        result = api.openLuminaire(ip_address, port)
        if result == 0:
            # Create a Luminaire object for this connection
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


def connect_luminaire_by_serial(serial_number):
    """
    Connect to a specific luminaire by its serial number.
    First discovers all luminaires, then connects to the one with matching serial.
    
    Args:
        serial_number (str): Serial number of the luminaire
    
    Returns:
        Luminaire object if connection successful, None otherwise
    """
    try:
        print(f"Searching for luminaire with serial number: {serial_number}")
        lum_list = discover_luminaires()
        
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
    
def disconnect_telelumen(lum) -> bool: 
    try :
        if (isinstance (lum, list)) :
            for l in lum :
                api.closeLuminaire(l.address)
        
        api.closeLuminaire(lum.address)
        print("-> Connection closed for " + l.address)
        return True
    except :
        print("Connection not closed \n")
        return False
    
def from13to24(vec):
    #[UV1, UV2, V1, V2, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, DR1, DR2, FR1, FR2, FR3, IR1, IR2]

    return [.0, .0, .0, .0, vec[0], vec[1], vec[2], vec[3], vec[4], vec[5], vec[6], vec[7], vec[8], vec[9] , vec[10], vec[11], vec[12], .0, .0, .0, .0, .0, .0, .0]
    
def light(lum, vec):
    result=lum.set_drive_levels(vec)        
    if (result != 0):
        print("TELELUMEN ERROR : " + str(result))
    return result

def light_off(lum):
    
    vec = [ .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0 , .0, .0, .0, .0, .0, .0, .0, .0, .0, .0 ]
    lum.set_drive_levels(vec)

def get_temperature(lum):
    s = lum.get_temperature()
    return float(s)

if __name__ == "__main__":
    
    # Example 1: Discover luminaires
    discover_luminaires()