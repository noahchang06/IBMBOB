import { create } from 'zustand';
import type { 
  AppView, WorkspacePanel, PresetChallenge, ReasoningGraph, 
  GraphNode, GraphEdge, Inspiration, ConstraintSet, ConstraintEffect,
  DesignSystem, ExplanationResponse 
} from '../types';
import { DEFAULT_CONSTRAINTS } from '../types';

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
  setGraph: (g: ReasoningGraph | null) => void;
  selectNode: (n: GraphNode | null) => void;
  selectEdge: (e: GraphEdge | null) => void;
  setHoveredNode: (id: string | null) => void;

  // Inspirations (loaded with challenge)
  inspirations: Record<string, Inspiration>;
  setInspirations: (list: Inspiration[]) => void;
  addInspiration: (inspiration: Inspiration) => void;
  addNodeAndEdges: (node: GraphNode, edges: GraphEdge[]) => void;

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
  inspirations: {},
  constraints: { ...DEFAULT_CONSTRAINTS },
  constraintEffects: [],
  designSystem: null,
  currentExplanation: null,
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

  setConstraint: (key, value) => set((state) => ({
    constraints: { ...state.constraints, [key]: value }
  })),
  setConstraints: (constraints) => set({ constraints }),
  setConstraintEffects: (constraintEffects) => set({ constraintEffects }),

  setDesignSystem: (designSystem) => set({ designSystem }),

  setExplanation: (currentExplanation) => set({ currentExplanation }),
  setExplanationLoading: (explanationLoading) => set({ explanationLoading }),

  setGraphLoading: (graphLoading) => set({ graphLoading }),
  setConstraintsApplying: (constraintsApplying) => set({ constraintsApplying }),

  reset: () => set(initialState),
  resetWorkspace: () => set(workspaceState),
}));
