import React, { useRef, useCallback, useEffect } from 'react';
import { useAppStore } from '../../store/appStore';
import { CONSTRAINT_META, ConstraintKey } from '../../types';
import { DerivationBadge } from '../shared/DerivationBadge';
import { useApi } from '../../hooks/useApi';

export function ConstraintPanel() {
  const { 
    constraints, setConstraint, graph, setGraph, setDesignSystem, 
    setConstraintEffects, setConstraintsApplying 
  } = useAppStore();
  const api = useApi();
  const debounceTimerRef = useRef<number | null>(null);

  const applyToBackend = useCallback(async (currentConstraints: typeof constraints) => {
    if (!graph) return;
    setConstraintsApplying(true);
    try {
      const result = await api.applyConstraints(graph, currentConstraints);
      setGraph(result.graph);
      setConstraintEffects(result.effects);
      setDesignSystem(result.design_system);
    } catch (err) {
      console.error(err);
    } finally {
      setConstraintsApplying(false);
    }
  }, [graph, api, setGraph, setConstraintEffects, setDesignSystem, setConstraintsApplying]);

  const handleSliderChange = (key: ConstraintKey, value: number) => {
    setConstraint(key, value);
    
    if (debounceTimerRef.current) {
      window.clearTimeout(debounceTimerRef.current);
    }
    
    debounceTimerRef.current = window.setTimeout(() => {
      applyToBackend({ ...constraints, [key]: value });
    }, 500);
  };

  const handlePreset = (preset: Partial<Record<ConstraintKey, number>>) => {
    const newConstraints = { ...constraints, ...preset };
    Object.keys(preset).forEach(k => setConstraint(k as ConstraintKey, newConstraints[k as ConstraintKey]));
    applyToBackend(newConstraints);
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-2">Creative Constraints</h2>
        <p className="text-text-muted text-sm">
          Adjust physical and conceptual constraints to influence the reasoning graph and design system generation.
        </p>
      </div>

      <div className="space-y-6">
        {(Object.keys(CONSTRAINT_META) as ConstraintKey[]).map((key) => {
          const meta = CONSTRAINT_META[key];
          const value = constraints[key];
          
          return (
            <div key={key} className="bg-surface-1 p-4 rounded-xl border border-border">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-accent">{meta.icon}</span>
                  <h3 className="font-medium">{meta.label}</h3>
                </div>
                <DerivationBadge label="SYSTEM" />
              </div>
              
              <p className="text-xs text-text-muted mb-4">{meta.description}</p>
              
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={value}
                  onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                  className="flex-1 h-1.5 bg-surface-3 rounded-lg appearance-none cursor-pointer accent-accent"
                />
                <span className="text-xs font-mono w-8 text-right">
                  {value.toFixed(2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3 border-b border-border pb-2">Presets</h3>
        <div className="grid grid-cols-2 gap-2">
          <button 
            onClick={() => handlePreset({ visual_tension: 0.5, information_density: 0.5, accessibility: 0.5, playfulness: 0.5, material_scarcity: 0.5 })}
            className="py-2 bg-surface-2 hover:bg-surface-3 rounded text-sm transition-colors border border-border"
          >
            Balanced
          </button>
          <button 
            onClick={() => handlePreset({ accessibility: 0.9, information_density: 0.8, playfulness: 0.1, visual_tension: 0.3, material_scarcity: 0.2 })}
            className="py-2 bg-surface-2 hover:bg-surface-3 rounded text-sm transition-colors border border-border"
          >
            Clinical
          </button>
          <button 
            onClick={() => handlePreset({ playfulness: 0.9, visual_tension: 0.8, material_scarcity: 0.1, accessibility: 0.4, information_density: 0.4 })}
            className="py-2 bg-surface-2 hover:bg-surface-3 rounded text-sm transition-colors border border-border"
          >
            Exploratory
          </button>
          <button 
            onClick={() => handlePreset({ material_scarcity: 0.9, information_density: 0.2, visual_tension: 0.2, playfulness: 0.2, accessibility: 0.7 })}
            className="py-2 bg-surface-2 hover:bg-surface-3 rounded text-sm transition-colors border border-border"
          >
            Minimalist
          </button>
        </div>
      </div>
    </div>
  );
}
