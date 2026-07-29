import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';

// ── Provenance tier configuration ─────────────────────────────────────────────
// The ordering here defines the visual order in the reasoning trace:
//   1. [RETRIEVED]  — facts pulled from the curated knowledge base
//   2. [SYSTEM]     — deterministic outputs from the constraint / centrality engine
//   3. [AI]         — IBM Granite qualitative interpretation (clearly labelled)
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

// ── Provenance explanation tooltip ────────────────────────────────────────────
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
          ['AI', '#d9a4b5', 'IBM Granite interpretation — qualitative only'],
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

export function ExplainablePanel() {
  const { currentExplanation, explanationLoading, selectedNode, selectedEdge } = useAppStore();

  const targetLabel = selectedEdge
    ? `Edge: ${selectedEdge.edge_type.replace(/_/g, ' ')}`
    : selectedNode
      ? `Node: ${selectedNode.label}`
      : null;

  // ── Loading ────────────────────────────────────────────────────────────────
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

  // ── Empty state ────────────────────────────────────────────────────────────
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

  // ── Full trace ────────────────────────────────────────────────────────────
  return (
    <div className="p-6 space-y-8 pb-20">
      {/* Target context */}
      {targetLabel && (
        <div className="text-xs font-mono text-text-muted bg-surface-1 px-3 py-2 rounded border border-border flex items-center justify-between">
          <span>Explaining → <span className="text-text-secondary">{targetLabel}</span></span>
          <DerivationBadge label="AI" />
        </div>
      )}

      {/* AI Summary — explicitly labelled as AI-generated */}
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
          <p className="text-sm text-text-secondary leading-relaxed">{summary}</p>
          <p className="mt-2 text-[10px] text-text-muted italic">
            This paragraph is IBM Granite's qualitative interpretation. It does not
            affect any deterministic output.
          </p>
        </div>
      </div>

      {/* Provenance legend (collapsed by default) */}
      <div className="border-t border-border pt-4">
        <ProvenanceLegend />
      </div>

      {/* Three-tier provenance chain */}
      <div className="space-y-8 relative before:absolute before:left-5 before:top-0 before:bottom-0 before:w-px before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
        {(Object.entries(chain) as [TierKey, typeof chain[TierKey]][]).map(([tierKey, steps]) => {
          if (!steps.length) return null;
          const cfg = TIER_CONFIG[tierKey];
          const isAI = 'isAI' in cfg && cfg.isAI;

          return (
            <div key={tierKey} className="relative z-10">
              {/* Tier header */}
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                  style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.color }}
                >
                  {cfg.num}
                </div>
                <div>
                  <h3 className="font-semibold leading-tight" style={{ color: cfg.color }}>
                    {cfg.label}
                  </h3>
                  <p className="text-[10px] text-text-muted mt-0.5">{cfg.sublabel}</p>
                </div>
              </div>

              {/* Steps */}
              <div className="ml-14 space-y-3">
                {steps.map(step => (
                  <div
                    key={step.step_number}
                    className="p-4 rounded-xl border"
                    style={{
                      background: isAI ? 'rgba(195,141,158,0.06)' : 'var(--color-surface-1)',
                      borderColor: isAI ? 'rgba(195,141,158,0.25)' : 'var(--color-border)',
                      borderLeftWidth: 2,
                      borderLeftColor: cfg.borderL,
                    }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[10px] text-text-muted font-mono uppercase">
                        Step {step.step_number}
                      </span>
                      <DerivationBadge label={step.derivation} />
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">
                      {step.description}
                    </p>
                    {/* Extra disclaimer on AI steps */}
                    {isAI && (
                      <p className="mt-2 text-[10px] text-text-muted italic border-t border-border/50 pt-2">
                        IBM Granite interpretation — qualitative only, not a
                        deterministic output.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* IBM Granite attribution footer */}
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
