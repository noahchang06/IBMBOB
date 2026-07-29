import React from 'react';
import type { DerivationLabel } from '../../types';

interface DerivationBadgeProps {
  label: DerivationLabel;
  className?: string;
}

export function DerivationBadge({ label, className = '' }: DerivationBadgeProps) {
  const baseClasses = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium tracking-wide';
  const labelClass = `badge-${label.toLowerCase()}`;
  
  return (
    <span className={`${baseClasses} ${labelClass} ${className}`}>
      [{label}]
    </span>
  );
}
