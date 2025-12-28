import pytest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.constitutional_gateway import ConstitutionalGateway

class TestConstitutionalGateway:
    @pytest.fixture
    def gateway(self):
        return ConstitutionalGateway()

    def test_artist_first_block(self, gateway):
        action = {
            "type": "deal_negotiation",
            "total_revenue": 1000,
            "artist_revenue": 400 # 40% < 50%
        }
        result = gateway.evaluate_action(action)
        assert result['status'] == "BLOCK"
        assert "below minimum" in result['reason']

    def test_artist_first_approve(self, gateway):
        action = {
            "type": "deal_negotiation",
            "total_revenue": 1000,
            "artist_revenue": 600 # 60% > 50%
        }
        result = gateway.evaluate_action(action)
        assert result['status'] == "APPROVE"

    def test_transparency_modify(self, gateway):
        action = {
            "type": "social_post",
            "content": "Check out this product!",
            "is_sponsored": True
        }
        result = gateway.evaluate_action(action)
        assert result['status'] == "MODIFY"
        assert "[PARTNER]" in result['action']['content']

    def test_privacy_block(self, gateway):
        action = {
            "type": "data_processing",
            "requires_pii": True,
            "has_explicit_consent": False
        }
        result = gateway.evaluate_action(action)
        assert result['status'] == "BLOCK"

    def test_privacy_approve(self, gateway):
        action = {
            "type": "data_processing",
            "requires_pii": True,
            "has_explicit_consent": True
        }
        result = gateway.evaluate_action(action)
        assert result['status'] == "APPROVE"
