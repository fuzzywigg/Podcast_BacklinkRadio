"""
Hive Knowledge Graph (Memory Layer)

This module implements the "Cognitive Map" for the Backlink Hive, transitioning
from flat file storage to a graph-based memory system using Cognee principles.

It provides the `HiveKnowledgeGraph` class which abstracts node/edge creation
and semantic retrieval.
"""

import logging
from typing import Any, Dict, List, Optional, Union

try:
    import networkx as nx
    # import cognee  # Commented out until fully vendored/installed
except ImportError:
    nx = None

logger = logging.getLogger(__name__)

class HiveKnowledgeGraph:
    """
    The central memory store for the Hive Swarm.
    
    Acts as a wrapper around a persisted Graph (NetworkX/Cognee) to allow Bees
    to store relationships (Triples) and retrieve context via traversal.
    """

    def __init__(self, persistence_path: str = "hive_memory.graphml"):
        self.persistence_path = persistence_path
        self.graph = nx.DiGraph() if nx else None
        self._load_graph()

    def _load_graph(self) -> None:
        """Loads the graph from disk if available."""
        if not self.graph:
            logger.warning("NetworkX not available. Graph memory disabled.")
            return
            
        try:
            # Placeholder for actual persistence logic
            # self.graph = nx.read_graphml(self.persistence_path)
            pass
        except Exception as e:
            logger.info(f"Initialized new Knowledge Graph (No existing file: {e})")

    async def add_knowledge(self, 
                            subject: str, 
                            predicate: str, 
                            object_: str, 
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Adds a semantic triple to the memory graph.
        
        Args:
            subject: The source node (e.g., "Stripe")
            predicate: The relationship (e.g., "handles")
            object_: The target node (e.g., "Payments")
            metadata: Additional context (e.g., source file, timestamp)
        """
        if not self.graph:
            return False

        try:
            self.graph.add_node(subject, type="entity")
            self.graph.add_node(object_, type="concept")
            self.graph.add_edge(subject, object_, relation=predicate, **(metadata or {}))
            logger.debug(f"Learned: {subject} -> {predicate} -> {object_}")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False

    async def retrieve_context(self, query_node: str, depth: int = 1) -> List[str]:
        """
        Retrieves related context by traversing the graph from a starting node.
        
        Args:
            query_node: The node to start searching from.
            depth: How many hops to traverse.
            
        Returns:
            List of natural language strings describing the relationships.
        """
        if not self.graph:
            return []
            
        if query_node not in self.graph:
            return [f"No memory found for '{query_node}'"]

        results = []
        # Simple BFS traversal for context
        edges = list(self.graph.out_edges(query_node, data=True))
        
        for u, v, data in edges:
            relation = data.get('relation', 'related_to')
            results.append(f"{u} {relation} {v}")
            
            # If depth > 1, we would recursively fetch v's edges here
            if depth > 1:
                sub_edges = self.graph.out_edges(v, data=True)
                for su, sv, sdata in sub_edges:
                    sub_rel = sdata.get('relation', 'related_to')
                    results.append(f"  -> {sv} ({sub_rel})")

        return results

    def save_snapshot(self) -> None:
        """Persists the current graph state to disk."""
        if self.graph:
            try:
                # nx.write_graphml(self.graph, self.persistence_path)
                pass
            except Exception as e:
                logger.error(f"Failed to save graph snapshot: {e}")

# Singleton instance
memory = HiveKnowledgeGraph()
