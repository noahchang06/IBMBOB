import React, { useRef, useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { PanelContainer } from './PanelContainer';
import { ReasoningGraph } from '../graph/ReasoningGraph';
import { CreateInspirationForm } from '../graph/CreateInspirationForm';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import type { GraphNode } from '../../types';

export function AppShell() {
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  // Captured when the create modal opens (initiation node for auto-connect priority).
  const initiationNodeRef = useRef<GraphNode | null>(null);

  const {
    selectedChallenge,
    selectedNode,
    addInspiration,
    addNodeAndEdges,
    edgeLinkMode,
    setEdgeLinkMode,
  } = useAppStore();
  const api = useApi();
  const canEditGraph = Boolean(selectedChallenge?.id.startsWith('user-'));

  const openCreateModal = () => {
    // Capture initiation node at open time (may differ from selection at submit).
    initiationNodeRef.current = selectedNode;
    setCreateError(null);
    setCreateModalOpen(true);
  };

  const handleCreateInspiration = async (inspirationData: {
    name: string;
    domain: string;
    description: string;
  }) => {
    if (!selectedChallenge) return;
    setCreateError(null);

    // Peer priority + semantic context for the single automatic edge:
    // 1. currently selected → "Builds on"
    // 2. initiation node (captured at modal open) → "Inspired by"
    // 3. omit → backend falls back to most recent → "Related to"
    let connectTo: string | null = null;
    let connectContext: 'selected' | 'initiation' | null = null;
    if (selectedNode) {
      connectTo = selectedNode.inspiration_id;
      connectContext = 'selected';
    } else if (initiationNodeRef.current) {
      connectTo = initiationNodeRef.current.inspiration_id;
      connectContext = 'initiation';
    }

    try {
      const { inspiration, new_edges } = await api.addInspiration(selectedChallenge.id, {
        ...inspirationData,
        connect_to_inspiration_id: connectTo,
        connect_context: connectContext,
      });
      addInspiration(inspiration);

      const newNode: GraphNode = {
        id: `n-${inspiration.id}`,
        inspiration_id: inspiration.id,
        label: inspiration.name,
        domain: inspiration.domain,
        importance: 0.5,
        derivation: inspiration.derivation,
      };

      const transformedEdges = new_edges.map(edge => ({
        ...edge,
        source_id: edge.source_id.startsWith('n-') ? edge.source_id : `n-${edge.source_id}`,
        target_id: edge.target_id.startsWith('n-') ? edge.target_id : `n-${edge.target_id}`,
      }));

      addNodeAndEdges(newNode, transformedEdges);
      initiationNodeRef.current = null;
      setCreateModalOpen(false);
    } catch (error) {
      console.error('Failed to create inspiration', error);
      setCreateError(error instanceof Error ? error.message : 'Failed to create inspiration');
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-surface-0">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative border-r border-border bg-surface-1">
          <ReasoningGraph />
          {canEditGraph && (
            <div className="absolute bottom-6 right-6 flex flex-col items-end gap-3 z-20">
              <button
                type="button"
                onClick={() => setEdgeLinkMode(!edgeLinkMode)}
                className={`px-3 py-2 rounded-lg text-xs font-semibold border shadow-lg transition-all ${
                  edgeLinkMode
                    ? 'bg-accent text-white border-accent'
                    : 'bg-surface-2 text-text-secondary border-border hover:text-text-primary hover:bg-surface-3'
                }`}
                title="Connect two nodes with an edge"
                aria-pressed={edgeLinkMode}
              >
                {edgeLinkMode ? 'Connecting…' : 'Connect nodes'}
              </button>
              <button
                type="button"
                onClick={openCreateModal}
                className="w-14 h-14 bg-accent rounded-full text-white flex items-center justify-center shadow-lg hover:bg-accent-bright transition-all"
                title="Add New Inspiration"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
            </div>
          )}
        </div>
        <PanelContainer />
      </div>
      {isCreateModalOpen && (
        <CreateInspirationForm
          onClose={() => {
            initiationNodeRef.current = null;
            setCreateModalOpen(false);
          }}
          onCreate={handleCreateInspiration}
          error={createError}
        />
      )}
    </div>
  );
}
