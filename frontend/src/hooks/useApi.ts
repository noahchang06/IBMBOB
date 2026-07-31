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
    edge: GraphEdge,
    graph?: ReasoningGraph | null,
    inspirations?: Inspiration[],
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain/edge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        edge_id: edgeId,
        source,
        target,
        edge,
        graph: graph ?? undefined,
        inspirations: inspirations ?? undefined,
      }),
    });
    if (!res.ok) throw new Error('Failed to explain edge');
    return res.json();
  };

  const explainNode = async (
    nodeId: string,
    inspiration: Inspiration,
    graph?: ReasoningGraph | null,
    node?: GraphNode | null,
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'node',
        target_id: nodeId,
        context: {
          inspiration,
          node: node ?? undefined,
          graph: graph ?? undefined,
          inspirations: inspiration ? [inspiration] : undefined,
        },
      }),
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

  const explainCompare = async (
    source: GraphNode,
    target: GraphNode,
    graph?: ReasoningGraph | null,
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source,
        target,
        graph: graph ?? undefined,
      }),
    });
    if (!res.ok) throw new Error('Failed to compare nodes');
    return res.json();
  };

  const explainRecommend = async (
    graph?: ReasoningGraph | null,
    focusNodeIds?: string[],
  ): Promise<ExplanationResponse> => {
    const res = await fetch(`${API_BASE}/explain/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        graph: graph ?? undefined,
        focus_node_ids: focusNodeIds ?? [],
      }),
    });
    if (!res.ok) throw new Error('Failed to recommend next idea');
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

  const addInspiration = async (
    challengeId: string,
    inspirationData: {
      name: string;
      domain: string;
      description: string;
      connect_to_inspiration_id?: string | null;
      connect_context?: 'selected' | 'initiation' | null;
    }
  ): Promise<{ inspiration: Inspiration, new_edges: GraphEdge[] }> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/inspirations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inspirationData),
    });
    if (!res.ok) {
      let detail = 'Failed to add inspiration';
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch {
        // keep default message
      }
      throw new Error(detail);
    }
    return res.json();
  };

  const createEdge = async (
    challengeId: string,
    edgeData: {
      source_id: string;
      target_id: string;
      edge_type?: string;
      relationship_label?: string;
      relationship_description?: string;
      transferable_insight?: string;
      confidence?: number | null;
      derivation?: string;
      from_ai_suggestion?: boolean;
      suggestion_edited?: boolean;
    }
  ): Promise<GraphEdge> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/edges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edgeData),
    });
    if (!res.ok) {
      let detail = 'Failed to create edge';
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch {
        // keep default message
      }
      throw new Error(detail);
    }
    return res.json();
  };

  const suggestRelationships = async (
    challengeId: string,
    payload: {
      source_id: string;
      target_id: string;
      graph?: unknown;
      inspirations?: unknown[];
    }
  ): Promise<{
    suggestions: Array<{
      edge_type: string;
      relationship_label: string;
      relationship_description: string;
      confidence?: number | null;
    }>;
  }> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/edges/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let detail = 'Failed to get Granite suggestions';
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch {
        // keep default
      }
      throw new Error(detail);
    }
    return res.json();
  };

  const updateEdge = async (
    challengeId: string,
    edgeId: string,
    edgeData: {
      edge_type?: string;
      relationship_label?: string;
      relationship_description?: string;
      transferable_insight?: string;
      confidence?: number | null;
      weight?: number;
    }
  ): Promise<GraphEdge> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/edges/${edgeId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edgeData),
    });
    if (!res.ok) {
      let detail = 'Failed to update edge';
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch {
        // keep default message
      }
      throw new Error(detail);
    }
    return res.json();
  };

  const deleteEdge = async (challengeId: string, edgeId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/challenges/${challengeId}/edges/${edgeId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      let detail = 'Failed to delete edge';
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch {
        // keep default
      }
      throw new Error(detail);
    }
  };

  return {
    fetchChallenges,
    buildGraph,
    applyConstraints,
    explainEdge,
    explainNode,
    explainDesignDecision,
    explainCompare,
    explainRecommend,
    exportPackage,
    createChallenge,
    deleteChallenge,
    addInspiration,
    createEdge,
    suggestRelationships,
    updateEdge,
    deleteEdge,
  };
  }
