from typing import Tuple, List
from app.models.graph import ReasoningGraph, EdgeType
from app.models.constraints import ConstraintSet, ConstraintEffect, ConstraintKey
from app.models.common import DerivationLabel

class ConstraintEngine:
    def apply_constraints(self, graph: ReasoningGraph, constraints: ConstraintSet) -> Tuple[ReasoningGraph, List[ConstraintEffect]]:
        effects = []
        
        # We'll create a copy of edges to modify
        modified_edges = []
        for edge in graph.edges:
            new_edge = edge.model_copy()
            modified_weight = edge.weight
            reasons = []
            
            # 1. Visual Tension
            vt = constraints.get(ConstraintKey.visual_tension, 0.5)
            if vt > 0.6:
                if edge.edge_type in [EdgeType.structural_analogy, EdgeType.visual_similarity]:
                    modified_weight *= (1 + (vt - 0.5))
                    reasons.append("Amplified by high visual tension.")
                elif edge.edge_type == EdgeType.functional_similarity:
                    modified_weight *= (1 - (vt - 0.5) * 0.5)
                    reasons.append("Reduced by high visual tension prioritizing form over function.")
                    
            # 2. Information Density
            id_val = constraints.get(ConstraintKey.information_density, 0.5)
            # Find if connected to specific high-density nodes (hardcoded for demo)
            high_density_targets = ["n-hc-swiss-rail", "n-hc-cockpit", "n-hc-medical-imaging"]
            nature_targets = ["n-hc-japanese-garden", "n-hc-butterfly"]
            
            if id_val > 0.6:
                if edge.source_id in high_density_targets or edge.target_id in high_density_targets:
                    modified_weight *= (1 + (id_val - 0.5))
                    reasons.append("Amplified by high information density connecting to dense patterns.")
                if edge.source_id in nature_targets or edge.target_id in nature_targets:
                    modified_weight *= (1 - (id_val - 0.5))
                    reasons.append("Reduced by high information density minimizing organic patterns.")
                    
            # 3. Accessibility
            acc = constraints.get(ConstraintKey.accessibility, 0.5)
            universal_targets = ["n-hc-triage", "n-hc-wayfinding", "n-hc-pharma"]
            if acc > 0.6:
                if edge.source_id in universal_targets or edge.target_id in universal_targets:
                    modified_weight *= (1 + (acc - 0.5))
                    reasons.append("Amplified by high accessibility requirements.")
                if edge.edge_type == EdgeType.behavioral_analogy:
                    modified_weight *= (1 + (acc - 0.5) * 0.5)
                    reasons.append("Behavioral analogies amplified for intuitive accessibility.")
                    
            # 4. Playfulness
            play = constraints.get(ConstraintKey.playfulness, 0.5)
            if play > 0.6:
                if edge.source_id in nature_targets or edge.target_id in nature_targets:
                    modified_weight *= (1 + (play - 0.5))
                    reasons.append("Amplified organic patterns due to playfulness.")
                if edge.edge_type == EdgeType.behavioral_analogy:
                    modified_weight *= (1 + (play - 0.5))
                if edge.edge_type == EdgeType.structural_analogy:
                    modified_weight *= (1 - (play - 0.5) * 0.5)
                    reasons.append("Reduced rigid structural analogies to favor playfulness.")
                    
            # 5. Material Scarcity
            mat = constraints.get(ConstraintKey.material_scarcity, 0.5)
            minimalist_targets = ["n-hc-bauhaus", "n-hc-japanese-garden"]
            if mat > 0.6:
                if edge.source_id in minimalist_targets or edge.target_id in minimalist_targets:
                    modified_weight *= (1 + (mat - 0.5))
                    reasons.append("Amplified minimalist patterns due to material scarcity.")
                if edge.edge_type == EdgeType.visual_similarity:
                    modified_weight *= (1 - (mat - 0.5))
                    reasons.append("Reduced superficial visual similarities under scarcity.")

            # Cap weight
            modified_weight = max(0.1, min(1.0, modified_weight))
            
            if abs(modified_weight - edge.weight) > 0.01:
                effects.append(ConstraintEffect(
                    edge_id=edge.id,
                    original_weight=edge.weight,
                    modified_weight=modified_weight,
                    reason=" ".join(reasons),
                    derivation=DerivationLabel.SYSTEM
                ))
            
            new_edge.weight = modified_weight
            modified_edges.append(new_edge)
            
        new_graph = graph.model_copy(deep=True)
        new_graph.edges = modified_edges
        
        # Update node importance
        from app.services.graph_service import GraphService
        gs = GraphService()
        gs._update_node_importance(new_graph)
        
        return new_graph, effects
