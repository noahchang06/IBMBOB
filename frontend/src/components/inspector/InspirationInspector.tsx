import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import { useApi } from '../../hooks/useApi';

export function InspirationInspector() {
  const { selectedNode, inspirations, setActivePanel, setExplanation, setExplanationLoading } = useAppStore();
  const api = useApi();

  if (!selectedNode) return null;

  const inspiration = inspirations[selectedNode.inspiration_id];
  if (!inspiration) return null;

  const domainColor = DOMAIN_COLORS[inspiration.domain];

  const handleExplain = async () => {
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainNode(selectedNode.id, inspiration);
      setExplanation(result);
    } catch (err) {
      console.error(err);
    } finally {
      setExplanationLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-8 pb-20">
      <div>
        <div className="flex items-start justify-between mb-4">
          <span 
            className="px-2 py-1 rounded text-xs font-mono uppercase font-medium"
            style={{ backgroundColor: `${domainColor}22`, color: domainColor, border: `1px solid ${domainColor}55` }}
          >
            {DOMAIN_LABELS[inspiration.domain]}
          </span>
          <DerivationBadge label={inspiration.derivation} />
        </div>
        
        <h2 className="text-3xl font-bold mb-4" style={{ color: domainColor }}>
          {inspiration.name}
        </h2>
        
        <p className="text-text-secondary leading-relaxed">
          {inspiration.description}
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Historical Context</h3>
        <p className="text-sm text-text-secondary">{inspiration.historical_context}</p>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Key Principles</h3>
        <div className="space-y-4">
          {inspiration.key_principles.map((p, idx) => (
            <div key={idx} className="bg-surface-2 p-3 rounded-lg border border-border">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-text-primary">{p.name}</h4>
                <DerivationBadge label={p.derivation} />
              </div>
              <p className="text-sm text-text-secondary">{p.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Transferable Lessons</h3>
        <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
          {inspiration.transferable_lessons.map((lesson, idx) => (
            <li key={idx}>{lesson}</li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Design Implications</h3>
        <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
          {inspiration.design_implications.map((imp, idx) => (
            <li key={idx} className="text-accent-bright">{imp}</li>
          ))}
        </ul>
      </div>

      <div className="pt-4">
        <button
          onClick={handleExplain}
          className="w-full py-3 bg-accent hover:bg-accent-bright text-surface-0 font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Explain Reasoning with AI
        </button>
      </div>
    </div>
  );
}
