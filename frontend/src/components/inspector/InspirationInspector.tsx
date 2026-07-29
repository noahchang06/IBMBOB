import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import { useApi } from '../../hooks/useApi';

export function InspirationInspector() {
  const { selectedNode, inspirations, graph, setActivePanel, setExplanation, setExplanationLoading } = useAppStore();
  const api = useApi();
  const [explainError, setExplainError] = useState<string | null>(null);

  if (!selectedNode) return null;

  const inspiration = inspirations[selectedNode.inspiration_id];
  if (!inspiration) return null;

  const domainColor = DOMAIN_COLORS[inspiration.domain];

  // Find nodes this one connects to (for related concepts section)
  const relatedNodes = graph
    ? graph.edges
        .filter(e => e.source_id === selectedNode.id || e.target_id === selectedNode.id)
        .map(e => {
          const otherId = e.source_id === selectedNode.id ? e.target_id : e.source_id;
          return graph.nodes.find(n => n.id === otherId);
        })
        .filter((n): n is NonNullable<typeof n> => !!n)
        // de-duplicate
        .filter((n, i, arr) => arr.findIndex(x => x.id === n.id) === i)
        .slice(0, 5)
    : [];

  const handleExplain = async () => {
    setExplainError(null);
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainNode(selectedNode.id, inspiration);
      setExplanation(result);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : 'Explanation request failed.');
    } finally {
      setExplanationLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-8 pb-20">
      {/* Identity header */}
      <div>
        <div className="flex items-start justify-between mb-3">
          <span
            className="px-2 py-1 rounded text-xs font-mono uppercase font-medium"
            style={{ backgroundColor: `${domainColor}22`, color: domainColor, border: `1px solid ${domainColor}55` }}
          >
            {DOMAIN_LABELS[inspiration.domain]}
          </span>
          <DerivationBadge label={inspiration.derivation} />
        </div>

        {/* h2 — corrected from text-3xl to text-xl for consistent panel hierarchy */}
        <h2 className="text-xl font-bold mb-3 leading-snug" style={{ color: domainColor }}>
          {inspiration.name}
        </h2>

        <p className="text-sm text-text-secondary leading-relaxed">
          {inspiration.description}
        </p>
      </div>

      {/* Historical Context */}
      <div>
        <h3 className="section-header">Historical Context</h3>
        <p className="text-sm text-text-secondary">{inspiration.historical_context}</p>
      </div>

      {/* Key Principles */}
      <div>
        <h3 className="section-header">Key Principles</h3>
        <div className="space-y-3">
          {inspiration.key_principles.map((p, idx) => (
            <div key={idx} className="bg-surface-2 p-3 rounded-lg border border-border">
              <div className="flex justify-between items-start mb-1.5">
                <h4 className="font-medium text-sm text-text-primary">{p.name}</h4>
                <DerivationBadge label={p.derivation} />
              </div>
              <p className="text-xs text-text-secondary">{p.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Transferable Lessons */}
      <div>
        <h3 className="section-header">Transferable Lessons</h3>
        <ul className="list-disc pl-5 space-y-1.5 text-sm text-text-secondary">
          {inspiration.transferable_lessons.map((lesson, idx) => (
            <li key={idx}>{lesson}</li>
          ))}
        </ul>
      </div>

      {/* Design Implications */}
      <div>
        <h3 className="section-header">Design Implications</h3>
        <ul className="list-disc pl-5 space-y-1.5 text-sm">
          {inspiration.design_implications.map((imp, idx) => (
            <li key={idx} className="text-accent-bright">{imp}</li>
          ))}
        </ul>
      </div>

      {/* Related Concepts — nodes connected via graph edges */}
      {relatedNodes.length > 0 && (
        <div>
          <h3 className="section-header">
            Related in Graph
            <span className="ml-1.5 text-accent font-mono normal-case tracking-normal">
              ({relatedNodes.length})
            </span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {relatedNodes.map(node => (
              <span
                key={node.id}
                className="px-2 py-1 rounded text-xs font-medium border"
                style={{
                  color: DOMAIN_COLORS[node.domain],
                  borderColor: `${DOMAIN_COLORS[node.domain]}44`,
                  background: `${DOMAIN_COLORS[node.domain]}12`,
                }}
              >
                {node.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Explain error */}
      {explainError && (
        <div
          role="alert"
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400"
        >
          <strong>Explanation failed:</strong> {explainError}
        </div>
      )}

      {/* CTA */}
      <div className="pt-2">
        <button
          onClick={handleExplain}
          className="w-full py-3 bg-accent hover:bg-accent-bright text-surface-0 font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Explain Reasoning with AI
        </button>
      </div>
    </div>
  );
}
