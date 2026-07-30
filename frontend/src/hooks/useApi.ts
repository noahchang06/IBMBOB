import type {
  PresetChallenge, ReasoningGraph, Inspiration, ConstraintSet,
  ConstraintEffect, DesignSystem, ExplanationResponse, ExportPackage,
  GraphNode, GraphEdge
} from '../types';

// Use relative path so Vite's dev proxy works and production builds
// can be served behind any base path without env config.
const API_BASE = '/api';

export function useApi() {
  const fetchChallenges = async (): Promise<PresetChallenge[]> => {
    const res = await fetch(`${API_BASE}/challenges`);
    if (!res.ok) throw new Error('Failed to fetch challenges');
    const data = await res.json();
    return data.challenges;
  };

  const buildGraph = async (
    challengeId: string
  ): Promise<{ graph: ReasoningGraph; inspirations: Inspiration[]; design_system: DesignSystem }> => {
    const res = await fetch(`${API_BASE}/graph/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challenge_id: challengeId }),
    });
    if (!res.ok) throw new Error('Failed to build graph');
    return res.json();
  };

  const applyConstraints = async (
    graph: ReasoningGraph,
    constraints: ConstraintSet
  ): Promise<{ graph: ReasoningGraph; effects: ConstraintEffect[]; design_system: DesignSystem }> => {
    const res = await fetch(`${API_BASE}/graph/apply-constraints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph, constraints }),
    });
    if (!res.ok) throw new Error('Failed to apply constraints');
    return res.json();
  };

  const explainEdge = async (
    edgeId: string,
    source: GraphNode,
    target: GraphNode,
    edge: GraphEdge
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain/edge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edge_id: edgeId, source, target, edge }),
    });
    if (!res.ok) throw new Error('Failed to explain edge');
    return res.json();
  };

  const explainNode = async (
    nodeId: string,
    inspiration: Inspiration
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_type: 'node', target_id: nodeId, context: { inspiration } }),
    });
    if (!res.ok) throw new Error('Failed to explain node');
    return res.json();
  };

  const explainDesignDecision = async (
    decision: string,
    context: Record<string, unknown>
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_type: 'design_decision', target_id: decision, context }),
    });
    if (!res.ok) throw new Error('Failed to explain design decision');
    return res.json();
  };

  /**
   * Export — payload must match backend ExportRequestBody:
   * { challenge_id, graph, constraints, inspiration_ids? }
   */
  const exportPackage = async (
    challengeId: string,
    graph: ReasoningGraph,
    constraints: ConstraintSet,
    inspirationIds: string[]
  ): Promise<ExportPackage> => {
    const res = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        challenge_id: challengeId,
        graph,
        constraints,
        inspiration_ids: inspirationIds,
      }),
    });
    if (!res.ok) throw new Error('Failed to export');
    return res.json();
  };

  const createChallenge = async (challengeData: any): Promise<PresetChallenge> => {
    const res = await fetch(`${API_BASE}/challenges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(challengeData),
    });
    if (!res.ok) throw new Error('Failed to create challenge');
    return res.json();
  };

  const deleteChallenge = async (challengeId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete challenge');
  };

  const addInspiration = async (challengeId: string, inspirationData: any): Promise<{ inspiration: Inspiration, new_edges: GraphEdge[] }> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/inspirations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inspirationData),
    });
    if (!res.ok) throw new Error('Failed to add inspiration');
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
    createChallenge,
    deleteChallenge,
    addInspiration,
  };
  }
