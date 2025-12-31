"""
Test script for Cognitive Layer and Model-First Reasoning.

Run this to verify the cognitive bees and MFR infrastructure work correctly.
"""

import sys
from pathlib import Path

# Add hive to path
hive_path = Path(__file__).parent.parent
sys.path.insert(0, str(hive_path))

# Use ASCII-safe symbols
PASS = "[OK]"
FAIL = "[FAIL]"

def test_pollen_store():
    """Test PollenStore functionality."""
    print("\n=== Testing PollenStore ===")
    
    from memory.pollen_store import PollenStore
    
    store = PollenStore(hive_path)
    
    # Store a test pattern
    pollen_id = store.store(
        bee_type="TestBee",
        task_type="test_task",
        model={
            "entities": ["test_entity"],
            "constraints": ["must be positive"],
            "possible_actions": ["process", "skip"]
        },
        result_summary={"success": True, "summary": "Test worked"},
        success_score=0.85,
        tags=["test", "unit_test"]
    )
    
    print(f"  {PASS} Stored pollen: {pollen_id}")
    
    # Recall patterns
    recalled = store.recall(task_type="test_task", min_score=0.7)
    print(f"  {PASS} Recalled {len(recalled)} patterns")
    
    # Get stats
    stats = store.get_stats()
    print(f"  {PASS} Store stats: {stats['total_entries']} entries, {stats['total_recalls']} recalls")
    
    return True


def test_lineage_tracker():
    """Test LineageTracker functionality."""
    print("\n=== Testing LineageTracker ===")
    
    from memory.lineage_tracker import LineageTracker
    
    tracker = LineageTracker(hive_path)
    
    # Register a bee type
    tracker.register_bee_type("TestBee", "1.0.0")
    print(f"  {PASS} Registered TestBee v1.0.0")
    
    # Propose an update
    proposal_id = tracker.propose_update(
        bee_type="TestBee",
        changes=["Improved response time", "Added caching"],
        evidence={
            "metrics": {"response_time": 0.5, "success_rate": 0.95},
            "sample_size": 10,
            "improvement_pct": 0.2
        },
        proposed_by="test_hive"
    )
    print(f"  {PASS} Proposed update: {proposal_id}")
    
    # Get pending proposals
    pending = tracker.get_pending_proposals()
    print(f"  {PASS} Pending proposals: {len(pending)}")
    
    # Get stats
    stats = tracker.get_stats()
    print(f"  {PASS} Tracker stats: {stats['registered_bee_types']} bee types, {stats['pending_proposals']} pending")
    
    return True


def test_coherence_guardian():
    """Test CoherenceGuardianBee functionality."""
    print("\n=== Testing CoherenceGuardianBee ===")
    
    from bees.cognitive.coherence_guardian_bee import CoherenceGuardianBee
    
    bee = CoherenceGuardianBee(hive_path)
    
    # Run full coherence check
    result = bee.run({"payload": {"action": "full_check"}})
    
    if result["success"]:
        check = result["result"]
        print(f"  {PASS} Coherence check: {check['overall_coherence']:.0%}")
        print(f"  {PASS} Checks performed: {check['checks_performed']}")
        print(f"  {PASS} Issues found: {len(check['issues_found'])}")
    else:
        print(f"  {FAIL} Error: {result.get('error')}")
        return False
    
    # Validate a model
    test_model = {
        "task_type": "test",
        "entities": ["bee", "task"],
        "state_variables": {"status": "pending"},
        "possible_actions": ["process", "skip"],
        "constraints": ["must validate"],
        "pollen_sources": []
    }
    
    result = bee.run({"payload": {"action": "validate_model", "model": test_model}})
    if result["success"]:
        validation = result["result"]
        print(f"  {PASS} Model validation: {'valid' if validation['valid'] else 'invalid'}")
        print(f"  {PASS} Completeness: {validation['completeness']:.0%}")
    
    return True


