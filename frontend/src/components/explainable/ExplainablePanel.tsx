import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import type { ReasoningPath, ReasoningPathEdge } from '../../types';

// ── Provenance tier configuration ─────────────────────────────────────────────
const TIER_CONFIG = {
  retrieved_knowledge: {
    num: 1,
    derivation: 'RETRIEVED' as const,
    label: 'Retrieved Knowledge',
    sublabel: 'Curated graph data',
    color: '#f0b88a',
    bg: 'rgba(232,168,124,0.10)',
    border: 'rgba(232,168,124,0.28)',
    borderL: '#f0b88a',
  },
  deterministic_reasoning: {
    num: 2,
    derivation: 'SYSTEM' as const,
    label: 'Deterministic Reasoning',
    sublabel: 'Constraint engine output',
    color: '#5fd4c0',
    bg: 'rgba(65,179,163,0.10)',
    border: 'rgba(65,179,163,0.28)',
    borderL: '#5fd4c0',
  },
  ai_interpretation: {
    num: 3,
    derivation: 'AI' as const,
    label: 'IBM Granite Interpretation',
    sublabel: 'Qualitative AI synthesis — not deterministic',
    color: '#d9a4b5',
    bg: 'rgba(195,141,158,0.10)',
    border: 'rgba(195,141,158,0.28)',
    borderL: '#d9a4b5',
    isAI: true,
  },
} as const;

type TierKey = keyof typeof TIER_CONFIG;

const HUMAN_PROVENANCE: Record<string, string> = {
  MANUAL: 'User-authored',
  SYSTEM: 'System-generated',
  CURATED: 'Context-derived',
  AI: 'AI suggestion',
  AI_ACCEPTED: 'AI suggestion accepted',
  RETRIEVED: 'Context-derived',
};

function humanProvenance(derivation?: string | null): string {
  if (!derivation) return 'Unknown provenance';
  return HUMAN_PROVENANCE[derivation.toUpperCase()] || derivation;
}

function ProvenanceLegend() {
  return (
    <details className="group">
      <summary className="cursor-pointer text-[10px] font-mono uppercase tracking-wider text-text-muted hover:text-text-secondary transition-colors select-none">
        Provenance key ▸
      </summary>
      <div className="mt-2 space-y-1.5 text-[11px] text-text-muted leading-snug">
        {([
          ['CURATED', '#8ba4ff', 'Peer-reviewed facts from the knowledge base'],
          ['RETRIEVED', '#f0b88a', 'Matched graph edges and evidence snippets'],
          ['SYSTEM', '#5fd4c0', 'Deterministic engine math — reproducible'],
          ['MANUAL', '#c3c8dc', 'User-authored relationship evidence'],
          ['AI', '#d9a4b5', 'IBM Granite suggestion — qualitative only'],
          ['AI_ACCEPTED', '#e8c4d0', 'User-confirmed AI relationship suggestion'],
        ] as const).map(([label, color, desc]) => (
          <div key={label} className="flex items-start gap-2">
            <span
              className="mt-0.5 shrink-0 font-mono text-[9px] px-1 py-0.5 rounded border"
              style={{ color, borderColor: color + '55', background: color + '18' }}
            >
              [{label}]
            </span>
            <span>{desc}</span>
          </div>
        ))}
      </div>
    </details>
  );
}

