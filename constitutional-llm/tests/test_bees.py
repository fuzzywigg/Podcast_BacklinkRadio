import pytest

def test_sponsor_bee_negotiation(sponsor_bee):
    # Safe deal (60% share)
    result = sponsor_bee.negotiate_deal("Coke", 1000, 600)
    assert result['artist_revenue'] == 600

    # Unsafe deal (40% share) -> Raises ValueError (BLOCKED)
    with pytest.raises(ValueError) as excinfo:
        sponsor_bee.negotiate_deal("Pepsi", 1000, 400)
    assert "below minimum" in str(excinfo.value)

def test_social_bee_posting(social_bee):
    # Sponsored post auto-fix
    result = social_bee.post_content("Buy stuff", is_sponsored=True)
    assert "[PARTNER]" in result['content']

    # Normal post
    result = social_bee.post_content("Hello world", is_sponsored=False)
    assert result['content'] == "Hello world"
