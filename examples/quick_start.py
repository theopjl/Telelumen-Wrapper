import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import api.api_tng as api
from telelumen_wrapper import Telelumen

lums = Telelumen.discover_luminaires()
if (lums is not None) and (len(lums) > 0):
    lum = lums[0]
    if lum is not None:

        # Connect to the first discovered luminaire
        print("\nConnected to luminaire:")
        print(f"  IP: {lum.address} | Serial: {lum.get_luminaire_serial_number()}")

        # Retrieve and display luminaire information
        serial = lum.get_luminaire_serial_number()
        version = lum.get_version()
        print(f"Serial: {serial}, Version: {version}")

        # Set drive levels to 50% for all channels
        #drive_levels = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # 50% brightness
        #lum.set_drive_levels(drive_levels)
        lum.go_dark()

        Telelumen.set_brightness(lum, 0.0)
        print("Set drive levels to 50% for all channels.")

        # Disconnect from the luminaire
        Telelumen.disconnect(lum)

    else:
        print("Failed to connect to the selected luminaire.")