import type { 
  PresetChallenge, ReasoningGraph, Inspiration, ConstraintSet,
  ConstraintEffect, DesignSystem, ExplanationResponse, ExportPackage, ExportRequest, GraphNode, GraphEdge 
} from '../types';

const API_BASE = 'http://localhost:8000/api';

export function useApi() {
  const fetchChallenges = async (): Promise<PresetChallenge[]> => {
    const res = await fetch(`${API_BASE}/challenges`);
    if (!res.ok) throw new Error('Failed to fetch challenges');
    const data = await res.json();
    return data.challenges;
  };

  const buildGraph = async (challengeId: string): Promise<{ graph: ReasoningGraph; inspirations: Inspiration[]; design_system: DesignSystem }> => {
    const res = await fetch(`${API_BASE}/graph/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challenge_id: challengeId })
    });
    if (!res.ok) throw new Error('Failed to build graph');
    return res.json();
  };

  const applyConstraints = async (graph: ReasoningGraph, constraints: ConstraintSet): Promise<{ graph: ReasoningGraph; effects: ConstraintEffect[]; design_system: DesignSystem }> => {
    const res = await fetch(`${API_BASE}/graph/apply-constraints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph, constraints })
    });
    if (!res.ok) throw new Error('Failed to apply constraints');
    return res.json();
  };

  const explainEdge = async (edgeId: string, source: GraphNode, target: GraphNode, edge: GraphEdge): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain/edge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edge_id: edgeId, source, target, edge })
    });
    if (!res.ok) throw new Error('Failed to explain edge');
    return res.json();
  };

  const explainNode = async (nodeId: string, inspiration: Inspiration): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_type: 'node', target_id: nodeId, context: { inspiration } })
    });
    if (!res.ok) throw new Error('Failed to explain node');
    return res.json();
  };

  const explainDesignDecision = async (decision: string, context: Record<string, unknown>): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_type: 'design_decision', target_id: decision, context })
    });
    if (!res.ok) throw new Error('Failed to explain design decision');
    return res.json();
  };

  const exportPackage = async (data: ExportRequest): Promise<ExportPackage> => {
    const res = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to export');
    return res.json();
  };

  return {
    fetchChallenges,
    buildGraph,
    applyConstraints,
    explainEdge,
    explainNode,
    explainDesignDecision,
    exportPackage,
  };
}
