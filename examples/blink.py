import sys
import time

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
        
        try :
            if not isinstance(result, list):
                lum = result

                while True:
                    print("Turning on...")
                    Telelumen.light_off(lum)
                    time.sleep(1)
                    print("Turning off...")
                    Telelumen.light_on(lum)
                    time.sleep(1)

            else:
                print("\n=== Testing Multiple Luminaires ===")
                luminaires = result


                while True:
                    print("Turning on...")
                    Telelumen.light_off_all(luminaires)
                    time.sleep(1)
                    print("Turning off...")
                    Telelumen.light_on_all(luminaires)
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\nInterrupted by user, disconnecting...")
            if isinstance(result, list):
                luminaires = result
                count = Telelumen.disconnect_all(luminaires)
                print(f"Disconnected {count}/{len(luminaires)} luminaires")
            else:
                lum = result
                Telelumen.disconnect(lum)
                print("Disconnected")