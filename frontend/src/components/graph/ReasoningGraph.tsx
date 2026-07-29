import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useAppStore } from '../../store/appStore';
import { useGraphLayout } from '../../hooks/useGraphLayout';
import { EDGE_TYPE_COLORS, EDGE_TYPE_LABELS, DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import type { EdgeType } from '../../types';

export function ReasoningGraph() {
  const {
    graph, graphLoading, selectedNode, selectedEdge, hoveredNode,
    selectNode, selectEdge, setHoveredNode,
  } = useAppStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const [showLegend, setShowLegend] = useState(false);

  // Handle container resize
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

  const { dragStart, dragMove, dragEnd } = useGraphLayout(
    graph?.nodes || [],
    graph?.edges || [],
    dimensions.width,
    dimensions.height,
    setPositions,
  );

  // ── Pan / Zoom ─────────────────────────────────────────────────────────────
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

  // Background pan — attach to an explicit rect overlay so we don't fight
  // with node pointer events.
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

  // Unique edge types present in the current graph
  const activeEdgeTypes = graph
    ? [...new Set(graph.edges.map(e => e.edge_type))] as EdgeType[]
    : [];

  // ── Loading state ───────────────────────────────────────────────────────────
  if (graphLoading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center relative">
        <div className="w-16 h-16 border-4 border-surface-3 border-t-accent rounded-full animate-spin" />
        <p className="mt-4 text-text-muted animate-pulse">Synthesizing reasoning graph…</p>
      </div>
    );
  }

  if (!graph) return null;

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
        {/* Background pan rect — sits behind everything */}
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
          {/* ── Edges ─────────────────────────────────────────────────────── */}
          {graph.edges.map(edge => {
            const src = positions.get(edge.source_id);
            const tgt = positions.get(edge.target_id);
            if (!src || !tgt) return null;

            const isSelected = selectedEdge?.id === edge.id;
            const linkedToNode = selectedNode &&
              (edge.source_id === selectedNode.id || edge.target_id === selectedNode.id);
            const linkedToHovered = hoveredNode &&
              (edge.source_id === hoveredNode || edge.target_id === hoveredNode);
            const highlighted = isSelected || linkedToNode || linkedToHovered;

            const opacity = highlighted ? 0.9 : 0.25 + edge.weight * 0.4;
            const strokeWidth = isSelected
              ? (1 + edge.weight * 3) + 2
              : (1 + edge.weight * 3);
            const color = EDGE_TYPE_COLORS[edge.edge_type];

            return (
              <line
                key={edge.id}
                x1={src.x} y1={src.y}
                x2={tgt.x} y2={tgt.y}
                stroke={color}
                strokeWidth={strokeWidth}
                strokeOpacity={opacity}
                strokeDasharray={isSelected ? '6,4' : undefined}
                className={`transition-all duration-300 cursor-pointer ${isSelected ? 'animate-[edge-flow_1s_linear_infinite]' : ''}`}
                onClick={e => { e.stopPropagation(); selectEdge(edge); }}
              />
            );
          })}

          {/* ── Nodes ─────────────────────────────────────────────────────── */}
          {graph.nodes.map(node => {
            const pos = positions.get(node.id);
            if (!pos) return null;

            const isSelected = selectedNode?.id === node.id;
            const isHovered = hoveredNode === node.id;
            const radius = 12 + node.importance * 20;
            const color = DOMAIN_COLORS[node.domain];

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x},${pos.y})`}
                className="cursor-pointer node-glow"
                style={{ color }}
                onClick={e => { e.stopPropagation(); selectNode(node); }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onPointerDown={e => {
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
                {/* Outer glow ring */}
                <circle
                  r={radius}
                  fill={`${color}33`}
                  stroke={color}
                  strokeWidth={isSelected ? 3 : 1.5}
                  className={`transition-all duration-300 ${isSelected ? 'animate-[node-pulse_2s_ease-in-out_infinite]' : ''}`}
                />
                {/* Inner solid dot */}
                <circle
                  r={radius * 0.42}
                  fill={color}
                  className="pointer-events-none"
                />

                {/* Label below */}
                <text
                  y={radius + 16}
                  textAnchor="middle"
                  fill={isSelected || isHovered ? '#e8e9f0' : '#6a6f85'}
                  fontSize={10}
                  fontFamily="JetBrains Mono, monospace"
                  className="pointer-events-none transition-colors duration-200"
                  style={{ textShadow: '0 1px 4px rgba(0,0,0,0.9)' }}
                >
                  {node.label}
                </text>

                {/* Domain badge on hover/select */}
                {(isHovered || isSelected) && (
                  <text
                    y={-radius - 10}
                    textAnchor="middle"
                    fill={color}
                    fontSize={8}
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight="bold"
                    className="pointer-events-none uppercase"
                    style={{ textShadow: '0 1px 4px rgba(0,0,0,0.9)' }}
                  >
                    {DOMAIN_LABELS[node.domain]}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* ── Zoom Controls ──────────────────────────────────────────────────── */}
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

      {/* ── Edge Type Legend ───────────────────────────────────────────────── */}
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

      {/* ── Node + Edge counts ─────────────────────────────────────────────── */}
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
