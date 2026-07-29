import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import { GlassCard } from '../shared/GlassCard';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import type { PresetChallenge } from '../../types';

export function DiscoveryView() {
  const {
    challenges, selectChallenge, setView, setGraph, setInspirations,
    setGraphLoading, setDesignSystem, graphLoading,
  } = useAppStore();
  const api = useApi();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSelectChallenge = async (challenge: PresetChallenge) => {
    selectChallenge(challenge);
    setView('workspace');
    setGraphLoading(true);
    setLoadingId(challenge.id);
    setError(null);

    try {
      const { graph, inspirations, design_system } = await api.buildGraph(challenge.id);
      setGraph(graph);
      setInspirations(inspirations);
      setDesignSystem(design_system);
    } catch {
      setError('Could not reach the backend. Make sure the server is running on port 8000.');
      setView('discovery');
      selectChallenge(null);
    } finally {
      setGraphLoading(false);
      setLoadingId(null);
    }
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-start p-8 overflow-y-auto bg-gradient-to-b from-surface-0 via-surface-1 to-surface-0">
      {/* Hero */}
      <div className="max-w-5xl w-full text-center mb-12 animate-fade-in flex flex-col items-center">
        <span className="px-3 py-1 rounded-full text-xs font-mono tracking-widest uppercase bg-accent/10 text-accent border border-accent/20 mb-6">
          IBM AI Builders Challenge · Creative Reasoning Partner
        </span>
        <h1 className="text-6xl font-extrabold mb-4 tracking-tight gradient-text drop-shadow-sm">
          Creative Reasoning Platform
        </h1>
        <p className="text-xl font-medium text-text-secondary tracking-wide">
          Discover <span className="text-accent">·</span> Reason{' '}
          <span className="text-accent">·</span> Design{' '}
          <span className="text-accent">·</span> Understand{' '}
          <span className="text-accent">·</span> Export
        </p>
        <p className="mt-4 text-sm text-text-muted max-w-2xl mx-auto leading-relaxed">
          Cross-domain inspiration graphs, deterministic constraint propagation, and
          explainable design system generation — powered by IBM Granite.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="w-full max-w-6xl mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400 text-center animate-fade-in">
          {error}
        </div>
      )}

      {/* Challenge cards */}
      {challenges.length === 0 ? (
        /* Loading skeleton while challenges fetch */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-surface-3 rounded w-2/3 mb-3" />
              <div className="h-4 bg-surface-3 rounded w-1/2 mb-6" />
              <div className="flex gap-2 mb-4">
                <div className="h-5 w-16 bg-surface-3 rounded" />
                <div className="h-5 w-20 bg-surface-3 rounded" />
              </div>
              <div className="h-12 bg-surface-3 rounded mb-4" />
              <div className="h-4 bg-surface-3 rounded w-1/3 mt-auto" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl">
          {challenges.map(challenge => {
            const isLoading = loadingId === challenge.id;
            return (
              <GlassCard
                key={challenge.id}
                className="p-6 cursor-pointer hover:border-border-bright hover:shadow-lg transition-all duration-300 flex flex-col group"
                onClick={() => !graphLoading && handleSelectChallenge(challenge)}
              >
                <h3 className="text-2xl font-semibold mb-2 group-hover:text-accent-bright transition-colors">
                  {challenge.name}
                </h3>
                <p className="text-text-secondary text-sm mb-4">{challenge.subtitle}</p>

                <div className="flex flex-wrap gap-2 mb-4">
                  {challenge.domains.map(d => (
                    <span
                      key={d}
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{
                        backgroundColor: `${DOMAIN_COLORS[d]}22`,
                        color: DOMAIN_COLORS[d],
                        border: `1px solid ${DOMAIN_COLORS[d]}55`,
                      }}
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
                  {isLoading ? (
                    <span className="flex items-center gap-2 text-accent">
                      <div className="w-3 h-3 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                      Loading…
                    </span>
                  ) : (
                    <span className="text-accent group-hover:underline">LAUNCH WORKSPACE →</span>
                  )}
                </div>
              </GlassCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
