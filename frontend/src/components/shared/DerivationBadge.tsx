import React from 'react';
import type { DerivationLabel } from '../../types';

interface DerivationBadgeProps {
  label: DerivationLabel;
  className?: string;
}

const SYMBOLS: Record<DerivationLabel, string> = {
  CURATED: '◈',
  RETRIEVED: '⤓',
  SYSTEM: '⚙',
  AI: '✨',
  AI_ACCEPTED: '✓✨',
  MANUAL: '✎',
};

export function DerivationBadge({ label, className = '' }: DerivationBadgeProps) {
  const baseClasses = 'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium tracking-wide';
  const labelClass = `badge-${label.toLowerCase()}`;
  const symbol = SYMBOLS[label] || '•';

  return (
    <span className={`${baseClasses} ${labelClass} ${className}`}>
      <span aria-hidden="true" className="text-[10px] opacity-80">{symbol}</span>
      <span>[{label}]</span>
    </span>
  );
}
