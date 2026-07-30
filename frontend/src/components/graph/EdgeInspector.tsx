import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import { EDGE_TYPE_COLORS, EDGE_TYPE_LABELS, DOMAIN_COLORS } from '../../types';
import { useApi } from '../../hooks/useApi';

export function EdgeInspector() {
  const { selectedEdge, graph, setActivePanel, setExplanation, setExplanationLoading } = useAppStore();
  const api = useApi();
  const [explainError, setExplainError] = useState<string | null>(null);

  if (!selectedEdge || !graph) return null;

  const sourceNode = graph.nodes.find(n => n.id === selectedEdge.source_id);
  const targetNode = graph.nodes.find(n => n.id === selectedEdge.target_id);

  if (!sourceNode || !targetNode) return null;

  const edgeColor = EDGE_TYPE_COLORS[selectedEdge.edge_type];

  const handleExplain = async () => {
    setExplainError(null);
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainEdge(selectedEdge.id, sourceNode, targetNode, selectedEdge);
      setExplanation(result);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : 'Explanation request failed.');
    } finally {
      setExplanationLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 pb-20">
      <div>
        <div className="flex items-start justify-between mb-4">
          <span 
            className="px-2.5 py-1 rounded text-xs font-mono uppercase font-semibold"
            style={{ backgroundColor: `${edgeColor}22`, color: edgeColor, border: `1px solid ${edgeColor}55` }}
          >
            {EDGE_TYPE_LABELS[selectedEdge.edge_type]}
          </span>
          <DerivationBadge label={selectedEdge.derivation} />
        </div>

        {/* Source -> Target Nodes */}
        <div className="flex items-center gap-4 bg-surface-2 p-4 rounded-xl border border-border mb-4">
          <div className="flex-1 text-center">
            <div className="text-[10px] font-mono text-text-muted uppercase mb-0.5">SOURCE NODE</div>
            <div className="font-semibold text-sm" style={{ color: DOMAIN_COLORS[sourceNode.domain] }}>{sourceNode.label}</div>
          </div>
          <div className="text-text-muted font-bold">→</div>
          <div className="flex-1 text-center">
            <div className="text-[10px] font-mono text-text-muted uppercase mb-0.5">TARGET NODE</div>
            <div className="font-semibold text-sm" style={{ color: DOMAIN_COLORS[targetNode.domain] }}>{targetNode.label}</div>
          </div>
        </div>

        {/* Connection Weight */}
        <div>
          <div className="flex justify-between text-xs mb-1 font-mono">
            <span className="text-text-muted">Connection Strength</span>
            <span className="font-bold" style={{ color: edgeColor }}>{(selectedEdge.weight * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-surface-3 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500" 
              style={{ width: `${selectedEdge.weight * 100}%`, backgroundColor: edgeColor }}
            />
          </div>
        </div>
      </div>

      {/* Prominent Transferable Insight Banner */}
      <div 
        className="p-4 rounded-xl border relative overflow-hidden"
        style={{
          backgroundColor: `${edgeColor}10`,
          borderColor: `${edgeColor}44`,
          borderLeftWidth: '4px',
          borderLeftColor: edgeColor,
        }}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider font-bold" style={{ color: edgeColor }}>
            Cross-Domain Transferable Insight
          </span>
          <DerivationBadge label={selectedEdge.derivation} />
        </div>
        <p className="text-sm font-medium text-text-primary leading-relaxed italic">
          "{selectedEdge.transferable_insight}"
        </p>
      </div>

      {/* Relationship Description */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2 border-b border-border pb-1">
          Relationship Description
        </h3>
        <p className="text-sm text-text-secondary leading-relaxed">{selectedEdge.relationship_description}</p>
      </div>

      {/* Evidence */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2 border-b border-border pb-1">
          Evidence Base
        </h3>
        <ul className="list-disc pl-5 space-y-1.5 text-xs text-text-secondary leading-relaxed">
          {selectedEdge.evidence.map((ev, idx) => (
            <li key={idx}>{ev}</li>
          ))}
        </ul>
      </div>

      {explainError && (
        <div
          role="alert"
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400"
        >
          <strong>Explanation failed:</strong> {explainError}
        </div>
      )}

      <div className="pt-2">
        <button
          onClick={handleExplain}
          className="w-full py-3 bg-surface-2 hover:bg-surface-3 border border-border text-text-primary font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Explain Connection
        </button>
      </div>
    </div>
  );
}
