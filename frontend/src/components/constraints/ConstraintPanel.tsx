import React, { useRef, useCallback, useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { CONSTRAINT_META } from '../../types';
import type { ConstraintKey } from '../../types';
import { DerivationBadge } from '../shared/DerivationBadge';
import { useApi } from '../../hooks/useApi';

export function ConstraintPanel() {
  const {
    constraints, setConstraint, graph, setGraph, setDesignSystem,
    setConstraintEffects, setConstraintsApplying, constraintsApplying, constraintEffects,
  } = useAppStore();
  const api = useApi();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  const applyToBackend = useCallback(async (current: typeof constraints) => {
    if (!graph) return;
    setConstraintsApplying(true);
    setApplyError(null);
    try {
      const result = await api.applyConstraints(graph, current);
      setGraph(result.graph);
      setConstraintEffects(result.effects);
      setDesignSystem(result.design_system);
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : 'Constraint propagation failed.');
    } finally {
      setConstraintsApplying(false);
    }
  }, [graph, api, setGraph, setConstraintEffects, setDesignSystem, setConstraintsApplying]);

  const handleSliderChange = (key: ConstraintKey, value: number) => {
    setConstraint(key, value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      applyToBackend({ ...constraints, [key]: value });
    }, 450);
  };

  const handlePreset = (preset: Partial<Record<ConstraintKey, number>>) => {
    const next = { ...constraints, ...preset };
    (Object.keys(preset) as ConstraintKey[]).forEach(k => setConstraint(k, next[k]));
    applyToBackend(next);
  };

  const modifiedCount = constraintEffects.length;

  // No-graph empty state
  if (!graph) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 gap-6 text-text-muted">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1" className="opacity-40" aria-hidden="true">
          <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
          <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
          <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/>
          <line x1="17" y1="16" x2="23" y2="16"/>
        </svg>
        <div className="space-y-2">
          <p className="text-sm">No reasoning graph loaded.</p>
          <p className="text-xs">Select a challenge from the Discovery view and build a graph to enable constraint tuning.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8 pb-20">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-2xl font-bold">Creative Constraints</h2>
          {constraintsApplying && (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <div className="w-3 h-3 border-2 border-surface-3 border-t-accent rounded-full animate-spin" />
              Recalculating…
            </div>
          )}
        </div>
        <p className="text-text-muted text-sm">
          Adjust constraints to influence the reasoning graph and design system generation.
        </p>
      </div>

      {/* Sliders */}
      <div className="space-y-5">
        {(Object.keys(CONSTRAINT_META) as ConstraintKey[]).map(key => {
          const meta = CONSTRAINT_META[key];
          const value = constraints[key];

          return (
            <div key={key} className="bg-surface-1 p-4 rounded-xl border border-border">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-accent text-sm">{meta.icon}</span>
                  <h3 className="font-medium text-sm">{meta.label}</h3>
                </div>
                <DerivationBadge label="SYSTEM" />
              </div>

              <p className="text-xs text-text-muted mb-4">{meta.description}</p>

              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0" max="1" step="0.05"
                  value={value}
                  onChange={e => handleSliderChange(key, parseFloat(e.target.value))}
                  aria-label={meta.label}
                  aria-valuemin={0}
                  aria-valuemax={1}
                  aria-valuenow={value}
                  aria-valuetext={`${(value * 100).toFixed(0)}%`}
                  className="flex-1 h-1.5 bg-surface-3 rounded-lg appearance-none cursor-pointer accent-accent"
                />
                <span className="text-xs font-mono w-8 text-right tabular-nums">
                  {value.toFixed(2)}
                </span>
              </div>

              {/* Micro bar showing value */}
              <div className="mt-2 h-0.5 bg-surface-3 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${value * 100}%`, backgroundColor: 'var(--color-accent)' }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary of effects */}
      {modifiedCount > 0 && !constraintsApplying && (
        <div className="bg-surface-1 border border-border rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted flex items-center gap-2">
              <span>Propagation Effects</span>
              <span className="px-1.5 py-0.5 rounded-full bg-accent/15 text-accent text-[10px] font-mono">
                {modifiedCount} edge{modifiedCount !== 1 ? 's' : ''} modified
              </span>
            </h3>
            <DerivationBadge label="SYSTEM" />
          </div>
          
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1 divide-y divide-border/40">
            {constraintEffects.slice(0, 8).map(effect => {
              const delta = effect.modified_weight - effect.original_weight;
              const isIncrease = delta > 0;
              const deltaFormatted = (isIncrease ? '+' : '') + delta.toFixed(2);

              return (
                <div key={effect.edge_id} className="pt-2 first:pt-0 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-text-secondary font-medium">
                      Edge #{effect.edge_id.replace('e-', '')}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-semibold uppercase ${
                      isIncrease ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                    }`}>
                      {isIncrease ? 'Amplified' : 'Attenuated'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 tabular-nums">
                    <span className="text-text-muted">
                      {effect.original_weight.toFixed(2)} → <strong className="text-text-primary">{effect.modified_weight.toFixed(2)}</strong>
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold flex items-center gap-0.5 ${
                      isIncrease ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                    }`}>
                      <span>{isIncrease ? '▲' : '▼'}</span>
                      <span>{deltaFormatted}</span>
                    </span>
                  </div>
                </div>
              );
            })}
            {modifiedCount > 8 && (
              <p className="pt-2 text-[10px] text-text-muted italic">
                +{modifiedCount - 8} additional edges modified in graph…
              </p>
            )}
          </div>
        </div>
      )}

      {/* Apply error */}
      {applyError && (
        <div
          role="alert"
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400"
        >
          <strong>Propagation failed:</strong> {applyError}
        </div>
      )}

      {/* Presets */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">
          Presets
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {([
            ['Balanced', { visual_tension: 0.5, information_density: 0.5, accessibility: 0.5, playfulness: 0.5, material_scarcity: 0.5 }],
            ['Clinical', { accessibility: 0.9, information_density: 0.8, playfulness: 0.1, visual_tension: 0.3, material_scarcity: 0.2 }],
            ['Exploratory', { playfulness: 0.9, visual_tension: 0.8, material_scarcity: 0.1, accessibility: 0.4, information_density: 0.4 }],
            ['Minimalist', { material_scarcity: 0.9, information_density: 0.2, visual_tension: 0.2, playfulness: 0.2, accessibility: 0.7 }],
          ] as const).map(([label, preset]) => (
            <button
              key={label}
              onClick={() => handlePreset(preset as Partial<Record<ConstraintKey, number>>)}
              className="py-2 bg-surface-2 hover:bg-surface-3 rounded text-sm transition-colors border border-border text-text-secondary hover:text-text-primary"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
