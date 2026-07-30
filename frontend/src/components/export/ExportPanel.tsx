import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';
import { DerivationBadge } from '../shared/DerivationBadge';

export function ExportPanel() {
  const { selectedChallenge, graph, designSystem, constraints, inspirations } = useAppStore();
  const api = useApi();
  const [exporting, setExporting] = useState(false);
  const [exportedOnce, setExportedOnce] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async () => {
    if (!selectedChallenge || !graph) return;

    setExporting(true);
    setExportError(null);
    try {
      const inspirationIds = graph.nodes
        .map(n => n.inspiration_id)
        .filter(id => !!inspirations[id]);

      const result = await api.exportPackage(
        selectedChallenge.id,
        graph,
        constraints,
        inspirationIds,
      );

      // JSON tokens download
      const jsonStr = 'data:text/json;charset=utf-8,' +
        encodeURIComponent(JSON.stringify(result, null, 2));
      const jsonAnchor = document.createElement('a');
      jsonAnchor.setAttribute('href', jsonStr);
      jsonAnchor.setAttribute(
        'download',
        `${selectedChallenge.name.toLowerCase().replace(/\s+/g, '-')}-export.json`,
      );
      document.body.appendChild(jsonAnchor);
      jsonAnchor.click();
      jsonAnchor.remove();

      // Markdown reasoning summary download
      const mdStr = 'data:text/markdown;charset=utf-8,' +
        encodeURIComponent(result.reasoning_summary_markdown);
      const mdAnchor = document.createElement('a');
      mdAnchor.setAttribute('href', mdStr);
      mdAnchor.setAttribute(
        'download',
        `${selectedChallenge.name.toLowerCase().replace(/\s+/g, '-')}-summary.md`,
      );
      document.body.appendChild(mdAnchor);
      mdAnchor.click();
      mdAnchor.remove();

      setExportedOnce(true);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const isReady = selectedChallenge && graph && designSystem;

  return (
    <div className="p-6 space-y-8 h-full flex flex-col">
      <div>
        <h2 className="text-2xl font-bold mb-2">Export Package</h2>
        <p className="text-text-muted text-sm">
          Download the complete generated design system, underlying graph structure,
          and AI reasoning trace.
        </p>
      </div>

      <div className="flex-1 space-y-4">
        {/* Design Tokens */}
        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
            <div>
              <div className="font-medium text-sm">Design Tokens</div>
              <div className="text-xs text-text-muted">JSON format · Style-dictionary compatible</div>
            </div>
          </div>
          <DerivationBadge label="SYSTEM" />
        </div>

        {/* Graph Data */}
        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2">
              <circle cx="18" cy="5" r="3" />
              <circle cx="6" cy="12" r="3" />
              <circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <div>
              <div className="font-medium text-sm">Reasoning Graph Data</div>
              <div className="text-xs text-text-muted">
                {graph ? `${graph.nodes.length} nodes · ${graph.edges.length} edges` : 'Nodes & Edges'}
              </div>
            </div>
          </div>
          <DerivationBadge label="RETRIEVED" />
        </div>

        {/* Reasoning Summary */}
        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            <div>
              <div className="font-medium text-sm">Reasoning Summary</div>
              <div className="text-xs text-text-muted">Markdown · IBM Granite rationale trace</div>
            </div>
          </div>
          <DerivationBadge label="AI" />
        </div>

        {/* Inspirations */}
        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <div className="font-medium text-sm">Inspiration Knowledge Base</div>
              <div className="text-xs text-text-muted">
                {graph ? `${graph.nodes.length} curated nodes with evidence` : 'Curated domain facts'}
              </div>
            </div>
          </div>
          <DerivationBadge label="CURATED" />
        </div>
      </div>

      {exportError && (
        <div
          role="alert"
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-xs text-red-400"
        >
          <strong>Export failed:</strong> {exportError}
        </div>
      )}

      {exportedOnce && !exportError && (
        <div className="bg-green-400/10 border border-green-400/30 rounded-lg p-3 text-xs text-green-400 text-center">
          ✓ Package downloaded — JSON tokens + Markdown summary
        </div>
      )}

      <div className="mt-auto pt-4">
        <button
          onClick={handleExport}
          disabled={!isReady || exporting}
          className="w-full py-4 bg-accent hover:bg-accent-bright disabled:opacity-40 disabled:cursor-not-allowed text-surface-0 font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          {exporting ? (
            <>
              <div className="w-4 h-4 border-2 border-surface-0/30 border-t-surface-0 rounded-full animate-spin" />
              <span>Generating Package…</span>
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Download Full Package
            </>
          )}
        </button>
        {!isReady && (
          <p className="text-center text-xs text-text-muted mt-3">
            Build a graph and apply constraints before exporting.
          </p>
        )}
      </div>
    </div>
  );
}
