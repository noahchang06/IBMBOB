import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import { GlassCard } from '../shared/GlassCard';
import { DOMAIN_COLORS, DOMAIN_LABELS } from '../../types';
import type { PresetChallenge } from '../../types';
import { CreateChallengeForm } from './CreateChallengeForm';

export function DiscoveryView() {
  const {
    challenges, selectChallenge, setView, setGraph, setInspirations,
    setGraphLoading, setDesignSystem, graphLoading, setChallenges,
  } = useAppStore();
  const api = useApi();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);

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

  const handleCreateChallenge = async (challengeData: any) => {
    try {
      const newChallenge = await api.createChallenge(challengeData);
      setChallenges([...challenges, newChallenge]);
      setCreateModalOpen(false);
      await handleSelectChallenge(newChallenge);
    } catch (error) {
      setError('Failed to create challenge. Please try again.');
    }
  };

  const handleDeleteChallenge = async (challengeId: string) => {
    try {
      await api.deleteChallenge(challengeId);
      setChallenges(challenges.filter(c => c.id !== challengeId));
    } catch (error) {
      setError('Failed to delete challenge. Please try again.');
    }
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-start p-8 overflow-y-auto bg-gradient-to-b from-surface-0 via-surface-1 to-surface-0">
      {isCreateModalOpen && (
        <CreateChallengeForm 
          onClose={() => setCreateModalOpen(false)}
          onCreate={handleCreateChallenge}
        />
      )}
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
        <div className="mt-8">
          <button 
            className="px-6 py-3 rounded-lg bg-accent text-white font-semibold hover:bg-accent-bright transition-all"
            onClick={() => setCreateModalOpen(true)}
          >
            Create New Challenge
          </button>
        </div>
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
                className="p-6 cursor-pointer hover:border-accent/50 hover:shadow-xl transition-all duration-300 flex flex-col group relative overflow-hidden"
                onClick={() => !graphLoading && handleSelectChallenge(challenge)}
              >
                {challenge.id.startsWith('user-') && (
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChallenge(challenge.id);
                    }}
                    className="absolute top-2 right-2 p-1 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/40"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </button>
                )}
                {/* Top badge */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                    {challenge.id.startsWith('user-') ? 'User-Created Challenge' : 'Curated Challenge'}
                  </span>
                  <span className="text-xs font-mono text-text-muted flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {challenge.node_count} Nodes
                  </span>
                </div>

                <h3 className="text-2xl font-bold mb-1.5 group-hover:text-accent-bright transition-colors text-text-primary leading-tight">
                  {challenge.name}
                </h3>
                <p className="text-text-secondary text-xs font-medium mb-4 leading-snug">{challenge.subtitle}</p>

                {/* Inspiration Domains */}
                <div className="mb-4 space-y-1.5">
                  <div className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                    Inspiration Domains:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {challenge.domains.map(d => (
                      <span
                        key={d}
                        className="px-2 py-0.5 rounded text-[11px] font-mono font-medium flex items-center gap-1"
                        style={{
                          backgroundColor: `${DOMAIN_COLORS[d]}22`,
                          color: DOMAIN_COLORS[d],
                          border: `1px solid ${DOMAIN_COLORS[d]}55`,
                        }}
                      >
                        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: DOMAIN_COLORS[d] }} />
                        {DOMAIN_LABELS[d]}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="text-text-muted text-xs leading-relaxed flex-grow mb-6 line-clamp-3">
                  {challenge.description}
                </p>

                {/* Prominent CTA */}
                <div className="pt-3 border-t border-border/60 mt-auto">
                  {isLoading ? (
                    <div className="w-full py-2.5 bg-accent/10 border border-accent/30 rounded-lg flex items-center justify-center gap-2 text-xs font-semibold text-accent">
                      <div className="w-3.5 h-3.5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                      Building Reasoning Graph…
                    </div>
                  ) : (
                    <div className="w-full py-2.5 px-4 bg-surface-2 group-hover:bg-accent group-hover:text-surface-0 border border-border group-hover:border-accent rounded-lg flex items-center justify-between text-xs font-semibold transition-all duration-200">
                      <span>Launch Reasoning Workspace</span>
                      <span className="font-mono text-sm transition-transform group-hover:translate-x-1">→</span>
                    </div>
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
