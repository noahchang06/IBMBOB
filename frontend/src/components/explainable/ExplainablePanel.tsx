import React from 'react';
import { useAppStore } from '../../store/appStore';
import { DerivationBadge } from '../shared/DerivationBadge';

export function ExplainablePanel() {
  const { currentExplanation, explanationLoading } = useAppStore();

  if (explanationLoading) {
    return (
      <div className="p-6 space-y-6 animate-pulse">
        <div className="h-8 bg-surface-2 rounded w-1/3 mb-8"></div>
        {[1, 2, 3].map(i => (
          <div key={i} className="space-y-3">
            <div className="h-4 bg-surface-2 rounded w-1/4"></div>
            <div className="h-24 bg-surface-2 rounded-xl w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!currentExplanation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-text-muted p-8 text-center h-full">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mb-4 opacity-50"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <p>Select "Explain with AI" on a node or edge to trace its reasoning.</p>
      </div>
    );
  }

  const { chain, summary } = currentExplanation;

  return (
    <div className="p-6 space-y-8 pb-20">
      <div>
        <h2 className="text-2xl font-bold mb-2">Reasoning Trace</h2>
        <p className="text-sm text-text-secondary leading-relaxed bg-surface-1 p-4 rounded-xl border border-border">
          {summary}
        </p>
      </div>

      <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
        
        {/* Tier 1: Retrieved Knowledge */}
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-4 bg-surface-0">
            <div className="w-10 h-10 rounded-full bg-[rgba(232,168,124,0.15)] border border-[rgba(232,168,124,0.3)] flex items-center justify-center text-[#f0b88a]">
              1
            </div>
            <h3 className="text-lg font-semibold text-[#f0b88a]">Retrieved Knowledge</h3>
          </div>
          <div className="ml-14 space-y-3">
            {chain.retrieved_knowledge.map(step => (
              <div key={step.step_number} className="bg-surface-1 p-4 rounded-xl border border-border border-l-2 border-l-[#f0b88a]">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs text-text-muted font-mono">STEP {step.step_number}</span>
                  <DerivationBadge label={step.derivation} />
                </div>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tier 2: Deterministic Reasoning */}
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-4 bg-surface-0">
            <div className="w-10 h-10 rounded-full bg-[rgba(65,179,163,0.15)] border border-[rgba(65,179,163,0.3)] flex items-center justify-center text-[#5fd4c0]">
              2
            </div>
            <h3 className="text-lg font-semibold text-[#5fd4c0]">Deterministic Reasoning</h3>
          </div>
          <div className="ml-14 space-y-3">
            {chain.deterministic_reasoning.map(step => (
              <div key={step.step_number} className="bg-surface-1 p-4 rounded-xl border border-border border-l-2 border-l-[#5fd4c0]">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs text-text-muted font-mono">STEP {step.step_number}</span>
                  <DerivationBadge label={step.derivation} />
                </div>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tier 3: AI Interpretation */}
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-4 bg-surface-0">
            <div className="w-10 h-10 rounded-full bg-[rgba(195,141,158,0.15)] border border-[rgba(195,141,158,0.3)] flex items-center justify-center text-[#d9a4b5]">
              3
            </div>
            <h3 className="text-lg font-semibold text-[#d9a4b5]">AI Interpretation</h3>
          </div>
          <div className="ml-14 space-y-3">
            {chain.ai_interpretation.map(step => (
              <div key={step.step_number} className="bg-surface-1 p-4 rounded-xl border border-border border-l-2 border-l-[#d9a4b5]">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs text-text-muted font-mono">STEP {step.step_number}</span>
                  <DerivationBadge label={step.derivation} />
                </div>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
