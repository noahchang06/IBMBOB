import React, { useEffect, useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import {
  EDGE_TYPE_COLORS,
  EDGE_TYPE_LABELS,
  DOMAIN_COLORS,
  RELATIONSHIP_PRESETS,
} from '../../types';
import type { EdgeType } from '../../types';
import { useApi } from '../../hooks/useApi';

export function EdgeInspector() {
  const {
    selectedEdge,
    selectedChallenge,
    graph,
    inspirations,
    setActivePanel,
    setExplanation,
    setExplanationLoading,
    updateEdgeInStore,
    removeEdgeFromStore,
    selectEdge,
  } = useAppStore();
  const api = useApi();

  const [explainError, setExplainError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [label, setLabel] = useState('');
  const [edgeType, setEdgeType] = useState<EdgeType>('similarity');
  const [description, setDescription] = useState('');
  const [customLabel, setCustomLabel] = useState(false);

  const canEdit = Boolean(selectedChallenge?.id.startsWith('user-'));

  useEffect(() => {
    if (!selectedEdge) return;
    setLabel(selectedEdge.relationship_label || EDGE_TYPE_LABELS[selectedEdge.edge_type]);
    setEdgeType(selectedEdge.edge_type);
    setDescription(selectedEdge.relationship_description || '');
    setCustomLabel(
      !RELATIONSHIP_PRESETS.some(p => p.label === selectedEdge.relationship_label)
      && !Object.values(EDGE_TYPE_LABELS).includes(selectedEdge.relationship_label)
    );
    setSaveError(null);
    setExplainError(null);
  }, [selectedEdge]);

  if (!selectedEdge || !graph) return null;

  const sourceNode = graph.nodes.find(n => n.id === selectedEdge.source_id);
  const targetNode = graph.nodes.find(n => n.id === selectedEdge.target_id);
  if (!sourceNode || !targetNode) return null;

  const edgeColor = EDGE_TYPE_COLORS[selectedEdge.edge_type] || '#41B3A3';
  const dirty =
    label !== (selectedEdge.relationship_label || '') ||
    edgeType !== selectedEdge.edge_type ||
    description !== (selectedEdge.relationship_description || '');

  const handlePresetChange = (value: string) => {
    if (value === '__custom__') {
      setCustomLabel(true);
      return;
    }
    setCustomLabel(false);
    const preset = RELATIONSHIP_PRESETS.find(p => p.label === value);
    if (preset) {
      setLabel(preset.label);
      setEdgeType(preset.edge_type);
    }
  };

  const handleExplain = async () => {
    setExplainError(null);
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainEdge(
        selectedEdge.id,
        sourceNode,
        targetNode,
        selectedEdge,
        graph,
        Object.values(inspirations),
      );
      setExplanation(result);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : 'Explanation request failed.');
    } finally {
      setExplanationLoading(false);
    }
  };

  const handleComparePaths = async () => {
    setExplainError(null);
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainCompare(sourceNode, targetNode, graph);
      setExplanation(result);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : 'Path comparison failed.');
    } finally {
      setExplanationLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedChallenge || !canEdit) return;
    const trimmed = label.trim();
    if (!trimmed) {
      setSaveError('Relationship label is required.');
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await api.updateEdge(selectedChallenge.id, selectedEdge.id, {
        relationship_label: trimmed,
        edge_type: edgeType,
        relationship_description: description,
      });
      updateEdgeInStore({
        ...updated,
        source_id: updated.source_id.startsWith('n-') ? updated.source_id : `n-${updated.source_id}`,
        target_id: updated.target_id.startsWith('n-') ? updated.target_id : `n-${updated.target_id}`,
      });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save edge');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedChallenge || !canEdit) return;
    if (!window.confirm('Delete this relationship? This cannot be undone.')) return;
    setDeleting(true);
    setSaveError(null);
    try {
      await api.deleteEdge(selectedChallenge.id, selectedEdge.id);
      removeEdgeFromStore(selectedEdge.id);
      selectEdge(null);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to delete edge');
    } finally {
      setDeleting(false);
    }
  };

  const presetValue = customLabel
    ? '__custom__'
    : (RELATIONSHIP_PRESETS.find(p => p.label === label)?.label ?? '__custom__');

  return (
    <div className="p-6 space-y-6 pb-20">
      <div>
        <div className="flex items-start justify-between mb-4 gap-2">
          <span
            className="px-2.5 py-1 rounded text-xs font-mono font-semibold"
            style={{ backgroundColor: `${edgeColor}22`, color: edgeColor, border: `1px solid ${edgeColor}55` }}
          >
            {selectedEdge.relationship_label || EDGE_TYPE_LABELS[selectedEdge.edge_type]}
          </span>
          <DerivationBadge label={selectedEdge.derivation} />
        </div>

        <div className="flex items-center gap-4 bg-surface-2 p-4 rounded-xl border border-border mb-4">
          <div className="flex-1 text-center">
            <div className="text-[10px] font-mono text-text-muted uppercase mb-0.5">SOURCE</div>
            <div className="font-semibold text-sm" style={{ color: DOMAIN_COLORS[sourceNode.domain] }}>
              {sourceNode.label}
            </div>
          </div>
          <div className="text-text-muted font-bold text-xs text-center max-w-[90px] leading-tight">
            {selectedEdge.relationship_label || '→'}
          </div>
          <div className="flex-1 text-center">
            <div className="text-[10px] font-mono text-text-muted uppercase mb-0.5">TARGET</div>
            <div className="font-semibold text-sm" style={{ color: DOMAIN_COLORS[targetNode.domain] }}>
              {targetNode.label}
            </div>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1 font-mono">
            <span className="text-text-muted">Connection Strength</span>
            <span className="font-bold" style={{ color: edgeColor }}>
              {(selectedEdge.weight * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full h-2 bg-surface-3 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${selectedEdge.weight * 100}%`, backgroundColor: edgeColor }}
            />
          </div>
        </div>

        {typeof selectedEdge.confidence === 'number' && (
          <div className="mt-3 text-xs font-mono text-text-muted">
            Confidence: <span className="text-text-primary">{(selectedEdge.confidence * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>

      {canEdit ? (
        <div className="space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted border-b border-border pb-1">
            Edit Relationship
          </h3>

          <div>
            <label htmlFor="rel-preset" className="block text-xs text-text-secondary mb-1">
              Relationship
            </label>
            <select
              id="rel-preset"
              value={presetValue}
              onChange={e => handlePresetChange(e.target.value)}
              className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm"
            >
              {RELATIONSHIP_PRESETS.map(p => (
                <option key={p.label} value={p.label}>{p.label}</option>
              ))}
              <option value="__custom__">Custom…</option>
            </select>
          </div>

          {customLabel && (
            <div>
              <label htmlFor="rel-label" className="block text-xs text-text-secondary mb-1">
                Custom label
              </label>
              <input
                id="rel-label"
                value={label}
                onChange={e => setLabel(e.target.value)}
                className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm"
                placeholder="e.g. Anticipates"
              />
            </div>
          )}

          <div>
            <label htmlFor="rel-type" className="block text-xs text-text-secondary mb-1">
              Internal type
            </label>
            <select
              id="rel-type"
              value={edgeType}
              onChange={e => setEdgeType(e.target.value as EdgeType)}
              className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm"
            >
              {(Object.keys(EDGE_TYPE_LABELS) as EdgeType[]).map(et => (
                <option key={et} value={et}>{EDGE_TYPE_LABELS[et]}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="rel-desc" className="block text-xs text-text-secondary mb-1">
              Why these ideas connect
            </label>
            <textarea
              id="rel-desc"
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm"
              placeholder="Explain how this idea relates to that idea…"
            />
          </div>

          {saveError && (
            <div role="alert" className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400">
              {saveError}
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              disabled={!dirty || saving}
              onClick={handleSave}
              className="flex-1 py-2.5 bg-accent text-white font-semibold rounded-lg disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            <button
              type="button"
              disabled={deleting}
              onClick={handleDelete}
              className="px-3 py-2.5 border border-red-500/40 text-red-400 rounded-lg text-sm hover:bg-red-500/10"
            >
              {deleting ? '…' : 'Delete'}
            </button>
          </div>
        </div>
      ) : (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2 border-b border-border pb-1">
            Reasoning Evidence
          </h3>
          <p className="text-sm text-text-secondary leading-relaxed">
            {selectedEdge.relationship_description || 'No relationship description recorded.'}
          </p>
        </div>
      )}

      {selectedEdge.transferable_insight && (
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
              Transferable Insight
            </span>
            <DerivationBadge label={selectedEdge.derivation} />
          </div>
          <p className="text-sm font-medium text-text-primary leading-relaxed italic">
            "{selectedEdge.transferable_insight}"
          </p>
        </div>
      )}

      {selectedEdge.evidence?.length > 0 && (
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
      )}

      {explainError && (
        <div role="alert" className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400">
          <strong>Explanation failed:</strong> {explainError}
        </div>
      )}

      <div className="pt-2">
        <button
          onClick={handleExplain}
          className="w-full py-3 bg-surface-2 hover:bg-surface-3 border border-border text-text-primary font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          Explain Connection
        </button>
        <button
          type="button"
          onClick={handleComparePaths}
          className="w-full py-2.5 border border-border text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-lg text-sm transition-colors"
        >
          Compare paths
        </button>
      </div>
    </div>
  );
}
