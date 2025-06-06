#!/usr/bin/env python3
"""
Test script to demonstrate the C major chord example function.
This creates a 4-beat measure with C major chords on every downbeat.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.set_management_handler import generate_c_major_chord_example

# Test the C major chord example
result = generate_c_major_chord_example("C_Major_Test", tempo=120.0)

if result['success']:
    print(f"✓ Success: {result['message']}")
    print(f"  Set saved to: {result['path']}")
else:
    print(f"✗ Error: {result['message']}")