function ReasoningPathCard({
  path,
  index,
  isHighlighted,
  onHighlight,
  onClearHighlight,
  onSelectNode,
  onSelectEdge,
}: {
  path: ReasoningPath;
  index: number;
  isHighlighted: boolean;
  onHighlight: () => void;
  onClearHighlight: () => void;
  onSelectNode: (nodeId: string) => void;
  onSelectEdge: (edge: ReasoningPathEdge) => void;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const nodes = path.nodes || [];
  const edges = path.edges || [];

  if (!nodes.length || !edges.length) return null;

  return (
    <div
      className="rounded-xl border p-3 space-y-3"
      style={{
        borderColor: isHighlighted ? 'rgba(65,179,163,0.55)' : 'var(--color-border)',
        background: isHighlighted ? 'rgba(65,179,163,0.08)' : 'var(--color-surface-2)',
      }}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-mono uppercase tracking-wider text-accent">
          Reasoning path {index + 1}
          {edges.length > 1 ? ` · ${edges.length} hops` : ' · direct'}
        </span>
        {isHighlighted ? (
          <button
            type="button"
            onClick={onClearHighlight}
            className="text-[10px] px-2 py-1 rounded border border-border text-text-muted hover:text-text-primary"
          >
            Clear highlight
          </button>
        ) : (
          <button
            type="button"
            onClick={onHighlight}
            className="text-[10px] px-2 py-1 rounded border border-accent/40 text-accent hover:bg-accent/10"
          >
            Highlight path in graph
          </button>
        )}
      </div>

      {/* Compact directed path: Idea A — Builds on → Idea B */}
      <div className="flex flex-col gap-1" role="list" aria-label={`Reasoning path ${index + 1}`}>
        {nodes.map((node, i) => {
          const edge: ReasoningPathEdge | undefined = edges[i];
          return (
            <div key={`${node.id}-${i}`} role="listitem">
              <button
                type="button"
                onClick={() => onSelectNode(node.id)}
                className="text-left text-sm font-medium text-text-primary hover:text-accent underline-offset-2 hover:underline"
              >
                {node.title}
              </button>
              {edge && (
                <div className="flex items-center gap-2 pl-3 py-1 text-xs text-text-muted">
                  <span aria-hidden="true">—</span>
                  <button
                    type="button"
                    onClick={() => onSelectEdge(edge)}
                    className="font-medium text-accent hover:underline"
                    title="Open edge inspector"
                  >
                    {edge.relationship_label}
                  </button>
                  <span aria-hidden="true">→</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <details
        open={detailsOpen}
        onToggle={e => setDetailsOpen((e.target as HTMLDetailsElement).open)}
      >
        <summary className="cursor-pointer text-[10px] font-mono uppercase tracking-wider text-text-muted">
          Relationship details ▸
        </summary>
        <div className="mt-2 space-y-2">
          {edges.map((edge, ei) => (
            <div key={edge.id || `${edge.source}-${edge.target}-${ei}`} className="text-xs bg-surface-1 border border-border rounded-lg p-2">
              <div className="font-medium text-text-primary mb-1">
                {edge.relationship_label}
              </div>
              <p className="text-text-secondary mb-1">
                {edge.relationship_description?.trim() || 'No relationship description recorded.'}
              </p>
              <div className="flex flex-wrap gap-2 text-[10px] text-text-muted font-mono">
                <span>{humanProvenance(edge.derivation)}</span>
                {typeof edge.confidence === 'number' && (
                  <span>confidence {(edge.confidence * 100).toFixed(0)}%</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

export function ExplainablePanel() {
  const {
    currentExplanation,
    explanationLoading,
    selectedNode,
    selectedEdge,
    graph,
    highlightedPath,
    selectNode,
    selectEdge,
    setActivePanel,
    highlightReasoningPath,
    clearHighlightedPath,
  } = useAppStore();

  const targetLabel = selectedEdge
    ? `Edge: ${selectedEdge.relationship_label || selectedEdge.edge_type.replace(/_/g, ' ')}`
    : selectedNode
      ? `Node: ${selectedNode.label}`
      : null;

  if (explanationLoading) {
    return (
      <div className="p-6 space-y-6" aria-busy="true" aria-label="Loading explanation from IBM Granite">
        {targetLabel && (
          <div className="text-xs font-mono text-text-muted bg-surface-1 px-3 py-2 rounded border border-border flex items-center gap-2">
            <div className="w-3 h-3 border-2 border-surface-3 border-t-[#d9a4b5] rounded-full animate-spin shrink-0" aria-hidden="true" />
            Querying IBM Granite for {targetLabel}…
          </div>
        )}
        <div className="animate-pulse space-y-6" aria-hidden="true">
          <div className="h-7 bg-surface-2 rounded w-1/3" />
          {[1, 2, 3].map(i => (
            <div key={i} className="space-y-3">
              <div className="h-4 bg-surface-2 rounded w-1/4" />
              <div className="h-20 bg-surface-2 rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!currentExplanation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-8 text-center h-full gap-6">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1" className="opacity-40">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-2.82 1.17V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-2.82-1.17l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
        <div className="space-y-2">
          <p className="text-sm">Select "Explain with AI" on a node or edge.</p>
          <p className="text-xs text-text-muted">
            The reasoning trace shows [RETRIEVED] knowledge, [SYSTEM] computation,
            then IBM Granite's [AI] interpretation — each clearly labelled.
          </p>
        </div>
        <div className="w-full border-t border-border pt-4">
          <ProvenanceLegend />
        </div>
      </div>
    );
  }

  const { chain, summary } = currentExplanation;
  const paths = (currentExplanation.paths || []).filter(
    p => (p.nodes?.length ?? 0) > 0 && (p.edges?.length ?? 0) > 0,
  );

  const focusPathNode = (nodeId: string) => {
    const node = graph?.nodes.find(n => n.id === nodeId);
    if (node) {
      selectNode(node);
    }
  };

  const focusPathEdge = (pathEdge: ReasoningPathEdge) => {
    if (!graph) return;
    let edge = pathEdge.id
      ? graph.edges.find(e => e.id === pathEdge.id)
      : undefined;
    if (!edge) {
      edge = graph.edges.find(
        e => e.source_id === pathEdge.source && e.target_id === pathEdge.target,
      );
    }
    if (edge) {
      selectEdge(edge);
      setActivePanel('inspector');
    }
  };

  return (
    <div className="p-6 space-y-8 pb-20">
      {targetLabel && (
        <div className="text-xs font-mono text-text-muted bg-surface-1 px-3 py-2 rounded border border-border flex items-center justify-between">
          <span>Explaining → <span className="text-text-secondary">{targetLabel}</span></span>
          <DerivationBadge label="AI" />
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold mb-3">Reasoning Trace</h2>
        <div
          className="p-4 rounded-xl border"
          style={{
            background: 'rgba(195,141,158,0.08)',
            borderColor: 'rgba(195,141,158,0.3)',
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color: '#d9a4b5' }}>
                IBM Granite — AI Summary
              </span>
            </div>
            <DerivationBadge label="AI" />
          </div>
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{summary}</p>
          <p className="mt-2 text-[10px] text-text-muted italic">
            This paragraph is IBM Granite's qualitative interpretation. It does not
            affect any deterministic output.
          </p>
        </div>
      </div>

      {/* Visual reasoning paths from backend — never fabricated client-side */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-1">
          Supporting relationship paths
        </h3>
        {paths.length > 0 ? (
          <div className="space-y-3">
            {paths.map((path, index) => (
              <ReasoningPathCard
                key={`path-${index}-${path.nodes.map(n => n.id).join('-')}`}
                path={path}
                index={index}
                isHighlighted={highlightedPath?.pathIndex === index}
                onHighlight={() => highlightReasoningPath(path, index)}
                onClearHighlight={clearHighlightedPath}
                onSelectNode={focusPathNode}
                onSelectEdge={focusPathEdge}
              />
            ))}
            {highlightedPath && (
              <button
                type="button"
                onClick={clearHighlightedPath}
                className="w-full text-xs py-2 rounded-lg border border-border text-text-muted hover:text-text-primary"
              >
                Clear highlight
              </button>
            )}
          </div>
        ) : (
          <p className="text-xs text-text-muted leading-relaxed">
            No meaningful relationship path is recorded for this conclusion.
            A path visualization is not shown because inventing one would be misleading.
          </p>
        )}
      </div>

      <div className="border-t border-border pt-4">
        <ProvenanceLegend />
      </div>

      <div className="space-y-8 relative">
        {(Object.entries(chain) as [TierKey, typeof chain[TierKey]][]).map(([tierKey, steps]) => {
          if (!steps.length) return null;
          const cfg = TIER_CONFIG[tierKey];
          const isAI = 'isAI' in cfg && cfg.isAI;

          return (
            <div
              key={tierKey}
              className="p-4 rounded-2xl border transition-all"
              style={{
                background: cfg.bg,
                borderColor: cfg.border,
              }}
            >
              <div className="flex items-center justify-between pb-3 border-b border-border/50 mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                    style={{ background: 'var(--color-surface-2)', border: `1px solid ${cfg.border}`, color: cfg.color }}
                  >
                    {cfg.num}
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm leading-tight flex items-center gap-2" style={{ color: cfg.color }}>
                      <span>{cfg.label}</span>
                    </h3>
                    <p className="text-[11px] text-text-muted">{cfg.sublabel}</p>
                  </div>
                </div>
                <DerivationBadge label={cfg.derivation} />
              </div>

              <div className="space-y-3">
                {steps.map(step => (
                  <div
                    key={step.step_number}
                    className="p-3.5 rounded-xl border bg-surface-1/90"
                    style={{
                      borderColor: isAI ? 'rgba(195,141,158,0.35)' : 'var(--color-border)',
                      borderLeftWidth: 3,
                      borderLeftColor: cfg.borderL,
                    }}
                  >
                    <div className="flex justify-between items-start mb-1.5">
                      <span className="text-[10px] text-text-muted font-mono uppercase font-semibold">
                        Step {step.step_number}
                      </span>
                      <DerivationBadge label={step.derivation} />
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap">
                      {step.description}
                    </p>
                    {isAI && (
                      <p className="mt-2 text-[10px] text-text-muted italic border-t border-border/40 pt-1.5">
                        IBM Granite interpretation — qualitative synthesis, does not alter graph calculation.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-border pt-4 text-center space-y-2">
        <p className="text-[10px] text-text-muted leading-relaxed">
          <span
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-mono align-middle"
            style={{ borderColor: 'rgba(195,141,158,0.3)', background: 'rgba(195,141,158,0.08)', color: '#d9a4b5' }}
          >
            [AI] IBM Granite
          </span>
          {' '}interprets.
        </p>
        <p className="text-[10px] text-text-muted leading-relaxed">
          <span
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-mono align-middle"
            style={{ borderColor: 'rgba(65,179,163,0.3)', background: 'rgba(65,179,163,0.08)', color: '#5fd4c0' }}
          >
            [SYSTEM]
          </span>
          {' '}outputs are deterministic and reproducible.
        </p>
      </div>
    </div>
  );
}
