import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telelumen_wrapper_clean import Telelumen

if __name__ == "__main__":
    # Example usage
    print("Telelumen Wrapper - Clean API Version\n")
    
    # Connect to luminaire(s)
    result = Telelumen.connect_from_list()
    
    if result is not None:
        
        if not isinstance(result, list):
            lum = result
            Telelumen.light_on(lum)
            Telelumen.disconnect(lum)
            print("Disconnected")
        # Handle multiple luminaires
        else:
            print("\n=== Testing Multiple Luminaires ===")
            luminaires = result
            success_count = Telelumen.light_on_all(luminaires)
            count = Telelumen.disconnect_all(luminaires)
            print(f"Disconnected {count}/{len(luminaires)} luminaires")
