#!/usr/bin/env python3
"""
Quick test for fifth layer screening system.
"""

from fifth_layer_screening import FifthLayerScreening

print("Testing Fifth Layer Screening System...")
print()

# Initialize
screening = FifthLayerScreening()

# Test with Technology sector (small test)
print("Testing sector screening...")
results = screening.screen_sector("Technology")

print()
print("Results:")
print(screening.format_results(results))




