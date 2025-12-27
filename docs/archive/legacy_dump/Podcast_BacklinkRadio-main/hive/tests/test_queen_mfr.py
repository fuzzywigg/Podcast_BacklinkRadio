"""Test Queen Orchestrator with MFR integration."""

import sys
from pathlib import Path

# Add hive to path
hive_path = Path(__file__).parent.parent
sys.path.insert(0, str(hive_path.parent))
sys.path.insert(0, str(hive_path / "bees"))

def test_queen_init():
    """Test Queen initialization with MFR."""
    from hive.queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    assert queen.mfr_enabled == True
    assert queen.coherence_check_enabled == True
    assert queen.experience_distillation_enabled == True
    assert len(queen.bee_registry) >= 11  # 8 original + 3 cognitive
    
    print(f"[PASS] Queen initialized with {len(queen.bee_registry)} registered bees")
    print(f"  MFR enabled: {queen.mfr_enabled}")
    return True

def test_queen_health():
    """Test Queen health check with cognitive metrics."""
    from hive.queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    status = queen.heartbeat()
    
    assert "hive_health" in status
    health = status["hive_health"]
    
    assert "mfr_enabled" in health
    assert "cognitive_layer" in health
    assert "pollen_patterns" in health
    
    print(f"[PASS]œ“ Health check passed")
    print(f"  MFR enabled: {health['mfr_enabled']}")
    print(f"  Pollen patterns: {health.get('pollen_patterns', 0)}")
    print(f"  Pending proposals: {health.get('pending_proposals', 0)}")
    return True

def test_cognitive_accessors():
    """Test cognitive layer accessors."""
    from hive.queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Test lazy loading
    guardian = queen._get_coherence_guardian()
    governor = queen._get_evolution_governor()
    distiller = queen._get_experience_distiller()
    
    # At least some should load (may fail if imports missing)
    loaded = sum([
        guardian is not None,
        governor is not None,
        distiller is not None
    ])
    
    print(f"[PASS]œ“ Cognitive accessors: {loaded}/3 loaded")
    return True

def test_mfr_workflow_methods():
    """Test MFR workflow method signatures."""
    from hive.queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Test coherence check
    assert hasattr(queen, 'run_coherence_check')
    assert hasattr(queen, 'run_evolution_governance')
    assert hasattr(queen, 'run_experience_distillation')
    assert hasattr(queen, 'check_model_coherence')
    assert hasattr(queen, '_spawn_with_mfr')
    assert hasattr(queen, '_run_cognitive_cycle')
    
    print("[PASS]œ“ MFR workflow methods present")
    return True

def test_success_score_calculation():
    """Test success score calculation."""
    from hive.queen.orchestrator import QueenOrchestrator
    
    queen = QueenOrchestrator(hive_path=hive_path)
    
    # Test various result scenarios
    score1 = queen._calculate_success_score({"success": True, "output": "test"}, 5)
    score2 = queen._calculate_success_score({"success": False, "error": "failed"}, 30)
    score3 = queen._calculate_success_score({}, 15)
    
    assert score1 > score2  # Success > failure
    assert score1 >= 0.8  # Fast success with output
    assert score2 <= 0.4  # Failed with error
    
    print(f"[PASS]œ“ Success scores: success={score1:.2f}, failure={score2:.2f}, neutral={score3:.2f}")
    return True

def run_all_tests():
    """Run all Queen MFR tests."""
    print("\n" + "="*50)
    print("QUEEN ORCHESTRATOR MFR INTEGRATION TESTS")
    print("="*50 + "\n")
    
    tests = [
        ("Queen Init", test_queen_init),
        ("Health Check", test_queen_health),
        ("Cognitive Accessors", test_cognitive_accessors),
        ("MFR Methods", test_mfr_workflow_methods),
        ("Success Score", test_success_score_calculation)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[TEST] {name}")
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[PASS]œ— {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
