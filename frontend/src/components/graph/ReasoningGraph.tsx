import React, { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useGraphLayout } from '../../hooks/useGraphLayout';
import { EDGE_TYPE_COLORS, DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';

export function ReasoningGraph() {
  const { 
    graph, graphLoading, selectedNode, selectedEdge, hoveredNode,
    selectNode, selectEdge, setHoveredNode 
  } = useAppStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());

  // Handle resize
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(entries => {
      for (let entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
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
    setPositions
  );

  // SVG Pan/Zoom state simple implementation
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isDraggingBg = useRef(false);
  const lastMousePos = useRef({ x: 0, y: 0 });

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform(prev => ({
      ...prev,
      k: Math.max(0.1, Math.min(prev.k * scaleFactor, 4))
    }));
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.target instanceof SVGSVGElement || (e.target as Element).tagName === 'g') {
      isDraggingBg.current = true;
      lastMousePos.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (isDraggingBg.current) {
      const dx = e.clientX - lastMousePos.current.x;
      const dy = e.clientY - lastMousePos.current.y;
      setTransform(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
      lastMousePos.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handlePointerUp = () => {
    isDraggingBg.current = false;
  };

  if (graphLoading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center relative">
        <div className="w-16 h-16 border-4 border-surface-3 border-t-accent rounded-full animate-spin"></div>
        <p className="mt-4 text-text-muted animate-pulse">Synthesizing reasoning graph...</p>
      </div>
    );
  }

  if (!graph) return null;

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full absolute inset-0 overflow-hidden"
      style={{ backgroundImage: 'radial-gradient(#2a2d3e 1px, transparent 1px)', backgroundSize: '24px 24px', backgroundPosition: `${transform.x}px ${transform.y}px` }}
      onWheel={handleWheel}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <svg width="100%" height="100%" className="absolute inset-0 touch-none">
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {/* Edges */}
          {graph.edges.map(edge => {
            const sourcePos = positions.get(edge.source_id);
            const targetPos = positions.get(edge.target_id);
            if (!sourcePos || !targetPos) return null;

            const isSelected = selectedEdge?.id === edge.id;
            const isConnectedToSelected = selectedNode && (edge.source_id === selectedNode.id || edge.target_id === selectedNode.id);
            const isConnectedToHovered = hoveredNode && (edge.source_id === hoveredNode || edge.target_id === hoveredNode);
            
            const opacity = isSelected || isConnectedToSelected || isConnectedToHovered ? 0.9 : 0.3 + edge.weight * 0.4;
            const strokeWidth = isSelected ? (1 + edge.weight * 3) + 2 : (1 + edge.weight * 3);
            const color = EDGE_TYPE_COLORS[edge.edge_type];

            return (
              <line
                key={edge.id}
                x1={sourcePos.x}
                y1={sourcePos.y}
                x2={targetPos.x}
                y2={targetPos.y}
                stroke={color}
                strokeWidth={strokeWidth}
                strokeOpacity={opacity}
                strokeDasharray={isSelected ? '5,5' : 'none'}
                className={`transition-all duration-300 cursor-pointer ${isSelected ? 'animate-[edge-flow_1s_linear_infinite]' : ''}`}
                onClick={(e) => { e.stopPropagation(); selectEdge(edge); }}
              />
            );
          })}

          {/* Nodes */}
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
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer node-glow"
                style={{ color }}
                onClick={(e) => { e.stopPropagation(); selectNode(node); }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onPointerDown={(e) => {
                  e.stopPropagation();
                  (e.target as Element).setPointerCapture(e.pointerId);
                  dragStart(node.id);
                  const handleMove = (ev: PointerEvent) => {
                    const svg = containerRef.current?.querySelector('svg');
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
                  fill={`${color}44`}
                  stroke={color}
                  strokeWidth={isSelected ? 3 : 1.5}
                  className={`transition-all duration-300 ${isSelected ? 'animate-[node-pulse_2s_ease-in-out_infinite]' : ''}`}
                />
                <circle
                  r={radius * 0.4}
                  fill={color}
                  className="pointer-events-none"
                />
                
                {/* Label */}
                <text
                  y={radius + 16}
                  textAnchor="middle"
                  fill={isSelected || isHovered ? '#fff' : '#9095a8'}
                  className="text-[10px] font-mono pointer-events-none transition-colors duration-200"
                  style={{ textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
                >
                  {node.label}
                </text>
                
                {/* Domain badge on hover/select */}
                {(isHovered || isSelected) && (
                  <text
                    y={-radius - 12}
                    textAnchor="middle"
                    fill={color}
                    className="text-[8px] font-mono uppercase font-bold pointer-events-none"
                    style={{ textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
                  >
                    {DOMAIN_LABELS[node.domain]}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
      
      {/* Legend / Tooltips could be absolutely positioned here */}
    </div>
  );
}
