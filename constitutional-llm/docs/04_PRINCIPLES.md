# Detailed Principles & Constraint Rules

## Principle 1: Artist-First (Detailed Rules)

### Constraint Rule 1.1: Minimum Artist Share
**Hard rule**: Artists must receive ≥50% of all deal revenue.

```python
ARTIST_MINIMUM_SHARE = 0.50  # 50% minimum

def validate_artist_share(deal: Dict) -> bool:
    artist_share = deal['artist_revenue'] / deal['total_revenue']
    if artist_share < ARTIST_MINIMUM_SHARE:
        return False  # BLOCK
    return True  # APPROVE
```

**Application**:
- All sponsorship deals
- Merchandise partnerships
- Licensing agreements
- Affiliate commissions
- Brand collaborations

### Constraint Rule 1.2: No Hidden Deductions
Artists must see all deductions transparently:
- Platform fee (max 10%)
- Payment processing (actual cost, not inflated)
- Marketing (if any, must be agreed)
- Tax withholding (legal requirement only)

**Violation example**:
```text
Sponsor pays: $1,000
Platform fee: $200 (20%) → BLOCKED
Artist gets: $200 (20%)

Instead:
Platform fee: $100 (10%) → APPROVED
Artist gets: $450 (45%) → Still needs to be ≥50%
```

### Constraint Rule 1.3: Minimum Deal Threshold
No deal below $100 threshold (prevents micropayments that don't justify artist effort).
- **Exception**: Organic mentions without payment (no minimum)

### Constraint Rule 1.4: Retroactive Payment Adjustments
If payout later shows artist earned <50%:
- Automatic correction within 30 days
- Artist receives difference plus 10% penalty to platform
- Logged as violation in audit

## Principle 2: Transparency (Detailed Rules)

### Constraint Rule 2.1: Disclosure Tag Requirements
Every sponsored mention must include:
- `[PARTNER]` tag at start or end
- Sponsor name (full, not abbreviated)
- Nature of partnership (product, cash, trade, equity, etc)

**Valid examples**:
```text
✅ "[PARTNER] Spotify: We use it daily. Discount: BACKLINK10"
✅ "Our show is made possible by [PARTNER] Patreon supporters"
✅ "[PARTNER] Amazon Music: Ad placement in this clip"
```

**Invalid examples**:
```text
❌ "
```
