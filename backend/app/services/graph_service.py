import uuid
from typing import Optional, List
from app.models.graph import ReasoningGraph, GraphNode, GraphEdge, EdgeType, default_relationship_label
from app.data.knowledge_base import knowledge_base
from app.db.repository import Repository
from app.models.common import DerivationLabel

class GraphService:
    def __init__(self, repo: Repository):
        self.repo = repo

    async def build_graph(self, challenge_id: str, selected_inspiration_ids: Optional[List[str]] = None) -> ReasoningGraph:
        if challenge_id.startswith("user-"):
            inspirations = await self.repo.get_inspirations_for_challenge(challenge_id)
        else:
            inspirations = knowledge_base.get_inspirations(challenge_id)

        if selected_inspiration_ids is not None:
            inspirations = [i for i in inspirations if i.id in selected_inspiration_ids]
            
        nodes = []
        for insp in inspirations:
            nodes.append(GraphNode(
                id=f"n-{insp.id}",
                inspiration_id=insp.id,
                label=insp.name,
                domain=insp.domain,
                importance=0.5, # Will be recomputed
                derivation=DerivationLabel.SYSTEM
            ))
            
        # Create a set of valid node inspiration IDs to filter edges
        valid_insp_ids = {i.id for i in inspirations}
        
        edges = []
        if challenge_id.startswith("user-"):
            db_edges = await self.repo.get_edges_for_challenge(challenge_id)
            for edge in db_edges:
                if edge.source_id in valid_insp_ids and edge.target_id in valid_insp_ids:
                    edge.source_id = f"n-{edge.source_id}"
                    edge.target_id = f"n-{edge.target_id}"
                    edges.append(edge)
        else:
            raw_edges = knowledge_base.get_raw_edges(challenge_id)
            for e_data in raw_edges:
                if e_data["source_id"] in valid_insp_ids and e_data["target_id"] in valid_insp_ids:
                    edge_type = EdgeType(e_data["edge_type"])
                    edges.append(GraphEdge(
                        id=e_data["id"],
                        source_id=f"n-{e_data['source_id']}",
                        target_id=f"n-{e_data['target_id']}",
                        edge_type=edge_type,
                        weight=e_data["weight"],
                        relationship_label=e_data.get("relationship_label")
                            or default_relationship_label(edge_type),
                        relationship_description=e_data["relationship_description"],
                        transferable_insight=e_data["transferable_insight"],
                        evidence=e_data["evidence"],
                        derivation=DerivationLabel.CURATED,
                        confidence=e_data.get("confidence"),
                    ))
                
        # Recompute node importance based on connectivity (degree centrality simplified)
        graph = ReasoningGraph(
            id=str(uuid.uuid4()),
            challenge_id=challenge_id,
            nodes=nodes,
            edges=edges
        )
        
        self.update_node_importance(graph)
        return graph
        
    @staticmethod
    def update_node_importance(graph: ReasoningGraph):
        """Recompute degree-centrality importance. Does not touch the repository."""
        if not graph.nodes:
            return
            
        node_weights = {node.id: 0.0 for node in graph.nodes}
        for edge in graph.edges:
            node_weights[edge.source_id] += edge.weight
            node_weights[edge.target_id] += edge.weight
            
        max_weight = max(node_weights.values()) if node_weights else 0
        if max_weight > 0:
            for node in graph.nodes:
                # Base importance 0.2 + normalized connectivity
                node.importance = 0.2 + (0.8 * (node_weights[node.id] / max_weight))
        else:
            for node in graph.nodes:
                node.importance = 0.5

    # Back-compat alias for any internal callers
    def _update_node_importance(self, graph: ReasoningGraph):
        GraphService.update_node_importance(graph)
