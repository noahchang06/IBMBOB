import React from 'react';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import { GlassCard } from '../shared/GlassCard';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import type { PresetChallenge } from '../../types';

export function DiscoveryView() {
  const { challenges, selectChallenge, setView, setGraph, setInspirations, setGraphLoading, setDesignSystem } = useAppStore();
  const api = useApi();

  const handleSelectChallenge = async (challenge: PresetChallenge) => {
    selectChallenge(challenge);
    setView('workspace');
    setGraphLoading(true);
    
    try {
      const { graph, inspirations, design_system } = await api.buildGraph(challenge.id);
      setGraph(graph);
      setInspirations(inspirations);
      setDesignSystem(design_system);
    } catch (err) {
      console.error(err);
      // Handle error visually here if necessary
    } finally {
      setGraphLoading(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-8 overflow-y-auto bg-gradient-to-b from-surface-0 via-surface-1 to-surface-0">
      <div className="max-w-5xl w-full text-center mb-12 animate-fade-in flex flex-col items-center">
        <span className="px-3 py-1 rounded-full text-xs font-mono tracking-widest uppercase bg-accent/10 text-accent border border-accent/20 mb-6 shadow-sm">
          IBM AI Builders Challenge • Creative AI Partner
        </span>
        <h1 className="text-6xl font-extrabold mb-4 tracking-tight gradient-text drop-shadow-sm">
          Creative Reasoning Platform
        </h1>
        <p className="text-xl font-medium text-text-secondary tracking-wide">
          Discover <span className="text-accent">•</span> Reason <span className="text-accent">•</span> Design <span className="text-accent">•</span> Understand <span className="text-accent">•</span> Export
        </p>
        <p className="mt-4 text-sm text-text-muted max-w-2xl mx-auto leading-relaxed">
          Cross-domain inspiration, deterministic constraint propagation, and explainable design system evolution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl">
        {challenges.map((challenge) => (
          <GlassCard 
            key={challenge.id}
            className="p-6 cursor-pointer hover:border-border-bright hover:shadow-lg transition-all duration-300 flex flex-col group"
            onClick={() => handleSelectChallenge(challenge)}
          >
            <h3 className="text-2xl font-semibold mb-2 group-hover:text-accent-bright transition-colors">{challenge.name}</h3>
            <p className="text-text-secondary text-sm mb-4">{challenge.subtitle}</p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {challenge.domains.map(d => (
                <span 
                  key={d} 
                  className="px-2 py-1 rounded text-xs font-medium"
                  style={{ backgroundColor: `${DOMAIN_COLORS[d]}22`, color: DOMAIN_COLORS[d], border: `1px solid ${DOMAIN_COLORS[d]}55` }}
                >
                  {DOMAIN_LABELS[d]}
                </span>
              ))}
            </div>
            
            <p className="text-text-muted text-sm flex-grow mb-4 line-clamp-3">
              {challenge.description}
            </p>

            <div className="flex justify-between items-center text-xs font-mono text-text-secondary border-t border-border pt-4 mt-auto">
              <span>{challenge.node_count} NODES</span>
              <span className="text-accent group-hover:underline">LAUNCH WORKSPACE →</span>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
