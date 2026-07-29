import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import type { GraphNode, GraphEdge } from '../types';

export function useGraphLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
  onPositionsUpdate: (positions: Map<string, { x: number; y: number }>) => void
) {
  const simulationRef = useRef<d3.Simulation<d3.SimulationNodeDatum, undefined> | null>(null);

  useEffect(() => {
    if (!nodes.length || width === 0 || height === 0) return;

    // Create d3 nodes from our graph nodes (cloning to avoid mutating original state directly outside of callback)
    const d3Nodes = nodes.map(n => ({ ...n, id: n.id, x: n.x ?? width / 2, y: n.y ?? height / 2 }));
    const d3Edges = edges.map(e => ({ ...e, source: e.source_id, target: e.target_id, weight: e.weight }));

    const simulation = d3.forceSimulation(d3Nodes as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(d3Edges).id((d: any) => d.id).distance(150).strength((d: any) => d.weight * 0.1))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius((d: any) => (12 + d.importance * 20) + 10));

    simulation.on('tick', () => {
      const positions = new Map<string, { x: number; y: number }>();
      d3Nodes.forEach(node => {
        positions.set(node.id, { x: node.x!, y: node.y! });
      });
      onPositionsUpdate(positions);
    });

    simulationRef.current = simulation;

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, width, height]);

  const dragStart = useCallback((id: string) => {
    if (simulationRef.current) {
      simulationRef.current.alphaTarget(0.3).restart();
      const node = simulationRef.current.nodes().find((n: any) => n.id === id) as any;
      if (node) {
        node.fx = node.x;
        node.fy = node.y;
      }
    }
  }, []);

  const dragMove = useCallback((id: string, x: number, y: number) => {
    if (simulationRef.current) {
      const node = simulationRef.current.nodes().find((n: any) => n.id === id) as any;
      if (node) {
        node.fx = x;
        node.fy = y;
      }
    }
  }, []);

  const dragEnd = useCallback((id: string) => {
    if (simulationRef.current) {
      simulationRef.current.alphaTarget(0);
      const node = simulationRef.current.nodes().find((n: any) => n.id === id) as any;
      if (node) {
        node.fx = null;
        node.fy = null;
      }
    }
  }, []);

  return { dragStart, dragMove, dragEnd };
}
