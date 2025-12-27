"""
Test Queen Orchestrator Bee Registry
Validates all 24 bees are registered and can be spawned
"""
import sys
from pathlib import Path

# Add hive to path
hive_path = Path(__file__).parent.parent
sys.path.insert(0, str(hive_path))

def test_registry():
    print("=" * 60)
    print("QUEEN ORCHESTRATOR BEE REGISTRY TEST")
    print("=" * 60)
    
    from queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Expected bees (24 total)
    expected_bees = {
        # Content (3)
        "show_prep", "clip_cutter", "script_writer",
        # Research (3)
        "trend_scout", "listener_intel", "music_discovery",
        # Marketing (3)
        "social_poster", "newsletter", "seo",
        # Monetization (3)
        "sponsor_hunter", "donation_processor", "revenue_analyst",
        # Community (4)
        "engagement", "vip_manager", "moderator", "giveaway",
        # Technical (3)
        "stream_monitor", "archivist", "automation",
        # Admin (2)
        "analytics", "planner",
        # Cognitive (3)
        "coherence_guardian", "evolution_governor", "experience_distiller"
    }
    
    print(f"\nExpected bees: {len(expected_bees)}")
    print(f"Registered bees: {len(queen.bee_registry)}")
    
    # Check each expected bee
    missing = []
    found = []
    
    for bee_type in sorted(expected_bees):
        if bee_type in queen.bee_registry:
            found.append(bee_type)
            print(f"  [OK] {bee_type}")
        else:
            missing.append(bee_type)
            print(f"  [MISSING] {bee_type}")
    
    # Check for unexpected bees
    unexpected = set(queen.bee_registry.keys()) - expected_bees
    if unexpected:
        print(f"\nUnexpected bees in registry: {unexpected}")
    
    print("\n" + "-" * 60)
    print(f"SUMMARY: {len(found)}/{len(expected_bees)} bees registered")
    
    if missing:
        print(f"Missing: {missing}")
        return False
    
    print("All bees registered successfully!")
    return True

def test_spawn_sample():
    """Test spawning a few sample bees"""
    print("\n" + "=" * 60)
    print("SPAWN TEST (Sample Bees)")
    print("=" * 60)
    
    from queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Test spawning different categories
    test_bees = [
        ("script_writer", {"action": "get_stats"}),
        ("music_discovery", {"action": "get_stats"}),
        ("seo", {"action": "get_stats"}),
        ("automation", {"action": "get_status"}),
    ]
    
    success_count = 0
    for bee_type, task in test_bees:
        try:
            result = queen.spawn_bee(bee_type, task)
            if "error" not in result:
                print(f"  [OK] {bee_type} spawned successfully")
                success_count += 1
            else:
                print(f"  [FAIL] {bee_type}: {result['error']}")
        except Exception as e:
            print(f"  [ERROR] {bee_type}: {e}")
    
    print(f"\nSpawn test: {success_count}/{len(test_bees)} successful")
    return success_count == len(test_bees)

if __name__ == "__main__":
    registry_ok = test_registry()
    spawn_ok = test_spawn_sample()
    
    print("\n" + "=" * 60)
    if registry_ok and spawn_ok:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)
