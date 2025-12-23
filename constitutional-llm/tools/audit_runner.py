import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.constitutional_audit import ConstitutionalAuditEngine

def main():
    print("Running Daily Audit...")

    # Initialize audit engine
    audit = ConstitutionalAuditEngine()

    # In a real run, this would be analyzing existing logs.
    # For this demo runner, we just generate the report based on current session logs.

    report = audit.generate_daily_report()

    print("-" * 50)
    print(f"AUDIT REPORT FOR {report['date']}")
    print("-" * 50)
    print(f"Total Actions:      {report['total_actions']}")
    print(f"Compliance Score:   {report['compliance_score']}%")
    print(f"Violations Blocked: {report['violations_blocked']}")
    print(f"Modifications:      {report['modifications_applied']}")
    print(f"Status:             {report['status']}")
    print("-" * 50)

    # Print violations if any
    if report['violations_blocked'] > 0:
        print("\nVIOLATION DETAILS:")
        for v in report['violation_details']:
            print(f"- {v['bee_type']}: {v['decision_reason']}")

    if report['status'] != 'HEALTHY':
        print("\n❌ CRITICAL ALERT: SYSTEM COMPLIANCE BELOW THRESHOLD")
        sys.exit(1)

    print("\n✅ SYSTEM HEALTHY")
    sys.exit(0)

if __name__ == "__main__":
    main()
