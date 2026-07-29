import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useApi } from '../../hooks/useApi';

export function ExportPanel() {
  const { selectedChallenge, graph, designSystem, constraints, inspirations } = useAppStore();
  const api = useApi();
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!selectedChallenge || !graph || !designSystem) return;
    
    setExporting(true);
    try {
      const selectedInspirations = graph.nodes.map(n => inspirations[n.inspiration_id]).filter(Boolean);
      
      const payload = {
        challenge_name: selectedChallenge.name,
        design_tokens: designSystem,
        graph,
        selected_inspirations: selectedInspirations,
        constraints
      };

      const result = await api.exportPackage(payload);
      
      // Create JSON download
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
      const downloadAnchorNode = document.createElement('a');
      downloadAnchorNode.setAttribute("href", dataStr);
      downloadAnchorNode.setAttribute("download", `${selectedChallenge.name.toLowerCase().replace(/\s+/g, '-')}-export.json`);
      document.body.appendChild(downloadAnchorNode);
      downloadAnchorNode.click();
      downloadAnchorNode.remove();

      // Create Markdown download
      const mdStr = "data:text/markdown;charset=utf-8," + encodeURIComponent(result.reasoning_summary_markdown);
      const mdNode = document.createElement('a');
      mdNode.setAttribute("href", mdStr);
      mdNode.setAttribute("download", `${selectedChallenge.name.toLowerCase().replace(/\s+/g, '-')}-summary.md`);
      document.body.appendChild(mdNode);
      mdNode.click();
      mdNode.remove();

    } catch (err) {
      console.error(err);
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
          Download the complete generated design system, underlying graph structure, and AI reasoning trace.
        </p>
      </div>

      <div className="flex-1 space-y-4">
        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
            <div>
              <div className="font-medium">Design Tokens</div>
              <div className="text-xs text-text-muted">JSON format • Ready for style-dictionary</div>
            </div>
          </div>
          {designSystem ? <span className="text-green-400 text-xs font-mono">READY</span> : <span className="text-text-muted text-xs font-mono">MISSING</span>}
        </div>

        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            <div>
              <div className="font-medium">Graph Data</div>
              <div className="text-xs text-text-muted">Nodes & Edges • Force-directed positions</div>
            </div>
          </div>
          {graph ? <span className="text-green-400 text-xs font-mono">READY</span> : <span className="text-text-muted text-xs font-mono">MISSING</span>}
        </div>

        <div className="bg-surface-1 p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="text-accent" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            <div>
              <div className="font-medium">Reasoning Summary</div>
              <div className="text-xs text-text-muted">Markdown • Trace of AI decisions</div>
            </div>
          </div>
          <span className="text-green-400 text-xs font-mono">AUTO-GEN</span>
        </div>
      </div>

      <div className="mt-auto pt-4">
        <button
          onClick={handleExport}
          disabled={!isReady || exporting}
          className="w-full py-4 bg-accent hover:bg-accent-bright disabled:opacity-50 disabled:hover:bg-accent text-surface-0 font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          {exporting ? (
            <span className="animate-pulse">Generating Package...</span>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download Full Package
            </>
          )}
        </button>
        {!isReady && (
          <p className="text-center text-xs text-text-muted mt-3">
            Apply constraints to generate the design system before exporting.
          </p>
        )}
      </div>
    </div>
  );
}
