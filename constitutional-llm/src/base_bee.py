# base_bee.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from .constitutional_gateway import ConstitutionalGateway
from .constitutional_audit import ConstitutionalAuditEngine

class BaseBee(ABC):
    """
    Abstract Base Class for all Bees.
    Enforces usage of safe_action() for constitutional compliance.
    """

    def __init__(self, bee_type: str):
        self.bee_type = bee_type
        self.gateway = ConstitutionalGateway(bee_type)
        self.audit = ConstitutionalAuditEngine()

    def safe_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper that sends action to Gateway before execution.
        Returns the safe action (which might be modified) or raises an error if blocked.
        """
        # 1. Evaluate
        decision = self.gateway.evaluate_action(action)

        # 2. Log
        self.audit.log_action(self.bee_type, action, decision)

        # 3. Execute or Halt
        if decision['status'] == 'BLOCK':
            # In a real agent, we might catch this and retry with different params.
            # Here we raise to stop execution.
            raise ValueError(f"Constitutional Violation (BLOCKED): {decision.get('reason')}")

        return decision['action'] # Returns modified or original action

    @abstractmethod
    def run(self):
        """Main loop for the Bee"""
        pass
