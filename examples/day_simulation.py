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
# Index:  0           1     2     3      4             5      6       7
#
# Color temperature reminder:
#   ~1500-3000K  → warm (red / orange / amber)   → sunrise, sunset, golden hour
#   ~4000-6500K  → neutral to cool white          → daytime, solar noon
#   ~8000-20000K → cool blue                      → night, blue hour

PRESETS_8CH = {
    # Night phases - progressive transition from deep blue to pre-dawn warmth
    # [Royal Blue, Blue, Cyan, Green, Yellow, Amber, Orange, Red]
    "night":         [0.06, 0.04, 0.01, 0.0,  0.0,  0.0,  0.0,  0.0 ],  # pure deep blue
    "night_start":   [0.06, 0.04, 0.01, 0.0,  0.0,  0.0,  0.0,  0.0 ],  # = night (opening)
    "night_mid":     [0.04, 0.03, 0.0,  0.0,  0.0,  0.01, 0.02, 0.01],  # very first warmth hint
    "night_pre_dawn":[0.01, 0.01, 0.0,  0.0,  0.01, 0.03, 0.06, 0.05],  # bridge to dawn_start
    "night_end":     [0.06, 0.04, 0.01, 0.0,  0.0,  0.0,  0.0,  0.0 ],  # = night (closing)

    # Dawn - First light on the horizon, very dim warm orange (~1500-2500K)
    "dawn_start": [0.0, 0.0, 0.0, 0.0, 0.01, 0.06, 0.12, 0.10],
    "dawn_mid":   [0.0, 0.0, 0.0, 0.01, 0.04, 0.15, 0.28, 0.22],
    "dawn_end":   [0.0, 0.0, 0.01, 0.04, 0.10, 0.30, 0.50, 0.40],

    # Sunrise - Bright warm orange-yellow (~2000-3500K)
    "sunrise_start": [0.0, 0.0, 0.0, 0.03, 0.08, 0.55, 0.80, 0.75],
    "sunrise_mid":   [0.0, 0.0, 0.02, 0.12, 0.25, 0.65, 0.85, 0.65],
    "sunrise_end":   [0.01, 0.03, 0.10, 0.35, 0.55, 0.65, 0.65, 0.45],

    # Morning - Bright neutral warm white (~4500-5500K)
    "morning":   [0.05, 0.10, 0.25, 0.70, 0.80, 0.65, 0.45, 0.30],
    # Solar noon - Bright cool white, peak illumination (~6000-6500K)
    "afternoon": [0.10, 0.18, 0.40, 0.90, 0.90, 0.70, 0.40, 0.25],

    # Golden Hour - Warm deep golden tones (~2000-3500K)
    "golden_hour_start": [0.0, 0.01, 0.04, 0.25, 0.45, 0.80, 0.90, 0.70],
    "golden_hour_mid":   [0.0, 0.0, 0.01, 0.10, 0.28, 0.85, 0.98, 0.82],
    "golden_hour_end":   [0.0, 0.0, 0.0, 0.04, 0.15, 0.78, 0.95, 0.90],

    # Sunset - Deep warm orange to red (~1500-2200K)
    "sunset_start": [0.0, 0.0, 0.0, 0.01, 0.05, 0.60, 0.88, 0.95],
    "sunset_mid":   [0.0, 0.0, 0.0, 0.0, 0.01, 0.35, 0.70, 0.90],
    "sunset_end":   [0.02, 0.04, 0.02, 0.01, 0.01, 0.18, 0.45, 0.60],

    # Blue Hour - Cool deep blue twilight (~8000-15000K, dimming)
    "blue_hour_start": [0.18, 0.28, 0.18, 0.04, 0.01, 0.02, 0.06, 0.04],
    "blue_hour_mid":   [0.22, 0.38, 0.22, 0.02, 0.0, 0.0, 0.02, 0.01],
    "blue_hour_end":   [0.12, 0.20, 0.10, 0.01, 0.0, 0.0, 0.01, 0.0],

    # Evening - Fading back to deep blue-violet night
    "evening": [0.03, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}


# ============================================================================
# LIGHTING PRESETS - 24 CHANNEL (Light Replicator)
# ============================================================================

# 24-channel mapping includes UVA, visible spectrum, and NIR
# Exact mapping depends on your Light Replicator model
# This is a general template - adjust based on your hardware specs
#
# Channel groups (indices):
#   UVA          365-400 nm   ch  0,  1
#   Violet-Blue  400-480 nm   ch  2,  3,  4,  5
#   Blue-Cyan    480-510 nm   ch  6,  7
#   Green        510-560 nm   ch  8,  9, 10, 11
#   Yellow-Orng  560-620 nm   ch 12, 13, 14, 15
#   Red          620-700 nm   ch 16, 17, 18, 19
#   NIR          700-1000 nm  ch 20, 21, 22, 23
#
# Color temperature reminder:
#   ~1500-3000K  → warm (red / orange / amber)   → sunrise, sunset, golden hour
#   ~4000-6500K  → neutral to cool white          → daytime, solar noon
#   ~8000-20000K → cool blue                      → night, blue hour

PRESETS_24CH = {
    # Night phases - progressive transition from deep blue to pre-dawn warmth

    # Pure deep blue night (opening & closing)
    "night": [
        0.0, 0.0,
        0.05, 0.06, 0.10, 0.10,
        0.04, 0.04,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
    "night_start": [
        0.0, 0.0,
        0.05, 0.06, 0.10, 0.10,
        0.04, 0.04,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
    # Very faint first warmth hint (atmospheric glow on horizon)
    "night_mid": [
        0.0, 0.0,
        0.03, 0.04, 0.06, 0.06,
        0.02, 0.02,
        0.0, 0.0, 0.0, 0.0,
        0.01, 0.01, 0.02, 0.02,
        0.01, 0.01, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
    # Bridge between night and dawn - blue fading, very dim warm emerging
    "night_pre_dawn": [
        0.0, 0.0,
        0.01, 0.01, 0.02, 0.02,
        0.01, 0.01,
        0.0, 0.0, 0.01, 0.01,
        0.03, 0.04, 0.08, 0.10,
        0.08, 0.08, 0.06, 0.06,
        0.01, 0.01, 0.01, 0.01
    ],
    # Closing night (same as night_start)
    "night_end": [
        0.0, 0.0,
        0.05, 0.06, 0.10, 0.10,
        0.04, 0.04,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],

    # Dawn Start - First light on the horizon, very dim warm (~1500K)
    "dawn_start": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.0, 0.0, 0.01, 0.01,
        0.04, 0.06, 0.10, 0.12,
        0.10, 0.10, 0.08, 0.08,
        0.01, 0.01, 0.02, 0.02
    ],

    # Dawn Mid - Growing warm orange (~2000K)
    "dawn_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.01, 0.01, 0.02, 0.02,
        0.12, 0.15, 0.22, 0.28,
        0.22, 0.22, 0.18, 0.18,
        0.02, 0.02, 0.03, 0.03
    ],

    # Dawn End - Moderate warm orange-yellow (~2500K)
    "dawn_end": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.01,
        0.01, 0.01,
        0.03, 0.04, 0.06, 0.08,
        0.25, 0.30, 0.42, 0.50,
        0.40, 0.40, 0.35, 0.35,
        0.04, 0.04, 0.06, 0.06
    ],

    # Sunrise Start - Bright warm orange (~2000-2500K)
    "sunrise_start": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.02, 0.03, 0.05, 0.05,
        0.50, 0.55, 0.72, 0.82,
        0.75, 0.75, 0.68, 0.68,
        0.06, 0.06, 0.08, 0.08
    ],

    # Sunrise Mid - Bright warm orange-yellow (~2500-3500K)
    "sunrise_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.01, 0.02,
        0.06, 0.06,
        0.12, 0.15, 0.22, 0.25,
        0.60, 0.65, 0.78, 0.88,
        0.65, 0.65, 0.58, 0.58,
        0.08, 0.08, 0.10, 0.10
    ],

    # Sunrise End - Transitioning toward daylight (~3500-5000K)
    "sunrise_end": [
        0.01, 0.01,
        0.02, 0.04, 0.06, 0.08,
        0.14, 0.14,
        0.32, 0.38, 0.52, 0.58,
        0.65, 0.70, 0.72, 0.78,
        0.55, 0.55, 0.48, 0.48,
        0.08, 0.08, 0.10, 0.10
    ],

    # Morning - Bright neutral warm white (~4500-5500K)
    "morning": [
        0.02, 0.02,
        0.08, 0.10, 0.16, 0.18,
        0.32, 0.35,
        0.68, 0.72, 0.78, 0.82,
        0.80, 0.82, 0.70, 0.70,
        0.52, 0.52, 0.46, 0.46,
        0.05, 0.05, 0.07, 0.07
    ],

    # Afternoon - Solar noon, bright cool white (~6000-6500K, peak UVA)
    "afternoon": [
        0.04, 0.04,
        0.12, 0.16, 0.22, 0.22,
        0.40, 0.42,
        0.82, 0.88, 0.92, 0.95,
        0.88, 0.90, 0.74, 0.74,
        0.52, 0.52, 0.46, 0.46,
        0.08, 0.08, 0.12, 0.12
    ],

    # Golden Hour Start - Warm deep golden (~3000-3500K)
    "golden_hour_start": [
        0.01, 0.01,
        0.0, 0.0, 0.02, 0.04,
        0.06, 0.08,
        0.22, 0.28, 0.40, 0.48,
        0.78, 0.82, 0.88, 0.95,
        0.88, 0.88, 0.80, 0.80,
        0.12, 0.12, 0.16, 0.16
    ],

    # Golden Hour Mid - Deep golden (~2000-2800K)
    "golden_hour_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.01,
        0.02, 0.02,
        0.08, 0.12, 0.20, 0.25,
        0.82, 0.86, 0.92, 0.98,
        0.92, 0.92, 0.85, 0.85,
        0.16, 0.16, 0.20, 0.20
    ],

    # Golden Hour End - Very warm golden-orange (~1800-2500K)
    "golden_hour_end": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.01, 0.01,
        0.02, 0.04, 0.10, 0.12,
        0.76, 0.80, 0.88, 0.95,
        0.88, 0.88, 0.82, 0.82,
        0.18, 0.18, 0.22, 0.22
    ],

    # Sunset Start - Deep warm orange-red (~1800-2200K)
    "sunset_start": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.01, 0.01, 0.04, 0.05,
        0.58, 0.62, 0.78, 0.88,
        0.85, 0.85, 0.78, 0.78,
        0.14, 0.14, 0.18, 0.18
    ],

    # Sunset Mid - Very deep red-orange (~1500-1800K)
    "sunset_mid": [
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0,
        0.0, 0.0, 0.01, 0.02,
        0.32, 0.38, 0.62, 0.75,
        0.88, 0.88, 0.82, 0.82,
        0.10, 0.10, 0.14, 0.14
    ],

    # Sunset End - Fading deep red, sky turning blue (~1500K fading)
    "sunset_end": [
        0.0, 0.0,
        0.01, 0.02, 0.04, 0.05,
        0.04, 0.04,
        0.01, 0.01, 0.02, 0.03,
        0.18, 0.22, 0.42, 0.58,
        0.65, 0.65, 0.60, 0.60,
        0.07, 0.07, 0.09, 0.09
    ],

    # Blue Hour Start - Deep blue twilight (~8000-12000K)
    "blue_hour_start": [
        0.0, 0.0,
        0.18, 0.22, 0.38, 0.38,
        0.22, 0.22,
        0.03, 0.04, 0.05, 0.05,
        0.05, 0.08, 0.12, 0.18,
        0.12, 0.12, 0.10, 0.10,
        0.0, 0.0, 0.0, 0.0
    ],

    # Blue Hour Mid - Peak deep blue (~10000-15000K)
    "blue_hour_mid": [
        0.0, 0.0,
        0.22, 0.28, 0.44, 0.44,
        0.25, 0.25,
        0.02, 0.02, 0.03, 0.03,
        0.02, 0.04, 0.07, 0.10,
        0.07, 0.07, 0.04, 0.04,
        0.0, 0.0, 0.0, 0.0
    ],

    # Blue Hour End - Fading blue to night (~12000-20000K)
    "blue_hour_end": [
        0.0, 0.0,
        0.12, 0.16, 0.26, 0.26,
        0.14, 0.14,
        0.01, 0.01, 0.01, 0.02,
        0.01, 0.02, 0.04, 0.05,
        0.02, 0.02, 0.01, 0.01,
        0.0, 0.0, 0.0, 0.0
    ],

    # Evening - Fading back to deep blue-violet night
    "evening": [
        0.0, 0.0,
        0.02, 0.01, 0.01, 0.0,
        0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.01, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0
    ],
}


# ============================================================================
# TIME ALLOCATION (same for both models)
# ============================================================================

TIME_ALLOCATION = {
    "night_start":       (0.02, 0.02),  # opening deep blue night
    "night_mid":         (0.03, 0.02),  # very faint warmth begins on horizon
    "night_pre_dawn":    (0.04, 0.01),  # bridge to dawn
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
        print("\nInterrupted by user, disconnecting...")
        if isinstance(result, list):
            luminaires = result
            Telelumen.reset_all(luminaires)
            count = Telelumen.disconnect_all(luminaires)
            print(f"Disconnected {count}/{len(luminaires)} luminaires")
        else:
            lum = result
            Telelumen.reset(lum)
            Telelumen.disconnect(lum)
            print("Disconnected")
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