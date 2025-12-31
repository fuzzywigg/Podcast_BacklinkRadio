"""Quick validation test for new bees."""
import sys
sys.path.insert(0, 'bees')

print('Testing new bee imports...')

try:
    from content.script_writer_bee import ScriptWriterBee
    print('[OK] ScriptWriterBee')
except Exception as e:
    print(f'[FAIL] ScriptWriterBee: {e}')

try:
    from research.music_discovery_bee import MusicDiscoveryBee
    print('[OK] MusicDiscoveryBee')
except Exception as e:
    print(f'[FAIL] MusicDiscoveryBee: {e}')

try:
    from marketing.seo_bee import SEOBee
    print('[OK] SEOBee')
except Exception as e:
    print(f'[FAIL] SEOBee: {e}')

try:
    from technical.automation_bee import AutomationBee
    print('[OK] AutomationBee')
except Exception as e:
    print(f'[FAIL] AutomationBee: {e}')

print()
print('Running quick functional tests...')

# ScriptWriterBee
sw = ScriptWriterBee()
result = sw.run({'action': 'get_stats'})
print(f"ScriptWriterBee.get_stats: {result.get('success', False)}")

# MusicDiscoveryBee
md = MusicDiscoveryBee()
result = md.run({'action': 'get_stats'})
print(f"MusicDiscoveryBee.get_stats: {result.get('success', False)}")

# SEOBee
seo = SEOBee()
result = seo.run({'action': 'get_stats'})
print(f"SEOBee.get_stats: {result.get('success', False)}")

# AutomationBee
auto = AutomationBee()
result = auto.run({'action': 'get_status'})
print(f"AutomationBee.get_status: {result.get('success', False)}")

print()
print('All new bees validated!')
