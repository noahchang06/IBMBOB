// === Derivation Labels ===
export type DerivationLabel = 'CURATED' | 'SYSTEM' | 'RETRIEVED' | 'AI';

export interface LabeledValue<T> {
  value: T;
  derivation: DerivationLabel;
}

// === Domains ===
export type DomainType = 
  | 'architecture' | 'biology' | 'music' | 'industrial_design' 
  | 'psychology' | 'nature' | 'fashion' | 'engineering' 
  | 'history' | 'film';

export const DOMAIN_COLORS: Record<DomainType, string> = {
  architecture: '#E8A87C',
  biology: '#41B3A3',
  music: '#C38D9E',
  industrial_design: '#85DCB8',
  psychology: '#E27D60',
  nature: '#659B5E',
  fashion: '#D4A5A5',
  engineering: '#5B8BA0',
  history: '#C9B1FF',
  film: '#F3C178',
};

export const DOMAIN_LABELS: Record<DomainType, string> = {
  architecture: 'Architecture',
  biology: 'Biology',
  music: 'Music',
  industrial_design: 'Industrial Design',
  psychology: 'Psychology',
  nature: 'Nature',
  fashion: 'Fashion',
  engineering: 'Engineering',
  history: 'History',
  film: 'Film',
};

// === Inspirations ===
export interface TransferablePrinciple {
  name: string;
  description: string;
  source_domain: DomainType;
  derivation: DerivationLabel;
}

export interface Inspiration {
  id: string;
  name: string;
  domain: DomainType;
  description: string;
  historical_context: string;
  key_principles: TransferablePrinciple[];
  transferable_lessons: string[];
  related_concepts: string[];
  design_implications: string[];
  image_url?: string;
  derivation: DerivationLabel;
}

// === Graph ===
export type EdgeType = 
  | 'transferable_principle' | 'functional_similarity' 
  | 'structural_analogy' | 'visual_similarity' | 'behavioral_analogy';

export const EDGE_TYPE_COLORS: Record<EdgeType, string> = {
  transferable_principle: '#E8A87C',
  functional_similarity: '#41B3A3',
  structural_analogy: '#C38D9E',
  visual_similarity: '#85DCB8',
  behavioral_analogy: '#E27D60',
};

export const EDGE_TYPE_LABELS: Record<EdgeType, string> = {
  transferable_principle: 'Transferable Principle',
  functional_similarity: 'Functional Similarity',
  structural_analogy: 'Structural Analogy',
  visual_similarity: 'Visual Similarity',
  behavioral_analogy: 'Behavioral Analogy',
};

export interface GraphNode {
  id: string;
  inspiration_id: string;
  label: string;
  domain: DomainType;
  importance: number; // 0-1
  x?: number;
  y?: number;
  derivation: DerivationLabel;
}

export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  weight: number; // 0-1
  relationship_description: string;
  transferable_insight: string;
  evidence: string[];
  derivation: DerivationLabel;
}

export interface ReasoningGraph {
  id: string;
  challenge_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// === Constraints ===
export type ConstraintKey = 
  | 'visual_tension' | 'information_density' | 'accessibility' 
  | 'playfulness' | 'material_scarcity';

export const CONSTRAINT_META: Record<ConstraintKey, { label: string; description: string; icon: string }> = {
  visual_tension: {
    label: 'Visual Tension',
    description: 'Amplifies contrast, asymmetry, and dynamic composition',
    icon: '◆',
  },
  information_density: {
    label: 'Information Density',
    description: 'Controls hierarchy depth, spacing, and component complexity',
    icon: '▦',
  },
  accessibility: {
    label: 'Accessibility',
    description: 'Strengthens universal design patterns and contrast ratios',
    icon: '◎',
  },
  playfulness: {
    label: 'Playfulness',
    description: 'Favors organic shapes, motion, and unexpected combinations',
    icon: '✦',
  },
  material_scarcity: {
    label: 'Material Scarcity',
    description: 'Reduces palette, favors minimalism and reduction',
    icon: '◇',
  },
};

export type ConstraintSet = Record<ConstraintKey, number>;

export const DEFAULT_CONSTRAINTS: ConstraintSet = {
  visual_tension: 0.5,
  information_density: 0.5,
  accessibility: 0.5,
  playfulness: 0.5,
  material_scarcity: 0.5,
};

export interface ConstraintEffect {
  edge_id: string;
  original_weight: number;
  modified_weight: number;
  reason: string;
  derivation: DerivationLabel;
}

// === Design System ===
export interface TypeScale {
  heading_family: string;
  heading_weight: number;
  body_family: string;
  body_weight: number;
  base_size: number;
  scale_ratio: number;
  line_height: number;
}

export interface ColorToken {
  name: string;
  hex: string;
  role: 'primary' | 'secondary' | 'accent' | 'surface' | 'text' | 'error' | 'warning' | 'success';
  contrast_ratio?: number;
  derivation: DerivationLabel;
}

export interface Palette {
  colors: ColorToken[];
  background: string;
  foreground: string;
  derivation: DerivationLabel;
}

export interface SpacingScale {
  base: number;
  scale: number[];
  unit: string;
}

export interface ComponentStyle {
  name: string;
  border_radius: string;
  padding: string;
  shadow: string;
  notes: string;
}

export interface DesignSystem {
  typography: TypeScale;
  palette: Palette;
  spacing: SpacingScale;
  components: ComponentStyle[];
  motion_duration_ms: number;
  motion_easing: string;
  wcag_level: string;
  derivation: DerivationLabel;
}

// === Explanations ===
export interface ReasoningStep {
  step_number: number;
  description: string;
  derivation: DerivationLabel;
}

export interface ExplanationChain {
  retrieved_knowledge: ReasoningStep[];
  deterministic_reasoning: ReasoningStep[];
  ai_interpretation: ReasoningStep[];
}

export interface ExplanationResponse {
  target_type: string;
  target_id: string;
  chain: ExplanationChain;
  summary: string;
}

// === Challenges ===
export interface PresetChallenge {
  id: string;
  name: string;
  subtitle: string;
  description: string;
  domains: DomainType[];
  node_count: number;
  tags: string[];
}

// === Export ===
export interface ExportRequest {
  challenge_name: string;
  design_tokens: DesignSystem;
  graph: ReasoningGraph;
  selected_inspirations: Inspiration[];
  constraints: ConstraintSet;
}

export interface ExportPackage {
  challenge_name: string;
  design_tokens: DesignSystem;
  graph: ReasoningGraph;
  selected_inspirations: Inspiration[];
  constraints: ConstraintSet;
  reasoning_summary_markdown: string;
}

// === UI State ===
export type AppView = 'discovery' | 'workspace';
export type WorkspacePanel = 'inspector' | 'constraints' | 'design-system' | 'explainable' | 'export';
