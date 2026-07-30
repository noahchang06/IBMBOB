import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';

export function TopBar() {
  const { selectedChallenge, activePanel, setView, reset, constraintsApplying } = useAppStore();

  const handleBack = () => {
    reset();
    setView('discovery');
  };

  if (!selectedChallenge) return null;

  // Stages configuration
  const stages = [
    { id: 'discover', label: '1. Discover', isActive: false, isDone: true },
    { id: 'reason', label: '2. Reason', isActive: activePanel === 'constraints' || activePanel === 'inspector', isDone: false },
    { id: 'design', label: '3. Design', isActive: activePanel === 'design-system', isDone: false },
    { id: 'understand', label: '4. Understand', isActive: activePanel === 'explainable', isDone: false },
    { id: 'export', label: '5. Export', isActive: activePanel === 'export', isDone: false },
  ];

  return (
    <div className="h-14 bg-surface-2 border-b border-border flex items-center px-4 justify-between z-10 shrink-0 gap-4">
      {/* Left: Challenge info & Back */}
      <div className="flex items-center gap-3 shrink-0">
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

        <div className="hidden sm:block">
          <h2 className="text-sm font-semibold text-text-primary leading-tight">{selectedChallenge.name}</h2>
          <div className="text-[11px] text-text-muted">{selectedChallenge.subtitle}</div>
        </div>

        {constraintsApplying && (
          <div className="flex items-center gap-2 text-xs text-text-muted ml-1">
            <div className="w-3 h-3 border-2 border-surface-3 border-t-accent rounded-full animate-spin" />
            <span className="hidden lg:inline text-[11px]">Recalculating…</span>
          </div>
        )}
      </div>

      {/* Center: Non-interactive 5-Stage Workflow Indicator */}
      <nav aria-label="Workflow progress" className="hidden lg:flex items-center gap-1.5 px-3 py-1 bg-surface-1/80 border border-border/80 rounded-full text-xs font-mono">
        {stages.map((stage, idx) => (
          <React.Fragment key={stage.id}>
            {idx > 0 && <span className="text-text-muted/40 font-light select-none">›</span>}
            <span
              className={`px-2 py-0.5 rounded-full transition-colors select-none ${
                stage.isActive
                  ? 'bg-accent/20 text-accent-bright font-semibold border border-accent/30'
                  : stage.isDone
                    ? 'text-text-secondary opacity-75'
                    : 'text-text-muted opacity-60'
              }`}
            >
              {stage.label}
            </span>
          </React.Fragment>
        ))}
      </nav>

      {/* Right: Domain Badges */}
      <div className="flex gap-1.5 flex-wrap justify-end shrink-0">
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
