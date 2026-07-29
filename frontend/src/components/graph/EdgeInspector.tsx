import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import { EDGE_TYPE_COLORS, EDGE_TYPE_LABELS, DOMAIN_COLORS } from '../../types';
import { useApi } from '../../hooks/useApi';

export function EdgeInspector() {
  const { selectedEdge, graph, setActivePanel, setExplanation, setExplanationLoading } = useAppStore();
  const api = useApi();

  if (!selectedEdge || !graph) return null;

  const sourceNode = graph.nodes.find(n => n.id === selectedEdge.source_id);
  const targetNode = graph.nodes.find(n => n.id === selectedEdge.target_id);

  if (!sourceNode || !targetNode) return null;

  const edgeColor = EDGE_TYPE_COLORS[selectedEdge.edge_type];

  const handleExplain = async () => {
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainEdge(selectedEdge.id, sourceNode, targetNode, selectedEdge);
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
        <div className="flex items-start justify-between mb-6">
          <span 
            className="px-2 py-1 rounded text-xs font-mono uppercase font-medium"
            style={{ backgroundColor: `${edgeColor}22`, color: edgeColor, border: `1px solid ${edgeColor}55` }}
          >
            {EDGE_TYPE_LABELS[selectedEdge.edge_type]}
          </span>
          <DerivationBadge label={selectedEdge.derivation} />
        </div>

        <div className="flex items-center gap-4 bg-surface-2 p-4 rounded-xl border border-border mb-6">
          <div className="flex-1 text-center">
            <div className="text-xs text-text-muted mb-1">SOURCE</div>
            <div className="font-medium" style={{ color: DOMAIN_COLORS[sourceNode.domain] }}>{sourceNode.label}</div>
          </div>
          <div className="text-text-muted">→</div>
          <div className="flex-1 text-center">
            <div className="text-xs text-text-muted mb-1">TARGET</div>
            <div className="font-medium" style={{ color: DOMAIN_COLORS[targetNode.domain] }}>{targetNode.label}</div>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-text-muted">Connection Weight</span>
            <span className="font-mono">{(selectedEdge.weight * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-surface-3 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500" 
              style={{ width: `${selectedEdge.weight * 100}%`, backgroundColor: edgeColor }}
            />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Relationship Description</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{selectedEdge.relationship_description}</p>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Transferable Insight</h3>
        <div className="border-l-2 pl-4 py-1 my-4 italic text-text-primary" style={{ borderColor: edgeColor }}>
          "{selectedEdge.transferable_insight}"
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Evidence</h3>
        <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
          {selectedEdge.evidence.map((ev, idx) => (
            <li key={idx}>{ev}</li>
          ))}
        </ul>
      </div>

      <div className="pt-4">
        <button
          onClick={handleExplain}
          className="w-full py-3 bg-surface-2 hover:bg-surface-3 border border-border text-text-primary font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          Explain Connection
        </button>
      </div>
    </div>
  );
}
