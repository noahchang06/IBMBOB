import React, { useRef, useCallback } from 'react';
import { useAppStore } from '../../store/appStore';
import type { WorkspacePanel } from '../../types';

// Simple SVG icons
const Icons = {
  inspector: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  constraints: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>,
  'design-system': () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>,
  explainable: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  export: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
};

const PANELS: { id: WorkspacePanel; label: string }[] = [
  { id: 'inspector',     label: 'Inspector' },
  { id: 'constraints',   label: 'Constraints' },
  { id: 'design-system', label: 'Design System' },
  { id: 'explainable',   label: 'Explainable AI' },
  { id: 'export',        label: 'Export' },
];

export function Sidebar() {
  const { activePanel, setActivePanel } = useAppStore();
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Arrow-key navigation within the sidebar nav
  const handleKeyDown = useCallback((e: React.KeyboardEvent, currentIndex: number) => {
    let next: number | null = null;
    if (e.key === 'ArrowDown') next = (currentIndex + 1) % PANELS.length;
    if (e.key === 'ArrowUp')   next = (currentIndex - 1 + PANELS.length) % PANELS.length;
    if (next !== null) {
      e.preventDefault();
      buttonRefs.current[next]?.focus();
    }
  }, []);

  return (
    <nav
      aria-label="Workspace panels"
      className="w-[56px] h-full flex flex-col bg-surface-2 border-r border-border py-4 items-center gap-3 z-10 relative"
    >
      {PANELS.map(({ id, label }, idx) => {
        const Icon = Icons[id];
        const isActive = activePanel === id;

        return (
          <button
            key={id}
            ref={el => { buttonRefs.current[idx] = el; }}
            onClick={() => setActivePanel(id)}
            onKeyDown={e => handleKeyDown(e, idx)}
            aria-label={label}
            aria-current={isActive ? 'page' : undefined}
            tabIndex={0}
            className={`w-10 h-10 rounded-lg flex items-center justify-center relative group transition-colors ${
              isActive
                ? 'text-accent bg-surface-3'
                : 'text-text-muted hover:text-text-primary hover:bg-surface-3'
            }`}
          >
            {isActive && (
              <div
                aria-hidden="true"
                className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent rounded-r-md"
              />
            )}
            <Icon />
            {/* Tooltip — hidden from a11y tree, visual only */}
            <div
              aria-hidden="true"
              className="absolute left-12 px-2 py-1 bg-surface-4 text-text-primary text-xs rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 border border-border"
            >
              {label}
            </div>
          </button>
        );
      })}
    </nav>
  );
}
