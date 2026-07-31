import { create } from 'zustand';
import type { 
  AppView, WorkspacePanel, PresetChallenge, ReasoningGraph, 
  GraphNode, GraphEdge, Inspiration, ConstraintSet, ConstraintEffect,
  DesignSystem, ExplanationResponse, ReasoningPath
} from '../types';
import { DEFAULT_CONSTRAINTS } from '../types';

export type HighlightedPathState = {
  nodeIds: string[];
  edgeIds: string[];
  edgeKeys: string[]; // `${source}->${target}` fallback when edge id absent
  pathIndex: number;
} | null;

interface AppState {
  // View state
  view: AppView;
  activePanel: WorkspacePanel;
  setView: (view: AppView) => void;
  setActivePanel: (panel: WorkspacePanel) => void;

  // Discovery
  challenges: PresetChallenge[];
  selectedChallenge: PresetChallenge | null;
  setChallenges: (c: PresetChallenge[]) => void;
  selectChallenge: (c: PresetChallenge | null) => void;

  // Graph
  graph: ReasoningGraph | null;
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  hoveredNode: string | null;
  highlightedPath: HighlightedPathState;
  setGraph: (g: ReasoningGraph | null) => void;
  selectNode: (n: GraphNode | null) => void;
  selectEdge: (e: GraphEdge | null) => void;
  setHoveredNode: (id: string | null) => void;
  setHighlightedPath: (path: HighlightedPathState) => void;
  clearHighlightedPath: () => void;
  highlightReasoningPath: (path: ReasoningPath, pathIndex?: number) => void;

  // Inspirations (loaded with challenge)
  inspirations: Record<string, Inspiration>;
  setInspirations: (list: Inspiration[]) => void;
  addInspiration: (inspiration: Inspiration) => void;
  addNodeAndEdges: (node: GraphNode, edges: GraphEdge[]) => void;
  addEdge: (edge: GraphEdge) => void;
  updateEdgeInStore: (edge: GraphEdge) => void;
  removeEdgeFromStore: (edgeId: string) => void;

  // Manual edge-link mode
  edgeLinkMode: boolean;
  edgeLinkSourceId: string | null;
  edgeLinkError: string | null;
  setEdgeLinkMode: (enabled: boolean) => void;
  setEdgeLinkSourceId: (id: string | null) => void;
  setEdgeLinkError: (msg: string | null) => void;

  // Constraints
  constraints: ConstraintSet;
  constraintEffects: ConstraintEffect[];
  setConstraint: (key: string, value: number) => void;
  setConstraints: (c: ConstraintSet) => void;
  setConstraintEffects: (e: ConstraintEffect[]) => void;

  // Design System
  designSystem: DesignSystem | null;
  setDesignSystem: (ds: DesignSystem | null) => void;

  // Explanations
  currentExplanation: ExplanationResponse | null;
  explanationLoading: boolean;
  setExplanation: (e: ExplanationResponse | null) => void;
  setExplanationLoading: (l: boolean) => void;

  // Loading states
  graphLoading: boolean;
  constraintsApplying: boolean;
  setGraphLoading: (l: boolean) => void;
  setConstraintsApplying: (l: boolean) => void;

  // Reset
  reset: () => void;
  resetWorkspace: () => void;
}

const workspaceState = {
  selectedChallenge: null,
  graph: null,
  selectedNode: null,
  selectedEdge: null,
  hoveredNode: null,
  highlightedPath: null as HighlightedPathState,
  inspirations: {},
  constraints: { ...DEFAULT_CONSTRAINTS },
  constraintEffects: [],
  designSystem: null,
  currentExplanation: null,
  edgeLinkMode: false,
  edgeLinkSourceId: null,
  edgeLinkError: null,
};

