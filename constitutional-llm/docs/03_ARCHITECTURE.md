# System Architecture: Technical Design

## High-Level System Flow
```text
Bee Action Request
    ↓
ConstitutionalGateway.evaluate_action()
    ├─ Check 5 Principles (hard constraints)
    ├─ Calculate compliance score
    └─ Return: BLOCK, MODIFY, or APPROVE
    ↓
If BLOCKED: Log violation + alert team
If MODIFIED: Apply correction (auto-fix)
If APPROVED: Execute safely
    ↓
ConstitutionalAuditEngine.log_action()
    ├─ Record full action + decision
    ├─ Calculate daily metrics
    └─ Publish audit report
    ↓
Public Audit Report (daily, 00:00 UTC)
```

## Data Flow Diagram
```text
Bee Systems
├── StreamMonitorBee
├── SponsorHunterBee
├── ClipCutterBee
├── SocialPosterBee
├── ListenerIntelBee
├── TrendAnalyzerBee
├── PayoutProcessorBee
└── ArchiveBee
    ↓
constitutional_gateway.py (CORE)
├── Principle 1 validator: Artist-First
├── Principle 2 validator: Transparency
├── Principle 3 validator: Privacy-Respecting
├── Principle 4 validator: Ad-Free Integrity
├── Principle 5 validator: Community-First
    ↓
Response Handler
├── BLOCK → Log violation + alert
├── MODIFY → Apply corrections + log
├── APPROVE → Execute + log
    ↓
constitutional_audit.py (AUDIT ENGINE)
├── Action logger (JSON-L format)
├── Metrics calculator
├── Compliance scorer
├── Report generator
    ↓
Public Audit Portal
├── Daily reports
├── Compliance dashboard
├── Violation timeline
└── Amendment history
```

## File Structure
```text
constitutional-llm/
├── src/
│   ├── __init__.py                      (1 KB)
│   ├── constitutional_gateway.py        (25 KB) - CORE ENGINE
│   ├── constitutional_audit.py          (12 KB) - AUDIT SYSTEM
│   ├── base_bee.py                       (5 KB) - INTEGRATION
│   └── bee_implementations.py           (18 KB) - ALL 8 BEES
├── tests/
│   ├── test_constitutional_gateway.py    (8 KB)
│   ├── test_principles.py                (6 KB)
│   ├── test_bees.py                      (6 KB)
│   ├── test_scenarios.py                 (6 KB)
│   ├── conftest.py
```
