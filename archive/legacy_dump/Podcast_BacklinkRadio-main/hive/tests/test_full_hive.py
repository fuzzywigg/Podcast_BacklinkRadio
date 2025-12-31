"""
Full Hive Validation Test
Tests all 32 bees are registered and can be spawned
"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding for Unicode (emojis in bee output)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add hive to path
hive_path = Path(__file__).parent.parent
sys.path.insert(0, str(hive_path))

def test_full_registry():
    print("=" * 70)
    print("FULL HIVE VALIDATION - 32 BEES")
    print("=" * 70)
    
    from queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # All 32 expected bees
    expected_bees = {
        # Content (4)
        "show_prep", "clip_cutter", "script_writer", "jingle",
        # Research (4)
        "trend_scout", "listener_intel", "music_discovery", "competitor_watch",
        # Marketing (4)
        "social_poster", "newsletter", "seo", "viral_analyst",
        # Monetization (4)
        "sponsor_hunter", "donation_processor", "revenue_analyst", "merch",
        # Community (5)
        "engagement", "vip_manager", "moderator", "giveaway", "local_liaison",
        # Technical (5)
        "stream_monitor", "archivist", "automation", "audio_engineer", "integration",
        # Admin (3)
        "analytics", "planner", "licensing",
        # Cognitive (3)
        "coherence_guardian", "evolution_governor", "experience_distiller"
    }
    
    print(f"\nExpected: {len(expected_bees)} bees")
    print(f"Registered: {len(queen.bee_registry)} bees")
    
    # Group by category for display
    categories = {
        "Content": ["show_prep", "clip_cutter", "script_writer", "jingle"],
        "Research": ["trend_scout", "listener_intel", "music_discovery", "competitor_watch"],
        "Marketing": ["social_poster", "newsletter", "seo", "viral_analyst"],
        "Monetization": ["sponsor_hunter", "donation_processor", "revenue_analyst", "merch"],
        "Community": ["engagement", "vip_manager", "moderator", "giveaway", "local_liaison"],
        "Technical": ["stream_monitor", "archivist", "automation", "audio_engineer", "integration"],
        "Admin": ["analytics", "planner", "licensing"],
        "Cognitive": ["coherence_guardian", "evolution_governor", "experience_distiller"]
    }
    
    all_found = True
    for category, bees in categories.items():
        print(f"\n{category} ({len(bees)}):")
        for bee_type in bees:
            if bee_type in queen.bee_registry:
                print(f"  [OK] {bee_type}")
            else:
                print(f"  [MISSING] {bee_type}")
                all_found = False
    
    print("\n" + "=" * 70)
    if all_found:
        print(f"SUCCESS: All {len(expected_bees)}/32 bees registered!")
    else:
        missing = expected_bees - set(queen.bee_registry.keys())
        print(f"INCOMPLETE: Missing {len(missing)} bees: {missing}")
    print("=" * 70)
    
    return all_found

def test_spawn_all():
    """Test spawning every bee type"""
    print("\n" + "=" * 70)
    print("SPAWN TEST - ALL BEES")
    print("=" * 70)
    
    from queen.orchestrator import QueenOrchestrator
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Test with no task - let bees do their default work
    # This tests that each bee can be spawned and execute its default behavior
    
    success = 0
    failed = []
    
    for bee_type in sorted(queen.bee_registry.keys()):
        try:
            # Spawn with None task - triggers default behavior
            result = queen.spawn_bee(bee_type, None)
            if "error" not in result:
                print(f"  [OK] {bee_type}")
                success += 1
            else:
                print(f"  [FAIL] {bee_type}: {result['error']}")
                failed.append(bee_type)
        except Exception as e:
            print(f"  [ERROR] {bee_type}: {e}")
            failed.append(bee_type)
    
    print(f"\nSpawn Results: {success}/{len(queen.bee_registry)} successful")
    if failed:
        print(f"Failed: {failed}")
    
    return len(failed) == 0

if __name__ == "__main__":
    registry_ok = test_full_registry()
    spawn_ok = test_spawn_all()
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    if registry_ok and spawn_ok:
        print("ALL 32 BEES OPERATIONAL!")
        print("Hive is at 100% capacity.")
    else:
        print("Some bees need attention.")
    print("=" * 70)
