import React from 'react';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  bright?: boolean;
}

export function GlassCard({ children, bright = false, className = '', ...props }: GlassCardProps) {
  const baseClass = bright ? 'glass-bright' : 'glass';
  return (
    <div className={`${baseClass} rounded-xl ${className}`} {...props}>
      {children}
    </div>
  );
}
