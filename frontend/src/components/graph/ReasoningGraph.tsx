import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useAppStore } from '../../store/appStore';
import { useGraphLayout } from '../../hooks/useGraphLayout';
import { useApi } from '../../hooks/useApi';
import {
  EDGE_TYPE_COLORS,
  EDGE_TYPE_LABELS,
  DOMAIN_COLORS,
  DOMAIN_LABELS,
  RELATIONSHIP_PRESETS,
} from '../../types';
import type { EdgeType, GraphNode } from '../../types';

const EDGE_TYPE_OPTIONS = Object.keys(EDGE_TYPE_LABELS) as EdgeType[];

type RelationshipSuggestion = {
  edge_type: EdgeType;
  relationship_label: string;
  relationship_description: string;
  confidence?: number | null;
};

export function ReasoningGraph() {
  const {
    graph,
    graphLoading,
    selectedNode,
    selectedEdge,
    hoveredNode,
    selectNode,
    selectEdge,
    setHoveredNode,
    selectedChallenge,
    edgeLinkMode,
    edgeLinkSourceId,
    edgeLinkError,
    setEdgeLinkMode,
    setEdgeLinkSourceId,
    setEdgeLinkError,
    addEdge,
    highlightedPath,
  } = useAppStore();
  const api = useApi();

  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const [showLegend, setShowLegend] = useState(false);
  const [pendingTarget, setPendingTarget] = useState<GraphNode | null>(null);
  const [pendingEdgeType, setPendingEdgeType] = useState<EdgeType>('similarity');
  const [pendingLabel, setPendingLabel] = useState('Similar to');
  const [pendingDescription, setPendingDescription] = useState('');
  const [pendingCustom, setPendingCustom] = useState(false);
  const [pendingConfidence, setPendingConfidence] = useState<number | null>(null);
  const [creatingEdge, setCreatingEdge] = useState(false);
  const [suggestions, setSuggestions] = useState<RelationshipSuggestion[]>([]);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const [suggestError, setSuggestError] = useState<string | null>(null);
  const [selectedSuggestionIdx, setSelectedSuggestionIdx] = useState<number | null>(null);
  const [fromAiSuggestion, setFromAiSuggestion] = useState(false);
  const [suggestionEdited, setSuggestionEdited] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const resetSuggestionState = useCallback(() => {
    setSuggestions([]);
    setSuggestLoading(false);
    setSuggestError(null);
    setSelectedSuggestionIdx(null);
    setFromAiSuggestion(false);
    setSuggestionEdited(false);
    setPendingConfidence(null);
  }, []);

  const cancelEdgeLink = useCallback(() => {
    setEdgeLinkMode(false);
    setPendingTarget(null);
    setPendingEdgeType('similarity');
    setPendingLabel('Similar to');
    setPendingDescription('');
    setPendingCustom(false);
    setCreatingEdge(false);
    resetSuggestionState();
  }, [setEdgeLinkMode, resetSuggestionState]);

  useEffect(() => {
    if (!edgeLinkMode) {
      setPendingTarget(null);
      resetSuggestionState();
      return;
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        cancelEdgeLink();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [edgeLinkMode, cancelEdgeLink, resetSuggestionState]);

  const { dragStart, dragMove, dragEnd } = useGraphLayout(
    graph?.nodes || [],
    graph?.edges || [],
    dimensions.width,
    dimensions.height,
    setPositions,
  );

  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isPanning = useRef(false);
  const lastPanPos = useRef({ x: 0, y: 0 });

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform(prev => ({
      ...prev,
      k: Math.max(0.15, Math.min(prev.k * factor, 5)),
    }));
  }, []);

  const handleBgPointerDown = useCallback((e: React.PointerEvent<SVGRectElement>) => {
    isPanning.current = true;
    lastPanPos.current = { x: e.clientX, y: e.clientY };
    (e.target as Element).setPointerCapture(e.pointerId);
  }, []);

  const handleBgPointerMove = useCallback((e: React.PointerEvent<SVGRectElement>) => {
    if (!isPanning.current) return;
    const dx = e.clientX - lastPanPos.current.x;
    const dy = e.clientY - lastPanPos.current.y;
    setTransform(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
    lastPanPos.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleBgPointerUp = useCallback(() => {
    isPanning.current = false;
  }, []);

  const handleZoomIn = () =>
    setTransform(prev => ({ ...prev, k: Math.min(prev.k * 1.25, 5) }));

  const handleZoomOut = () =>
    setTransform(prev => ({ ...prev, k: Math.max(prev.k / 1.25, 0.15) }));

  const handleZoomFit = useCallback(() => {
    if (!graph || positions.size === 0) return;
    const xs = Array.from(positions.values()).map(p => p.x);
    const ys = Array.from(positions.values()).map(p => p.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const pad = 80;
    const scaleX = (dimensions.width - pad * 2) / (maxX - minX || 1);
    const scaleY = (dimensions.height - pad * 2) / (maxY - minY || 1);
    const k = Math.min(scaleX, scaleY, 1.5);
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    setTransform({
      k,
      x: dimensions.width / 2 - cx * k,
      y: dimensions.height / 2 - cy * k,
    });
  }, [graph, positions, dimensions]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    if (!edgeLinkMode) {
      selectNode(node);
      return;
    }

    setEdgeLinkError(null);

    if (!edgeLinkSourceId) {
      setEdgeLinkSourceId(node.id);
      selectNode(node);
      return;
    }

    if (node.id === edgeLinkSourceId) {
      setEdgeLinkError('Cannot create a self-loop: choose a different target node.');
      return;
    }

    setPendingTarget(node);
    resetSuggestionState();
  }, [
    edgeLinkMode,
    edgeLinkSourceId,
    selectNode,
    setEdgeLinkError,
    setEdgeLinkSourceId,
    resetSuggestionState,
  ]);

  const applySuggestion = (suggestion: RelationshipSuggestion, index: number) => {
    setSelectedSuggestionIdx(index);
    setPendingLabel(suggestion.relationship_label);
    setPendingEdgeType(suggestion.edge_type);
    setPendingDescription(suggestion.relationship_description);
    setPendingConfidence(
      typeof suggestion.confidence === 'number' ? suggestion.confidence : null,
    );
    setPendingCustom(true);
    setFromAiSuggestion(true);
    setSuggestionEdited(false);
  };

  const markEditedIfFromAi = () => {
    if (fromAiSuggestion) setSuggestionEdited(true);
  };

  const requestGraniteSuggestions = async () => {
    if (!selectedChallenge || !edgeLinkSourceId || !pendingTarget || !graph) return;
    const sourceNode = graph.nodes.find(n => n.id === edgeLinkSourceId);
    if (!sourceNode) return;

    setSuggestLoading(true);
    setSuggestError(null);
    setSelectedSuggestionIdx(null);
    try {
      const result = await api.suggestRelationships(selectedChallenge.id, {
        source_id: sourceNode.inspiration_id,
        target_id: pendingTarget.inspiration_id,
        graph,
      });
      const next = (result.suggestions || []).map(s => ({
        edge_type: s.edge_type as EdgeType,
        relationship_label: s.relationship_label,
        relationship_description: s.relationship_description,
        confidence: s.confidence ?? null,
      }));
      setSuggestions(next);
      if (next.length === 0) {
        setSuggestError('Granite returned no suggestions. Try again or fill the form manually.');
      }
    } catch (error) {
      setSuggestions([]);
      setSuggestError(
        error instanceof Error ? error.message : 'Could not get Granite suggestions.',
      );
    } finally {
      setSuggestLoading(false);
    }
  };

  const rejectSuggestion = (index: number) => {
    setSuggestions(prev => prev.filter((_, i) => i !== index));
    if (selectedSuggestionIdx === index) {
      setSelectedSuggestionIdx(null);
      setFromAiSuggestion(false);
      setSuggestionEdited(false);
      setPendingConfidence(null);
    } else if (selectedSuggestionIdx !== null && selectedSuggestionIdx > index) {
      setSelectedSuggestionIdx(selectedSuggestionIdx - 1);
    }
  };

  const confirmCreateEdge = async () => {
    if (!selectedChallenge || !edgeLinkSourceId || !pendingTarget || !graph) return;

    const sourceNode = graph.nodes.find(n => n.id === edgeLinkSourceId);
    if (!sourceNode) {
      setEdgeLinkError('Source node no longer exists.');
      cancelEdgeLink();
      return;
    }
    if (!graph.nodes.some(n => n.id === pendingTarget.id)) {
      setEdgeLinkError('Target node no longer exists.');
      cancelEdgeLink();
      return;
    }

    setCreatingEdge(true);
    setEdgeLinkError(null);
    try {
      const trimmedLabel = pendingLabel.trim();
      if (!trimmedLabel) {
        setEdgeLinkError('Relationship label is required.');
        setCreatingEdge(false);
        return;
      }
      const edge = await api.createEdge(selectedChallenge.id, {
        source_id: sourceNode.inspiration_id,
        target_id: pendingTarget.inspiration_id,
        edge_type: pendingEdgeType,
        relationship_label: trimmedLabel,
        relationship_description:
          pendingDescription.trim() ||
          `${trimmedLabel}: ${sourceNode.label} → ${pendingTarget.label}`,
        confidence: fromAiSuggestion ? pendingConfidence : null,
        derivation: fromAiSuggestion ? 'AI_ACCEPTED' : 'MANUAL',
        from_ai_suggestion: fromAiSuggestion,
        suggestion_edited: fromAiSuggestion && suggestionEdited,
      });
      addEdge({
        ...edge,
        source_id: edge.source_id.startsWith('n-') ? edge.source_id : `n-${edge.source_id}`,
        target_id: edge.target_id.startsWith('n-') ? edge.target_id : `n-${edge.target_id}`,
      });
      cancelEdgeLink();
    } catch (error) {
      setEdgeLinkError(error instanceof Error ? error.message : 'Failed to create edge');
      setPendingTarget(null);
    } finally {
      setCreatingEdge(false);
    }
  };

  const activeEdgeTypes = graph
    ? [...new Set(graph.edges.map(e => e.edge_type))] as EdgeType[]
    : [];

  const sourceLabel = graph?.nodes.find(n => n.id === edgeLinkSourceId)?.label;

  if (graphLoading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center relative">
        <div className="w-16 h-16 border-4 border-surface-3 border-t-accent rounded-full animate-spin" />
        <p className="mt-4 text-text-muted animate-pulse">Synthesizing reasoning graph…</p>
      </div>
    );
  }

  if (!graph) return null;

  const pathActive = Boolean(highlightedPath);
  const pathNodeIds = new Set(highlightedPath?.nodeIds ?? []);
  const pathEdgeIds = new Set(highlightedPath?.edgeIds ?? []);
  const pathEdgeKeys = new Set(highlightedPath?.edgeKeys ?? []);

  return (
    <div
      ref={containerRef}
      className="w-full h-full absolute inset-0 overflow-hidden"
      style={{
        backgroundImage: 'radial-gradient(#2a2d3e 1px, transparent 1px)',
        backgroundSize: '24px 24px',
        backgroundPosition: `${transform.x % 24}px ${transform.y % 24}px`,
      }}
      onWheel={handleWheel}
    >
      <svg ref={svgRef} width="100%" height="100%" className="absolute inset-0 touch-none">
        <rect
          x={0} y={0}
          width="100%" height="100%"
          fill="transparent"
          style={{ cursor: isPanning.current ? 'grabbing' : 'grab' }}
          onPointerDown={handleBgPointerDown}
          onPointerMove={handleBgPointerMove}
          onPointerUp={handleBgPointerUp}
          onPointerLeave={handleBgPointerUp}
        />

        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
          {graph.edges.map(edge => {
            const src = positions.get(edge.source_id);
            const tgt = positions.get(edge.target_id);
            if (!src || !tgt) return null;

            const isSelected = selectedEdge?.id === edge.id;
            const onPath = pathEdgeIds.has(edge.id)
              || pathEdgeKeys.has(`${edge.source_id}->${edge.target_id}`);
            const linkedToNode = selectedNode &&
              (edge.source_id === selectedNode.id || edge.target_id === selectedNode.id);
            const linkedToHovered = hoveredNode &&
              (edge.source_id === hoveredNode || edge.target_id === hoveredNode);
            const highlighted = isSelected || linkedToNode || linkedToHovered || onPath;

            let opacity = highlighted ? 0.98 : 0.35 + edge.weight * 0.45;
            if (pathActive && !onPath) opacity = Math.min(opacity, 0.12);
            if (pathActive && onPath) opacity = 1;

            const strokeWidth = onPath
              ? (1.5 + edge.weight * 3) + 3
              : isSelected
                ? (1.5 + edge.weight * 3) + 2
                : (1.5 + edge.weight * 3);
            const color = EDGE_TYPE_COLORS[edge.edge_type] || '#41B3A3';
            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;
            const label = edge.relationship_label || EDGE_TYPE_LABELS[edge.edge_type];
            const showLabel = highlighted || isSelected || onPath;

            return (
              <g key={edge.id} style={{ opacity: pathActive && !onPath ? 0.35 : 1 }}>
                <line
                  x1={src.x} y1={src.y}
                  x2={tgt.x} y2={tgt.y}
                  stroke={color}
                  strokeWidth={strokeWidth}
                  strokeOpacity={opacity}
                  strokeDasharray={isSelected || onPath ? '6,4' : undefined}
                  className={`transition-all duration-300 cursor-pointer ${isSelected || onPath ? 'animate-[edge-flow_1s_linear_infinite]' : ''}`}
                  onClick={e => {
                    e.stopPropagation();
                    if (!edgeLinkMode) selectEdge(edge);
                  }}
                />
                {/* Wider invisible hit target for accessibility */}
                <line
                  x1={src.x} y1={src.y}
                  x2={tgt.x} y2={tgt.y}
                  stroke="transparent"
                  strokeWidth={14}
                  className="cursor-pointer"
                  onClick={e => {
                    e.stopPropagation();
                    if (!edgeLinkMode) selectEdge(edge);
                  }}
                />
                {showLabel && label && (
                  <text
                    x={midX}
                    y={midY - 6}
                    textAnchor="middle"
                    fill={isSelected || onPath ? '#ffffff' : '#c3c8dc'}
                    fontSize={9}
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight="600"
                    className="pointer-events-none"
                    style={{ textShadow: '0 1px 4px rgba(0,0,0,0.95)' }}
                  >
                    {label}
                  </text>
                )}
              </g>
            );
          })}

          {graph.nodes.map(node => {
            const pos = positions.get(node.id);
            if (!pos) return null;

            const isSelected = selectedNode?.id === node.id;
            const isHovered = hoveredNode === node.id;
            const isLinkSource = edgeLinkMode && edgeLinkSourceId === node.id;
            const onPath = pathNodeIds.has(node.id);
            const radius = 12 + node.importance * 20;
            const color = DOMAIN_COLORS[node.domain];
            const dimmed = pathActive && !onPath;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x},${pos.y})`}
                className="cursor-pointer node-glow"
                style={{ color, opacity: dimmed ? 0.22 : 1 }}
                onClick={e => {
                  e.stopPropagation();
                  handleNodeClick(node);
                }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onPointerDown={e => {
                  if (edgeLinkMode) return;
                  e.stopPropagation();
                  (e.target as Element).setPointerCapture(e.pointerId);
                  dragStart(node.id);
                  const handleMove = (ev: PointerEvent) => {
                    const svg = svgRef.current;
                    if (!svg) return;
                    const pt = svg.createSVGPoint();
                    pt.x = ev.clientX;
                    pt.y = ev.clientY;
                    const ctm = svg.querySelector('g')?.getScreenCTM();
                    if (ctm) {
                      const svgP = pt.matrixTransform(ctm.inverse());
                      dragMove(node.id, svgP.x, svgP.y);
                    }
                  };
                  const handleUp = (ev: PointerEvent) => {
                    (e.target as Element).releasePointerCapture(ev.pointerId);
                    window.removeEventListener('pointermove', handleMove);
                    window.removeEventListener('pointerup', handleUp);
                    dragEnd(node.id);
                  };
                  window.addEventListener('pointermove', handleMove);
                  window.addEventListener('pointerup', handleUp);
                }}
              >
                <circle
                  r={radius}
                  fill={`${color}33`}
                  stroke={isLinkSource || onPath ? '#ffffff' : color}
                  strokeWidth={isLinkSource || isSelected || onPath ? 3 : 1.5}
                  className={`transition-all duration-300 ${isSelected || isLinkSource || onPath ? 'animate-[node-pulse_2s_ease-in-out_infinite]' : ''}`}
                />
                <circle
                  r={radius * 0.42}
                  fill={color}
                  className="pointer-events-none"
                />

                <text
                  y={radius + 16}
                  textAnchor="middle"
                  fill={isSelected || isHovered || isLinkSource || onPath ? '#ffffff' : '#c3c8dc'}
                  fontSize={11}
                  fontWeight={isSelected || isHovered || isLinkSource ? '600' : '500'}
                  fontFamily="JetBrains Mono, monospace"
                  className="pointer-events-none transition-colors duration-200"
                  style={{ textShadow: '0 1px 4px rgba(0,0,0,0.95), 0 0 8px rgba(0,0,0,0.9)' }}
                >
                  {node.label}
                </text>

                {(isHovered || isSelected || isLinkSource) && (
                  <text
                    y={-radius - 10}
                    textAnchor="middle"
                    fill={color}
                    fontSize={9}
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight="bold"
                    className="pointer-events-none uppercase tracking-wider"
                    style={{ textShadow: '0 1px 4px rgba(0,0,0,0.95), 0 0 8px rgba(0,0,0,0.9)' }}
                  >
                    {DOMAIN_LABELS[node.domain]}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {edgeLinkMode && (
        <div
          className="absolute top-12 left-1/2 -translate-x-1/2 z-20 max-w-md w-[calc(100%-2rem)] bg-surface-2 border border-border rounded-xl px-4 py-3 shadow-lg"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-accent mb-1">
                Connect nodes
              </div>
              <p className="text-sm text-text-primary">
                {!edgeLinkSourceId
                  ? 'Step 1 of 2 — Select the source node'
                  : pendingTarget
                    ? 'Confirm relationship type, then create the edge'
                    : `Step 2 of 2 — Select the target node (source: ${sourceLabel ?? 'selected'})`}
              </p>
              {edgeLinkError && (
                <p className="mt-2 text-xs text-red-400">{edgeLinkError}</p>
              )}
            </div>
            <button
              type="button"
              onClick={cancelEdgeLink}
              className="shrink-0 px-2 py-1 text-xs text-text-muted hover:text-text-primary border border-border rounded"
              title="Cancel (Esc)"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {pendingTarget && edgeLinkSourceId && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/40">
          <div
            className="bg-surface-1 border border-border rounded-xl p-5 w-full max-w-md shadow-xl max-h-[90vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-labelledby="edge-type-title"
          >
            <h3 id="edge-type-title" className="text-lg font-semibold text-text-primary mb-1">
              Create relationship
            </h3>
            <p className="text-xs text-text-muted mb-4">
              {sourceLabel} → {pendingTarget.label}
            </p>

            <label htmlFor="edge-preset" className="block text-sm text-text-secondary mb-1">
              Relationship
            </label>
            <select
              id="edge-preset"
              value={pendingCustom ? '__custom__' : pendingLabel}
              onChange={e => {
                markEditedIfFromAi();
                if (e.target.value === '__custom__') {
                  setPendingCustom(true);
                  return;
                }
                setPendingCustom(false);
                const preset = RELATIONSHIP_PRESETS.find(p => p.label === e.target.value);
                if (preset) {
                  setPendingLabel(preset.label);
                  setPendingEdgeType(preset.edge_type);
                }
              }}
              className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm mb-3"
            >
              {RELATIONSHIP_PRESETS.map(p => (
                <option key={p.label} value={p.label}>{p.label}</option>
              ))}
              <option value="__custom__">Custom…</option>
            </select>

            {pendingCustom && (
              <>
                <label htmlFor="edge-label" className="block text-sm text-text-secondary mb-1">
                  Custom label
                </label>
                <input
                  id="edge-label"
                  value={pendingLabel}
                  onChange={e => {
                    markEditedIfFromAi();
                    setPendingLabel(e.target.value);
                  }}
                  className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm mb-3"
                  placeholder="e.g. Anticipates"
                />
                <label htmlFor="edge-type" className="block text-sm text-text-secondary mb-1">
                  Internal type
                </label>
                <select
                  id="edge-type"
                  value={pendingEdgeType}
                  onChange={e => {
                    markEditedIfFromAi();
                    setPendingEdgeType(e.target.value as EdgeType);
                  }}
                  className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm mb-3"
                >
                  {EDGE_TYPE_OPTIONS.map(et => (
                    <option key={et} value={et}>{EDGE_TYPE_LABELS[et]}</option>
                  ))}
                </select>
              </>
            )}

            <label htmlFor="edge-desc" className="block text-sm text-text-secondary mb-1">
              Why they connect
            </label>
            <textarea
              id="edge-desc"
              value={pendingDescription}
              onChange={e => {
                markEditedIfFromAi();
                setPendingDescription(e.target.value);
              }}
              rows={3}
              className="w-full px-3 py-2 bg-surface-2 border border-border rounded-md text-sm mb-3"
              placeholder="Explain how this idea relates to that idea…"
            />

            <div className="mb-4">
              <button
                type="button"
                disabled={suggestLoading}
                onClick={requestGraniteSuggestions}
                className="w-full px-3 py-2 text-sm border border-accent/40 text-accent rounded-md hover:bg-accent/10 disabled:opacity-60"
              >
                {suggestLoading ? 'Asking Granite…' : suggestions.length ? 'Suggest again with Granite' : 'Suggest with Granite'}
              </button>
              {suggestError && (
                <p className="mt-2 text-xs text-red-400" role="alert">{suggestError}</p>
              )}
              {fromAiSuggestion && (
                <p className="mt-2 text-[10px] font-mono uppercase tracking-wider text-accent">
                  Using AI suggestion{suggestionEdited ? ' (edited)' : ''} — confirm to save
                </p>
              )}
            </div>

            {suggestions.length > 0 && (
              <div className="mb-4 space-y-2" role="list" aria-label="AI relationship suggestions">
                {suggestions.map((s, idx) => {
                  const selected = selectedSuggestionIdx === idx;
                  return (
                    <div
                      key={`${s.edge_type}-${s.relationship_label}-${idx}`}
                      role="listitem"
                      className={`rounded-lg border p-3 ${
                        selected ? 'border-accent bg-accent/10' : 'border-border bg-surface-2'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-accent">
                          AI suggestion
                        </span>
                        {typeof s.confidence === 'number' && (
                          <span className="text-[10px] font-mono text-text-muted">
                            conf {(s.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <div className="text-sm font-medium text-text-primary">{s.relationship_label}</div>
                      <div className="text-[10px] font-mono text-text-muted mb-1">{s.edge_type}</div>
                      <p className="text-xs text-text-secondary mb-2">{s.relationship_description}</p>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => applySuggestion(s, idx)}
                          className="px-2 py-1 text-xs rounded bg-accent text-white"
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            applySuggestion(s, idx);
                          }}
                          className="px-2 py-1 text-xs rounded border border-border text-text-secondary"
                        >
                          Edit in form
                        </button>
                        <button
                          type="button"
                          onClick={() => rejectSuggestion(idx)}
                          className="px-2 py-1 text-xs rounded border border-border text-text-muted"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setPendingTarget(null);
                  resetSuggestionState();
                }}
                className="px-3 py-2 text-sm text-text-secondary bg-surface-2 rounded-md"
              >
                Back
              </button>
              <button
                type="button"
                disabled={creatingEdge}
                onClick={confirmCreateEdge}
                className="px-3 py-2 text-sm text-white bg-accent rounded-md disabled:opacity-60"
              >
                {creatingEdge ? 'Creating…' : 'Create edge'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="absolute bottom-4 left-4 flex flex-col gap-1 z-10">
        <button
          onClick={handleZoomIn}
          className="w-8 h-8 rounded bg-surface-2 border border-border text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors flex items-center justify-center text-lg font-light"
          title="Zoom in"
        >+</button>
        <button
          onClick={handleZoomOut}
          className="w-8 h-8 rounded bg-surface-2 border border-border text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors flex items-center justify-center text-lg font-light"
          title="Zoom out"
        >−</button>
        <button
          onClick={handleZoomFit}
          className="w-8 h-8 rounded bg-surface-2 border border-border text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors flex items-center justify-center"
          title="Fit graph"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
          </svg>
        </button>
      </div>

      <div className="absolute bottom-4 right-4 z-10">
        <button
          onClick={() => setShowLegend(v => !v)}
          className="px-2 py-1 rounded bg-surface-2 border border-border text-text-muted hover:text-text-primary text-[10px] font-mono uppercase tracking-wider transition-colors"
        >
          {showLegend ? 'Hide' : 'Legend'}
        </button>
        {showLegend && (
          <div className="absolute bottom-8 right-0 bg-surface-2 border border-border rounded-xl p-3 min-w-[200px] space-y-2 shadow-lg">
            {activeEdgeTypes.map(et => (
              <div key={et} className="flex items-center gap-2">
                <div className="w-6 h-0.5 rounded-full" style={{ backgroundColor: EDGE_TYPE_COLORS[et] }} />
                <span className="text-[10px] text-text-secondary font-mono">{EDGE_TYPE_LABELS[et]}</span>
              </div>
            ))}
            <div className="border-t border-border pt-2 mt-2">
              {[...new Set(graph.nodes.map(n => n.domain))].map(domain => (
                <div key={domain} className="flex items-center gap-2 py-0.5">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: DOMAIN_COLORS[domain] }} />
                  <span className="text-[10px] text-text-muted">{DOMAIN_LABELS[domain]}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="absolute top-3 left-4 flex gap-3 z-10 pointer-events-none">
        <span className="text-[10px] font-mono text-text-muted bg-surface-2/80 px-2 py-1 rounded border border-border">
          {graph.nodes.length} NODES
        </span>
        <span className="text-[10px] font-mono text-text-muted bg-surface-2/80 px-2 py-1 rounded border border-border">
          {graph.edges.length} EDGES
        </span>
      </div>
    </div>
  );
}
