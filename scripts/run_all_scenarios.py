"""
AquaRoute AI - Command Line Batch Scenario Generator
Regenerates all 9 flood scenarios across Mumbai, Jakarta, and Houston.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import run_all

if __name__ == "__main__":
    print("==================================================================")
    print("🌊 AquaRoute AI: Batch 4-Step Flood Simulation Generator")
    print("==================================================================")
    run_all()
