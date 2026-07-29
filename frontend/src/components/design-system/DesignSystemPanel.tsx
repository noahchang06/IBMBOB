import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';

export function DesignSystemPanel() {
  const { designSystem } = useAppStore();

  if (!designSystem) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-8 text-center h-full">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mb-4 opacity-50"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
        <p>Apply constraints to generate a design system.</p>
      </div>
    );
  }

  const { typography, palette, spacing, components } = designSystem;

  return (
    <div className="p-6 space-y-10 pb-20">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold mb-1">Design System</h2>
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <span>WCAG: {designSystem.wcag_level}</span>
            <span>•</span>
            <span>Motion: {designSystem.motion_duration_ms}ms {designSystem.motion_easing}</span>
          </div>
        </div>
        <DerivationBadge label={designSystem.derivation} />
      </div>

      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">Typography</h3>
        <div className="space-y-4 bg-surface-1 p-4 rounded-xl border border-border">
          <div className="flex justify-between text-xs text-text-muted font-mono mb-2">
            <span>Base: {typography.base_size}px</span>
            <span>Scale: {typography.scale_ratio}</span>
          </div>
          
          <div style={{ fontFamily: typography.heading_family, fontWeight: typography.heading_weight }}>
            <div className="text-xs text-text-muted mb-1 font-mono">Heading 1</div>
            <div style={{ fontSize: `${typography.base_size * Math.pow(typography.scale_ratio, 3)}px`, lineHeight: typography.line_height }}>
              The quick brown fox
            </div>
          </div>
          
          <div style={{ fontFamily: typography.heading_family, fontWeight: typography.heading_weight }}>
            <div className="text-xs text-text-muted mb-1 font-mono">Heading 2</div>
            <div style={{ fontSize: `${typography.base_size * Math.pow(typography.scale_ratio, 2)}px`, lineHeight: typography.line_height }}>
              Jumps over the lazy dog
            </div>
          </div>
          
          <div style={{ fontFamily: typography.body_family, fontWeight: typography.body_weight }}>
            <div className="text-xs text-text-muted mb-1 font-mono">Body</div>
            <div style={{ fontSize: `${typography.base_size}px`, lineHeight: typography.line_height }} className="text-text-secondary">
              Design is not just what it looks like and feels like. Design is how it works.
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">Palette</h3>
        <div className="grid grid-cols-2 gap-3">
          {palette.colors.map(color => (
            <div key={color.name} className="flex flex-col rounded-lg overflow-hidden border border-border bg-surface-1">
              <div className="h-16 w-full" style={{ backgroundColor: color.hex }} />
              <div className="p-2">
                <div className="text-xs font-medium truncate">{color.name}</div>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-[10px] font-mono text-text-muted uppercase">{color.role}</span>
                  <span className="text-[10px] font-mono text-text-muted">{color.hex}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 rounded-xl border border-border" style={{ backgroundColor: palette.background, color: palette.foreground }}>
          <div className="text-sm font-medium mb-1">Contrast Preview</div>
          <div className="text-xs opacity-80">Ensuring readability across the system.</div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">Components</h3>
        <div className="space-y-4">
          {components.map(comp => (
            <div key={comp.name} className="bg-surface-1 p-4 rounded-xl border border-border">
              <div className="text-xs font-medium mb-3">{comp.name} Structure</div>
              
              <div className="bg-surface-2 border border-border flex items-center justify-center p-6 rounded" style={{ borderRadius: comp.border_radius, padding: comp.padding, boxShadow: comp.shadow }}>
                Preview Area
              </div>
              
              <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] font-mono text-text-muted">
                <div>Radius: {comp.border_radius}</div>
                <div>Pad: {comp.padding}</div>
                <div className="col-span-2 truncate">Shadow: {comp.shadow}</div>
              </div>
              <p className="mt-2 text-xs text-text-secondary italic">"{comp.notes}"</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