def test_evolution_governor():
    """Test EvolutionGovernorBee functionality."""
    print("\n=== Testing EvolutionGovernorBee ===")
    
    from bees.cognitive.evolution_governor_bee import EvolutionGovernorBee
    
    bee = EvolutionGovernorBee(hive_path)
    
    # Get stats
    result = bee.run({"payload": {"action": "stats"}})
    
    if result["success"]:
        stats = result["result"]
        print(f"  {PASS} Pending proposals: {stats['totals']['pending']}")
        print(f"  {PASS} Approval rate: {stats['approval_rate']:.0%}")
        print(f"  {PASS} Governance health: {stats['governance_health']}")
    else:
        print(f"  {FAIL} Error: {result.get('error')}")
        return False
    
    return True


def test_experience_distiller():
    """Test ExperienceDistillerBee functionality."""
    print("\n=== Testing ExperienceDistillerBee ===")
    
    from bees.cognitive.experience_distiller_bee import ExperienceDistillerBee
    
    bee = ExperienceDistillerBee(hive_path)
    
    # Analyze pollen utilization
    result = bee.run({"payload": {"action": "analyze"}})
    
    if result["success"]:
        analysis = result["result"]
        print(f"  {PASS} Total pollen entries: {analysis.get('total_entries', 0)}")
        print(f"  {PASS} Utilization rate: {analysis.get('utilization_rate', 0):.1%}")
        if analysis.get("recommendations"):
            print(f"  {PASS} Recommendations: {len(analysis['recommendations'])}")
    else:
        print(f"  {FAIL} Error: {result.get('error')}")
        return False
    
    return True


def test_base_bee_mfr():
    """Test Model-First Reasoning in BaseBee."""
    print("\n=== Testing BaseBee MFR ===")
    
    from bees.base_bee import BaseBee
    
    # Create a concrete test bee
    class TestMFRBee(BaseBee):
        BEE_TYPE = "test_mfr"
        BEE_NAME = "Test MFR Bee"
        CATEGORY = "test"
        
        def work(self, task=None):
            return {"message": "Test work completed"}
        
        def execute_within_model(self, model, task):
            return {
                "success": True,
                "summary": f"Executed with {len(model.get('constraints', []))} constraints"
            }
    
    bee = TestMFRBee(hive_path)
    
    # Define a model
    task = {"type": "test", "payload": {"action": "test"}}
    model = bee.define_model(task)
    
    print(f"  {PASS} Model defined with {len(model['entities'])} entities")
    print(f"  {PASS} Model has {len(model['constraints'])} constraints")
    print(f"  {PASS} Model has {len(model['possible_actions'])} possible actions")
    
    # Check coherence
    coherent = bee.coherence_check(model)
    print(f"  {PASS} Coherence check: {'passed' if coherent else 'failed'}")
    
    # Execute within model
    result = bee.execute_within_model(model, task)
    print(f"  {PASS} Execution result: {result.get('success')}")
    
    # Store pollen
    pollen_id = bee.store_pollen(model, result, success_score=0.9)
    print(f"  {PASS} Pollen stored: {pollen_id or 'N/A'}")
    
    return True


def main():
    """Run all cognitive layer tests."""
    print("=" * 60)
    print("COGNITIVE LAYER & MFR TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("PollenStore", test_pollen_store),
        ("LineageTracker", test_lineage_tracker),
        ("CoherenceGuardianBee", test_coherence_guardian),
        ("EvolutionGovernorBee", test_evolution_governor),
        ("ExperienceDistillerBee", test_experience_distiller),
        ("BaseBee MFR", test_base_bee_mfr)
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, success))
        except Exception as e:
            print(f"\n  {FAIL} ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = f"{PASS} PASS" if success else f"{FAIL} FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    import os
    os.chdir(str(hive_path))
    success = main()
    sys.exit(0 if success else 1)
