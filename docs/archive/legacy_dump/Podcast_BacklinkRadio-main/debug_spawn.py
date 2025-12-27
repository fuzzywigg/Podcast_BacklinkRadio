#!/usr/bin/env python3
"""Debug script to investigate MFR spawn failures."""

import sys
sys.path.insert(0, '.')

import traceback
from hive.queen.orchestrator import QueenOrchestrator

def test_spawn():
    print("=== Initializing Queen ===")
    queen = QueenOrchestrator()
    queen.mfr_enabled = True
    
    # Test just 3 bees with detailed error capture
    test_bees = ['show_prep', 'automation', 'coherence_guardian']
    
    for bee_type in test_bees:
        print(f'\n{"="*50}')
        print(f'Testing: {bee_type}')
        print("="*50)
        try:
            result = queen.spawn_bee(bee_type, {'action': 'get_stats'})
            print(f'Success: {result.get("success", "N/A")}')
            print(f'Coherence: {result.get("_mfr", {}).get("coherence_valid", "N/A")}')
            if not result.get("success"):
                print(f'Error: {result.get("error", "Unknown")}')
        except Exception as e:
            print(f'EXCEPTION: {type(e).__name__}: {e}')
            traceback.print_exc()

if __name__ == "__main__":
    test_spawn()
