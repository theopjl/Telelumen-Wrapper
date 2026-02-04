"""
Day Simulation Script - Multi-Model Support
============================================
Supports both 8-channel Standard Luminaires and 24-channel Light Replicators.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from telelumen_wrapper_clean import Telelumen
from api.telelumen_api import LuminaireType


# ============================================================================
# SIMULATION CONFIGURATION
# ============================================================================

TOTAL_DURATION = 60  # seconds
INTERPOLATION_STEPS = 16


# ============================================================================
# LIGHTING PRESETS - 8 CHANNEL (Standard Luminaire)
# ============================================================================

# 8-channel mapping (estimated - verify with your hardware):
# [Royal Blue, Blue, Cyan, Green, Yellow/Lime, Amber, Orange, Red]

PRESETS_8CH = {
    # Night - Very dark, cool blue tones (moonlight)
    "night": [0.02, 0.03, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0],
    
    # Dawn - Deep blue gradually warming (2000-3000K)
    "dawn_start": [0.25, 0.35, 0.15, 0.02, 0.0, 0.05, 0.08, 0.02],
    "dawn_mid": [0.15, 0.25, 0.18, 0.08, 0.05, 0.15, 0.25, 0.12],
    "dawn_end": [0.08, 0.15, 0.12, 0.18, 0.15, 0.35, 0.50, 0.35],
    
    # Sunrise - Warm orange/yellow (2500-4000K)
    "sunrise_start": [0.02, 0.05, 0.05, 0.25, 0.30, 0.60, 0.85, 0.70],
    "sunrise_mid": [0.0, 0.02, 0.08, 0.40, 0.50, 0.70, 0.90, 0.75],
    "sunrise_end": [0.0, 0.05, 0.15, 0.55, 0.65, 0.75, 0.80, 0.70],
    
    # Morning - Bright cool white (5500-6500K)
    "morning": [0.15, 0.20, 0.40, 0.75, 0.85, 0.70, 0.50, 0.55],
    "afternoon": [0.12, 0.18, 0.38, 0.80, 0.90, 0.75, 0.55, 0.60],
    
    # Golden Hour - Warm golden tones, low blue (2000-3000K)
    "golden_hour_start": [0.0, 0.02, 0.10, 0.55, 0.65, 0.85, 0.95, 0.90],
    "golden_hour_mid": [0.0, 0.0, 0.05, 0.40, 0.50, 0.90, 1.0, 0.95],
    "golden_hour_end": [0.0, 0.0, 0.02, 0.30, 0.40, 0.85, 0.95, 0.90],
    
    # Sunset - Deep orange to red (1500-2500K)
    "sunset_start": [0.0, 0.0, 0.02, 0.20, 0.30, 0.75, 0.90, 0.85],
    "sunset_mid": [0.0, 0.0, 0.0, 0.08, 0.15, 0.60, 0.85, 0.90],
    "sunset_end": [0.05, 0.08, 0.05, 0.02, 0.05, 0.40, 0.65, 0.70],
    
    # Blue Hour - Deep blue twilight
    "blue_hour_start": [0.25, 0.40, 0.20, 0.05, 0.02, 0.12, 0.20, 0.15],
    "blue_hour_mid": [0.30, 0.45, 0.22, 0.03, 0.0, 0.05, 0.10, 0.08],
    "blue_hour_end": [0.20, 0.30, 0.12, 0.02, 0.0, 0.02, 0.05, 0.03],
    
    # Evening - Returning to night
    "evening": [0.08, 0.12, 0.05, 0.0, 0.0, 0.0, 0.02, 0.0],
}


# ============================================================================
# LIGHTING PRESETS - 24 CHANNEL (Light Replicator)
# ============================================================================

# 24-channel mapping includes UVA, visible spectrum, and NIR
# Exact mapping depends on your Light Replicator model
# This is a general template - adjust based on your hardware specs

PRESETS_24CH = {
    # Night - Very dark, cool blue moonlight (minimal intensity)
    "night": [
        # UVA (365-400nm) - off
        0.0, 0.0,
        # Violet-Blue (400-480nm) - minimal blue
        0.01, 0.02, 0.03, 0.03,
        # Blue-Cyan (480-510nm) - slight blue
        0.02, 0.02,
        # Green (510-560nm) - off
        0.0, 0.0, 0.0, 0.0,
        # Yellow-Orange (560-620nm) - off
        0.0, 0.0, 0.0, 0.0,
        # Red (620-700nm) - off
        0.0, 0.0, 0.0, 0.0,
        # NIR (700-1000nm) - off
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Dawn Start - Deep blue with hints of warm (2000-2500K)
    "dawn_start": [
        0.0, 0.0,
        0.18, 0.25, 0.35, 0.35,
        0.15, 0.15,
        0.02, 0.02, 0.0, 0.0,
        0.0, 0.02, 0.05, 0.08,
        0.02, 0.02, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Dawn Mid - Blue reducing, warm increasing (2500-3000K)
    "dawn_mid": [
        0.0, 0.0,
        0.12, 0.15, 0.25, 0.25,
        0.18, 0.18,
        0.05, 0.08, 0.08, 0.05,
        0.10, 0.15, 0.20, 0.25,
        0.12, 0.12, 0.08, 0.08,
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Dawn End - Warm colors dominating (3000-4000K)
    "dawn_end": [
        0.0, 0.0,
        0.05, 0.08, 0.15, 0.15,
        0.12, 0.12,
        0.15, 0.18, 0.18, 0.15,
        0.30, 0.35, 0.45, 0.50,
        0.35, 0.35, 0.30, 0.30,
        0.02, 0.02, 0.02, 0.02
    ],
    
    # Sunrise Start - Orange/yellow dominant (2500-3500K)
    "sunrise_start": [
        0.0, 0.0,
        0.0, 0.02, 0.05, 0.05,
        0.05, 0.05,
        0.20, 0.25, 0.30, 0.30,
        0.55, 0.60, 0.75, 0.85,
        0.70, 0.70, 0.65, 0.65,
        0.05, 0.05, 0.08, 0.08
    ],
    
    # Sunrise Mid - Bright warm (3500-4500K)
    "sunrise_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.02, 0.02,
        0.08, 0.08,
        0.35, 0.40, 0.50, 0.50,
        0.65, 0.70, 0.80, 0.90,
        0.75, 0.75, 0.70, 0.70,
        0.08, 0.08, 0.10, 0.10
    ],
    
    # Sunrise End - Transitioning to daylight (4500-5500K)
    "sunrise_end": [
        0.01, 0.01,
        0.0, 0.05, 0.05, 0.08,
        0.15, 0.15,
        0.50, 0.55, 0.65, 0.65,
        0.70, 0.75, 0.75, 0.80,
        0.70, 0.70, 0.65, 0.65,
        0.10, 0.10, 0.12, 0.12
    ],
    
    # Morning - Bright cool white daylight (5500-6500K)
    "morning": [
        0.02, 0.02,  # UVA for realism
        0.12, 0.15, 0.20, 0.20,
        0.35, 0.40,
        0.70, 0.75, 0.80, 0.85,
        0.80, 0.85, 0.70, 0.70,
        0.55, 0.55, 0.50, 0.50,
        0.05, 0.05, 0.08, 0.08
    ],
    
    # Afternoon - Bright slightly warm (5000-6000K)
    "afternoon": [
        0.03, 0.03,  # Peak UVA (midday)
        0.10, 0.12, 0.18, 0.18,
        0.35, 0.38,
        0.75, 0.80, 0.85, 0.90,
        0.85, 0.90, 0.75, 0.75,
        0.60, 0.60, 0.55, 0.55,
        0.08, 0.08, 0.12, 0.12
    ],
    
    # Golden Hour Start - Warm golden (2500-3500K)
    "golden_hour_start": [
        0.01, 0.01,
        0.0, 0.0, 0.02, 0.05,
        0.08, 0.10,
        0.50, 0.55, 0.60, 0.65,
        0.80, 0.85, 0.90, 0.95,
        0.90, 0.90, 0.85, 0.85,
        0.12, 0.12, 0.15, 0.15
    ],
    
    # Golden Hour Mid - Peak warm golden (2000-3000K)
    "golden_hour_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.02,
        0.05, 0.05,
        0.35, 0.40, 0.50, 0.50,
        0.85, 0.90, 0.95, 1.0,
        0.95, 0.95, 0.90, 0.90,
        0.15, 0.15, 0.20, 0.20
    ],
    
    # Golden Hour End - Transitioning to sunset (2000-2800K)
    "golden_hour_end": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.02, 0.02,
        0.25, 0.30, 0.40, 0.40,
        0.80, 0.85, 0.90, 0.95,
        0.90, 0.90, 0.85, 0.85,
        0.18, 0.18, 0.22, 0.22
    ],
    
    # Sunset Start - Deep warm orange (1800-2500K)
    "sunset_start": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.02, 0.02,
        0.15, 0.20, 0.30, 0.30,
        0.70, 0.75, 0.85, 0.90,
        0.85, 0.85, 0.80, 0.80,
        0.15, 0.15, 0.18, 0.18
    ],
    
    # Sunset Mid - Deep orange to red (1500-2000K)
    "sunset_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.05, 0.08, 0.15, 0.15,
        0.55, 0.60, 0.75, 0.85,
        0.90, 0.90, 0.85, 0.85,
        0.12, 0.12, 0.15, 0.15
    ],
    
    # Sunset End - Fading to blue hour (1500-2000K)
    "sunset_end": [
        0.0, 0.0,
        0.02, 0.05, 0.08, 0.08,
        0.05, 0.05,
        0.02, 0.02, 0.05, 0.05,
        0.35, 0.40, 0.55, 0.65,
        0.70, 0.70, 0.65, 0.65,
        0.08, 0.08, 0.10, 0.10
    ],
    
    # Blue Hour Start - Deep blue twilight
    "blue_hour_start": [
        0.0, 0.0,
        0.20, 0.25, 0.40, 0.40,
        0.20, 0.20,
        0.03, 0.05, 0.05, 0.05,
        0.08, 0.10, 0.15, 0.20,
        0.15, 0.15, 0.12, 0.12,
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Blue Hour Mid - Peak deep blue
    "blue_hour_mid": [
        0.0, 0.0,
        0.25, 0.30, 0.45, 0.45,
        0.22, 0.22,
        0.02, 0.03, 0.03, 0.03,
        0.03, 0.05, 0.08, 0.10,
        0.08, 0.08, 0.05, 0.05,
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Blue Hour End - Fading to night
    "blue_hour_end": [
        0.0, 0.0,
        0.15, 0.20, 0.30, 0.30,
        0.12, 0.12,
        0.01, 0.02, 0.02, 0.02,
        0.02, 0.02, 0.05, 0.05,
        0.03, 0.03, 0.02, 0.02,
        0.0, 0.0, 0.0, 0.0
    ],
    
    # Evening - Returning to night darkness
    "evening": [
        0.0, 0.0,
        0.05, 0.08, 0.12, 0.12,
        0.05, 0.05,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.02, 0.02,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
}


# ============================================================================
# TIME ALLOCATION (same for both models)
# ============================================================================

TIME_ALLOCATION = {
    "night_start":       (0.02, 0.01),
    "dawn_start":        (0.04, 0.02),
    "dawn_mid":          (0.04, 0.02),
    "dawn_end":          (0.03, 0.01),
    "sunrise_start":     (0.04, 0.02),
    "sunrise_mid":       (0.04, 0.02),
    "sunrise_end":       (0.03, 0.01),
    "morning":           (0.05, 0.08),
    "afternoon":         (0.04, 0.08),
    "golden_hour_start": (0.04, 0.02),
    "golden_hour_mid":   (0.04, 0.02),
    "golden_hour_end":   (0.03, 0.01),
    "sunset_start":      (0.04, 0.02),
    "sunset_mid":        (0.04, 0.02),
    "sunset_end":        (0.03, 0.01),
    "blue_hour_start":   (0.04, 0.02),
    "blue_hour_mid":     (0.04, 0.02),
    "blue_hour_end":     (0.03, 0.01),
    "evening":           (0.04, 0.03),
    "night_end":         (0.03, 0.02),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_presets_for_luminaire(lum):
    """
    Get the appropriate preset dictionary for a luminaire.
    
    Args:
        lum: Luminaire object
    
    Returns:
        Dictionary of presets (8-channel or 24-channel)
    """
    if lum.luminaire_type == LuminaireType.LIGHT_REPLICATOR:
        return PRESETS_24CH
    else:
        return PRESETS_8CH


def interpolate_preset(preset1, preset2, factor):
    """Interpolate between two presets."""
    return [p1 + (p2 - p1) * factor for p1, p2 in zip(preset1, preset2)]


def smooth_transition(lum, from_preset, to_preset, duration, steps=None):
    """Smoothly transition between presets."""
    if steps is None:
        steps = INTERPOLATION_STEPS
    
    step_duration = duration / steps
    
    for i in range(steps + 1):
        t = i / steps
        factor = t * t * (3.0 - 2.0 * t)  # Ease-in-out
        
        current_preset = interpolate_preset(from_preset, to_preset, factor)
        
        # Set drive levels directly (bypass wrapper's 13-to-24 conversion)
        lum.set_drive_levels(current_preset)
        
        if i < steps:
            time.sleep(step_duration)


# ============================================================================
# MAIN SIMULATION
# ============================================================================

def run_day_simulation_per_luminaire(luminaires):
    """
    Run day simulation with per-luminaire preset selection.
    Each luminaire uses presets appropriate for its channel count.
    """
    if not isinstance(luminaires, list):
        luminaires = [luminaires]
    
    # Build sequence
    sequence = []
    for phase_name, (trans_pct, hold_pct) in TIME_ALLOCATION.items():
        # Extract base preset name (remove _start, _mid, _end, etc.)
        base_name = phase_name.replace('_start', '').replace('_mid', '').replace('_end', '')
        
        trans_dur = TOTAL_DURATION * trans_pct
        hold_dur = TOTAL_DURATION * hold_pct
        
        sequence.append((f"{base_name} (transition)", phase_name, "transition", trans_dur))
        if hold_dur > 0.05:  # Only add hold if meaningful
            sequence.append((f"{base_name} (hold)", phase_name, "hold", hold_dur))
    
    print("\n" + "="*70)
    print(f"DAY SIMULATION - Multi-Model Support")
    print("="*70)
    print(f"\nLuminaires: {len(luminaires)}")
    for i, lum in enumerate(luminaires):
        ch_count = 24 if lum.luminaire_type == LuminaireType.LIGHT_REPLICATOR else 8
        print(f"  [{i+1}] {lum.ip_address} - {ch_count} channels")
    print(f"\nTotal duration: {TOTAL_DURATION}s")
    print(f"Phases: {len(sequence)}")
    print(f"Interpolation steps: {INTERPOLATION_STEPS}\n")
    
    # Track previous presets per luminaire
    prev_presets = [None] * len(luminaires)
    
    start_time = time.time()
    
    for phase_idx, (desc, preset_name, phase_type, duration) in enumerate(sequence):
        print(f"[{phase_idx+1:2d}/{len(sequence)}] {desc:40s} {duration:5.2f}s")
        
        if phase_type == "transition":
            # Transition each luminaire independently
            for lum_idx, lum in enumerate(luminaires):
                presets = get_presets_for_luminaire(lum)
                current_preset = presets.get(preset_name, presets["morning"])  # Fallback
                
                if prev_presets[lum_idx] is not None:
                    smooth_transition(lum, prev_presets[lum_idx], current_preset, duration)
                else:
                    # Set drive levels directly (bypass wrapper conversion)
                    lum.set_drive_levels(current_preset)
                    time.sleep(duration)
                
                prev_presets[lum_idx] = current_preset
        
        else:  # hold
            time.sleep(duration)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Simulation complete! Elapsed: {elapsed:.1f}s")
    print(f"{'='*70}\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("Day Simulation - Multi-Model Support")
    print("=" * 70)
    
    result = Telelumen.connect_from_list()
    
    if result is None:

        print("Failed to connect")
        sys.exit(1)
    
    try:
        run_day_simulation_per_luminaire(result)
        
        print("Returning to neutral state...")
        if isinstance(result, list):
            Telelumen.light_on_all(result, brightness=0.5)
        else:
            Telelumen.light_on(result, brightness=0.5)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nDisconnecting...")
        if isinstance(result, list):
            count = Telelumen.disconnect_all(result)
            print(f"Disconnected {count}/{len(result)}")
        else:
            Telelumen.disconnect(result)
        print("Done!")