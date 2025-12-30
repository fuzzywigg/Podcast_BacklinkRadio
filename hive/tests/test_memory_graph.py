import pytest
import asyncio
from unittest.mock import MagicMock, patch
from hive.utils.memory_graph import HiveKnowledgeGraph

class TestHiveKnowledgeGraph:
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test that graph initializes correctly."""
        # Mock networkx presence check to True if needed, but the code gracefully handles absence.
        # Here we just verify it doesn't crash.
        g = HiveKnowledgeGraph()
        # If networkx is installed in the env, graph is a DiGraph, otherwise None.
        # We assert it's an object.
        assert g is not None

    @pytest.mark.asyncio
    async def test_add_knowledge(self):
        """Test adding a triple."""
        g = HiveKnowledgeGraph()
        
        # We need to ensure self.graph is not None for this test to "work" logically,
        # otherwise it returns False.
        # Let's mock the internal graph object to simulate a working environment regardless of imports.
        g.graph = MagicMock()
        
        result = await g.add_knowledge("Stripe", "handles", "Payments")
        
        assert result is True
        g.graph.add_node.assert_any_call("Stripe", type="entity")
        g.graph.add_edge.assert_called_with("Stripe", "Payments", relation="handles")

    @pytest.mark.asyncio
    async def test_retrieve_context(self):
        """Test retrieving context via traversal."""
        g = HiveKnowledgeGraph()
        
        # Setup a real NetworkX graph if available, or mock it.
        # Since we can't guarantee 'networkx' is in the test runner's env, let's mock the behavior.
        # But actually, requirements.txt has networkx, so let's assume availability or skip.
        try:
            import networkx as nx
            g.graph = nx.DiGraph()
            g.graph.add_edge("Stripe", "Payments", relation="handles")
            
            context = await g.retrieve_context("Stripe")
            assert "Stripe handles Payments" in context
            
            # Test missing node
            missing = await g.retrieve_context("Ghost")
            assert "No memory found" in missing[0]
            
        except ImportError:
            pytest.skip("NetworkX not installed")

    @pytest.mark.asyncio
    async def test_graceful_failure_without_graph(self):
        """Test that methods fail safely if graph backend is missing."""
        g = HiveKnowledgeGraph()
        g.graph = None # Simulate missing dependency
        
        added = await g.add_knowledge("A", "b", "C")
        assert added is False
        
        context = await g.retrieve_context("A")
        assert context == []
