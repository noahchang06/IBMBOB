import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { PanelContainer } from './PanelContainer';
import { ReasoningGraph } from '../graph/ReasoningGraph';
import { CreateInspirationForm } from '../graph/CreateInspirationForm';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import { GraphNode } from '../../types';

export function AppShell() {
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const { selectedChallenge, addInspiration, addNodeAndEdges } = useAppStore();
  const api = useApi();

  const handleCreateInspiration = async (inspirationData: any) => {
    if (!selectedChallenge) return;

    try {
      const { inspiration, new_edges } = await api.addInspiration(selectedChallenge.id, inspirationData);
      addInspiration(inspiration);
      
      const newNode: GraphNode = {
        id: `n-${inspiration.id}`,
        inspiration_id: inspiration.id,
        label: inspiration.name,
        domain: inspiration.domain,
        importance: 0.5, // Default importance
        derivation: inspiration.derivation,
      };

      const transformedEdges = new_edges.map(edge => ({
          ...edge,
          source_id: `n-${edge.source_id}`,
          target_id: `n-${edge.target_id}`,
      }));
      
      addNodeAndEdges(newNode, transformedEdges);

      setCreateModalOpen(false);
    } catch (error) {
      console.error("Failed to create inspiration", error);
      // You might want to show an error to the user
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-surface-0">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative border-r border-border bg-surface-1">
          <ReasoningGraph />
          <button
            onClick={() => setCreateModalOpen(true)}
            className="absolute bottom-6 right-6 w-14 h-14 bg-accent rounded-full text-white flex items-center justify-center shadow-lg hover:bg-accent-bright transition-all"
            title="Add New Inspiration"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
        </div>
        <PanelContainer />
      </div>
      {isCreateModalOpen && (
        <CreateInspirationForm
          onClose={() => setCreateModalOpen(false)}
          onCreate={handleCreateInspiration}
        />
      )}
    </div>
  );
}
