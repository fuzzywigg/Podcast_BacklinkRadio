def test_principle_1_artist_share(gateway):
    # Test 50% rule
    # Below 50% -> BLOCK
    assert gateway.evaluate_action({"type": "deal_negotiation", "total_revenue": 100, "artist_revenue": 49})['status'] == "BLOCK"
    # Exact 50% -> APPROVE
    assert gateway.evaluate_action({"type": "deal_negotiation", "total_revenue": 100, "artist_revenue": 50})['status'] == "APPROVE"
    # Above 50% -> APPROVE
    assert gateway.evaluate_action({"type": "deal_negotiation", "total_revenue": 100, "artist_revenue": 70})['status'] == "APPROVE"

def test_principle_2_transparency(gateway):
    # Test [PARTNER] tag
    # Missing tag -> MODIFY
    res = gateway.evaluate_action({"type": "social_post", "content": "Buy this!", "is_sponsored": True})
    assert res['status'] == "MODIFY"
    assert "[PARTNER]" in res['action']['content']

    # Present tag -> APPROVE
    res = gateway.evaluate_action({"type": "social_post", "content": "[PARTNER] Buy this!", "is_sponsored": True})
    assert res['status'] == "APPROVE"

def test_principle_3_privacy(gateway):
    # Test consent
    # No consent -> BLOCK
    assert gateway.evaluate_action({"type": "data_processing", "requires_pii": True, "has_explicit_consent": False})['status'] == "BLOCK"
    # Consent -> APPROVE
    assert gateway.evaluate_action({"type": "data_processing", "requires_pii": True, "has_explicit_consent": True})['status'] == "APPROVE"

def test_principle_4_ad_free(gateway):
    # Test hourly limit
    # First one OK (Must include [PARTNER] to avoid transparency modification)
    assert gateway.evaluate_action({"type": "broadcast_announcement", "is_sponsored": True, "content": "[PARTNER] ad"})['status'] == "APPROVE"

    # Second one -> BLOCK
    gateway.sponsor_mentions_this_hour = 1
    assert gateway.evaluate_action({"type": "broadcast_announcement", "is_sponsored": True, "content": "[PARTNER] ad"})['status'] == "BLOCK"

def test_principle_5_community(gateway):
    # High virality, low retention -> BLOCK
    assert gateway.evaluate_action({"type": "content_strategy", "projected_virality": 0.9, "projected_retention": 0.2})['status'] == "BLOCK"
    # Balanced -> APPROVE
    assert gateway.evaluate_action({"type": "content_strategy", "projected_virality": 0.9, "projected_retention": 0.5})['status'] == "APPROVE"
