import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';

export function TopBar() {
  const { selectedChallenge, setView, reset, constraintsApplying } = useAppStore();

  const handleBack = () => {
    reset();
    setView('discovery');
  };

  if (!selectedChallenge) return null;

  return (
    <div className="h-14 bg-surface-2 border-b border-border flex items-center px-4 justify-between z-10 shrink-0">
      <div className="flex items-center gap-4">
        <button
          onClick={handleBack}
          className="p-1.5 rounded hover:bg-surface-3 text-text-secondary hover:text-text-primary transition-colors"
          title="Back to Discovery"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
        </button>

        <div>
          <h2 className="text-sm font-semibold text-text-primary">{selectedChallenge.name}</h2>
          <div className="text-xs text-text-muted">{selectedChallenge.subtitle}</div>
        </div>

        {constraintsApplying && (
          <div className="flex items-center gap-2 text-xs text-text-muted ml-2">
            <div className="w-3 h-3 border-2 border-surface-3 border-t-accent rounded-full animate-spin" />
            <span className="hidden sm:inline">Recalculating…</span>
          </div>
        )}
      </div>

      <div className="flex gap-1.5 flex-wrap justify-end">
        {selectedChallenge.domains.map(d => (
          <span
            key={d}
            className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-medium"
            style={{
              backgroundColor: `${DOMAIN_COLORS[d]}22`,
              color: DOMAIN_COLORS[d],
              border: `1px solid ${DOMAIN_COLORS[d]}55`,
            }}
          >
            {DOMAIN_LABELS[d]}
          </span>
        ))}
      </div>
    </div>
  );
}
