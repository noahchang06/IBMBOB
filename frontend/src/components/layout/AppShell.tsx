import React from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { PanelContainer } from './PanelContainer';
import { ReasoningGraph } from '../graph/ReasoningGraph';

export function AppShell() {
  return (
    <div className="w-full h-full flex flex-col bg-surface-0">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative border-r border-border bg-surface-1">
          <ReasoningGraph />
        </div>
        <PanelContainer />
      </div>
    </div>
  );
}