const initialState = {
  view: 'discovery' as AppView,
  activePanel: 'inspector' as WorkspacePanel,
  challenges: [],
  ...workspaceState,
  explanationLoading: false,
  graphLoading: false,
  constraintsApplying: false,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setView: (view) => set({ view }),
  setActivePanel: (activePanel) => set({ activePanel }),

  setChallenges: (challenges) => set({ challenges }),
  selectChallenge: (selectedChallenge) => set({ selectedChallenge }),

  setGraph: (graph) => set({ graph }),
  selectNode: (selectedNode) => set({ selectedNode, selectedEdge: null }),
  selectEdge: (selectedEdge) => set({ selectedEdge, selectedNode: null }),
  setHoveredNode: (hoveredNode) => set({ hoveredNode }),
  setHighlightedPath: (highlightedPath) => set({ highlightedPath }),
  clearHighlightedPath: () => set({ highlightedPath: null }),
  highlightReasoningPath: (path, pathIndex = 0) => {
    const nodeIds = (path.nodes || []).map(n => n.id).filter(Boolean);
    const edgeIds = (path.edges || [])
      .map(e => e.id)
      .filter((id): id is string => typeof id === 'string' && id.length > 0);
    const edgeKeys = (path.edges || [])
      .map(e => `${e.source}->${e.target}`)
      .filter(k => !k.startsWith('->') && !k.endsWith('->'));
    if (!nodeIds.length || (!edgeIds.length && !edgeKeys.length)) {
      set({ highlightedPath: null });
      return;
    }
    set({
      highlightedPath: { nodeIds, edgeIds, edgeKeys, pathIndex },
    });
  },

  setInspirations: (list) => {
    const map: Record<string, Inspiration> = {};
    list.forEach(item => {
      map[item.id] = item;
    });
    set({ inspirations: map });
  },

  addInspiration: (inspiration) => set((state) => ({
    inspirations: { ...state.inspirations, [inspiration.id]: inspiration }
  })),

  addNodeAndEdges: (node, edges) => set((state) => ({
    graph: state.graph
      ? { 
          ...state.graph, 
          nodes: [...state.graph.nodes, node],
          edges: [...state.graph.edges, ...edges],
        }
      : null
  })),

  addEdge: (edge) => set((state) => ({
    graph: state.graph
      ? { ...state.graph, edges: [...state.graph.edges, edge] }
      : null,
  })),

  updateEdgeInStore: (edge) => set((state) => ({
    graph: state.graph
      ? {
          ...state.graph,
          edges: state.graph.edges.map(e => (e.id === edge.id ? edge : e)),
        }
      : null,
    selectedEdge: state.selectedEdge?.id === edge.id ? edge : state.selectedEdge,
  })),

  removeEdgeFromStore: (edgeId) => set((state) => ({
    graph: state.graph
      ? {
          ...state.graph,
          edges: state.graph.edges.filter(e => e.id !== edgeId),
        }
      : null,
    selectedEdge: state.selectedEdge?.id === edgeId ? null : state.selectedEdge,
  })),

  setEdgeLinkMode: (edgeLinkMode) => set({
    edgeLinkMode,
    edgeLinkSourceId: null,
    edgeLinkError: null,
  }),
  setEdgeLinkSourceId: (edgeLinkSourceId) => set({ edgeLinkSourceId }),
  setEdgeLinkError: (edgeLinkError) => set({ edgeLinkError }),

  setConstraint: (key, value) => set((state) => ({
    constraints: { ...state.constraints, [key]: value }
  })),
  setConstraints: (constraints) => set({ constraints }),
  setConstraintEffects: (constraintEffects) => set({ constraintEffects }),

  setDesignSystem: (designSystem) => set({ designSystem }),

  setExplanation: (currentExplanation) => set({
    currentExplanation,
    highlightedPath: null,
  }),
  setExplanationLoading: (explanationLoading) => set({ explanationLoading }),

  setGraphLoading: (graphLoading) => set({ graphLoading }),
  setConstraintsApplying: (constraintsApplying) => set({ constraintsApplying }),

  reset: () => set(initialState),
  resetWorkspace: () => set(workspaceState),
}));
