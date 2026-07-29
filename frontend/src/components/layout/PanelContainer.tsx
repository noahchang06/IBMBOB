import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useAppStore } from '../../store/appStore';
import { InspirationInspector } from '../inspector/InspirationInspector';
import { EdgeInspector } from '../graph/EdgeInspector';
import { ConstraintPanel } from '../constraints/ConstraintPanel';
import { DesignSystemPanel } from '../design-system/DesignSystemPanel';
import { ExplainablePanel } from '../explainable/ExplainablePanel';
import { ExportPanel } from '../export/ExportPanel';

export function PanelContainer() {
  const { activePanel, selectedNode, selectedEdge } = useAppStore();

  const renderContent = () => {
    switch (activePanel) {
      case 'inspector':
        if (selectedEdge) return <EdgeInspector />;
        if (selectedNode) return <InspirationInspector />;
        return (
          <div className="flex-1 flex items-center justify-center text-text-muted p-8 text-center">
            Select a node or edge in the graph to view details.
          </div>
        );
      case 'constraints':
        return <ConstraintPanel />;
      case 'design-system':
        return <DesignSystemPanel />;
      case 'explainable':
        return <ExplainablePanel />;
      case 'export':
        return <ExportPanel />;
      default:
        return null;
    }
  };

  return (
    <div className="w-[400px] xl:w-[480px] h-full bg-surface-0 border-l border-border flex flex-col shrink-0 overflow-hidden relative z-20">
      <AnimatePresence mode="wait">
        <motion.div
          key={activePanel + (activePanel === 'inspector' ? (selectedNode?.id || selectedEdge?.id || 'none') : '')}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="w-full h-full overflow-y-auto"
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
