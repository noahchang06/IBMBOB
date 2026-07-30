import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';
import { useApi } from '../../hooks/useApi';

export function DesignSystemPanel() {
  const { designSystem, graph, constraints, setExplanation, setExplanationLoading, setActivePanel } = useAppStore();
  const api = useApi();

  const [explainError, setExplainError] = useState<string | null>(null);

  const handleExplainTokens = async () => {
    if (!designSystem) return;
    setExplainError(null);
    setActivePanel('explainable');
    setExplanationLoading(true);
    try {
      const result = await api.explainDesignDecision('design_tokens', {
        design_system: designSystem,
        constraints,
      });
      setExplanation(result);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : 'Explanation request failed.');
    } finally {
      setExplanationLoading(false);
    }
  };

  if (!designSystem) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-8 text-center h-full">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1" className="mb-4 opacity-50">
          <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
        </svg>
        <p>Build a graph and apply constraints to generate a design system.</p>
      </div>
    );
  }

  const { typography, palette, spacing, components } = designSystem;

  return (
    <div className="p-6 space-y-10 pb-20">
      {/* Header & Compliance Summary */}
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold mb-1">Design System</h2>
            <p className="text-xs text-text-muted">
              Generated deterministically from reasoning graph constraints.
            </p>
          </div>
          <DerivationBadge label={designSystem.derivation} />
        </div>

        {/* Accessibility & Compliance Banner */}
        <div className="bg-surface-1 border border-border rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-text-muted">WCAG Status:</span>
            <span className={`px-2 py-0.5 rounded font-semibold ${
              designSystem.wcag_level === 'AAA'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : designSystem.wcag_level === 'AA'
                  ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
            }`}>
              Level {designSystem.wcag_level} Compliant
            </span>
          </div>

          <div className="flex items-center gap-2 text-text-secondary">
            <span className="text-text-muted">Motion Curve:</span>
            <span className="bg-surface-2 px-2 py-0.5 rounded border border-border">
              {designSystem.motion_duration_ms}ms ease-out
            </span>
          </div>
        </div>
      </div>

      {/* Typography */}
      <section>
        <div className="flex items-center justify-between mb-3 border-b border-border pb-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Typography Tokens
          </h3>
          <DerivationBadge label="SYSTEM" />
        </div>
        <div className="bg-surface-1 p-4 rounded-xl border border-border space-y-4">
          <div className="flex justify-between text-[11px] text-text-muted font-mono bg-surface-2/60 p-2 rounded border border-border/50">
            <span>Base Size: <strong className="text-text-primary">{typography.base_size}px</strong></span>
            <span>Scale Ratio: <strong className="text-text-primary">×{typography.scale_ratio}</strong></span>
            <span>Leading: <strong className="text-text-primary">{typography.line_height}</strong></span>
          </div>

          {([
            ['H1', 3],
            ['H2', 2],
            ['H3', 1],
          ] as const).map(([label, exp]) => (
            <div key={label}>
              <div className="text-[10px] text-text-muted font-mono mb-1">{label}</div>
              <div
                style={{
                  fontFamily: typography.heading_family,
                  fontWeight: typography.heading_weight,
                  fontSize: `${typography.base_size * Math.pow(typography.scale_ratio, exp)}px`,
                  lineHeight: typography.line_height,
                }}
              >
                The quick brown fox
              </div>
            </div>
          ))}

          <div>
            <div className="text-[10px] text-text-muted font-mono mb-1">BODY</div>
            <div
              style={{
                fontFamily: typography.body_family,
                fontWeight: typography.body_weight,
                fontSize: `${typography.base_size}px`,
                lineHeight: typography.line_height,
              }}
              className="text-text-secondary"
            >
              Design is not just what it looks like and feels like. Design is how it works.
            </div>
          </div>

          <div className="text-[10px] text-text-muted font-mono">
            {typography.heading_family}
          </div>
        </div>
      </section>

      {/* Palette */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">
          Colour Palette
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {palette.colors.map(color => (
            <div key={color.name} className="rounded-lg overflow-hidden border border-border bg-surface-1">
              <div className="h-14 w-full" style={{ backgroundColor: color.hex }} />
              <div className="p-2">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-medium">{color.name}</span>
                  {color.contrast_ratio && (
                    <span className="text-[9px] font-mono text-text-muted">{color.contrast_ratio}:1</span>
                  )}
                </div>
                <div className="flex justify-between items-center mt-0.5">
                  <span className="text-[10px] font-mono text-text-muted uppercase">{color.role}</span>
                  <span className="text-[10px] font-mono text-text-muted">{color.hex}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        {/* Contrast preview */}
        <div
          className="mt-3 p-4 rounded-xl border border-border"
          style={{ backgroundColor: palette.background, color: palette.foreground }}
        >
          <div className="text-sm font-medium mb-0.5">Contrast Preview</div>
          <div className="text-xs opacity-75">Ensuring readability across the full system.</div>
        </div>
      </section>

      {/* Spacing Scale */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">
          Spacing Scale <span className="normal-case text-text-muted">(base {spacing.base}px)</span>
        </h3>
        <div className="bg-surface-1 p-4 rounded-xl border border-border">
          <div className="flex items-end gap-1.5 flex-wrap">
            {spacing.scale.map((multiplier, idx) => {
              const px = spacing.base * multiplier;
              const maxPx = spacing.base * Math.max(...spacing.scale);
              const barHeight = Math.max(4, Math.round((px / maxPx) * 48));
              return (
                <div key={idx} className="flex flex-col items-center gap-1">
                  <span className="text-[8px] font-mono text-text-muted">{px}px</span>
                  <div
                    className="rounded-sm bg-accent/40 border border-accent/30"
                    style={{ width: 12, height: barHeight }}
                  />
                </div>
              );
            })}
          </div>
          <div className="mt-3 text-[10px] font-mono text-text-muted">
            Unit: {spacing.unit} · {spacing.scale.length} steps
          </div>
        </div>
      </section>

      {/* Components */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4 border-b border-border pb-2">
          Component Tokens
        </h3>
        <div className="space-y-4">
          {components.map(comp => (
            <div key={comp.name} className="bg-surface-1 p-4 rounded-xl border border-border">
              <div className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                {comp.name}
              </div>

              <div
                className="bg-surface-2 border border-border flex items-center justify-center text-xs text-text-muted"
                style={{
                  borderRadius: comp.border_radius,
                  padding: comp.padding,
                  boxShadow: comp.shadow,
                }}
              >
                Preview
              </div>

              <div className="mt-3 grid grid-cols-2 gap-1 text-[10px] font-mono text-text-muted">
                <div>radius: {comp.border_radius}</div>
                <div>padding: {comp.padding}</div>
                <div className="col-span-2 truncate">shadow: {comp.shadow}</div>
              </div>
              <p className="mt-2 text-[11px] text-text-secondary italic leading-snug">
                "{comp.notes}"
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Explain error */}
      {explainError && (
        <div
          role="alert"
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400"
        >
          <strong>Explanation failed:</strong> {explainError}
        </div>
      )}

      {/* Explain button */}
      {graph && (
        <div className="pt-2">
          <button
            onClick={handleExplainTokens}
            className="w-full py-3 bg-surface-2 hover:bg-surface-3 border border-border text-text-primary font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 4.6a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 .33 1.65 1.65 0 0 0 10.51 0V0a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            Explain Token Derivation
          </button>
        </div>
      )}
    </div>
  );
}
