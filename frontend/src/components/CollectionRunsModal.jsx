import React, { useState, useEffect } from 'react';
import { X, Play, RefreshCw, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { api } from '../services/api';

export default function CollectionRunsModal({ onClose, onCollectionComplete }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selectedSource, setSelectedSource] = useState('all');

  const fetchRuns = async () => {
    try {
      const data = await api.getCollectionRuns();
      setRuns(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleTrigger = async () => {
    setRunning(true);
    try {
      await api.triggerCollection({ source: selectedSource, brand_id: 1 });
      await fetchRuns();
      if (onCollectionComplete) onCollectionComplete();
    } catch (err) {
      alert(`Collection failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center bg-slate-900/50 dark:bg-slate-950/70 backdrop-blur-xs p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-850">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Data Collectors & Run Pipeline</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Trigger on-demand collection and review historical collection logs</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Trigger Bar */}
        <div className="p-4 bg-slate-100/70 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Source:</span>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 font-medium text-slate-800 dark:text-slate-200 flex-1 sm:flex-initial"
            >
              <option value="all">All Sources (Parallel Pipeline)</option>
              <option value="mock">Mock Feeds (Instant 50+)</option>
              <option value="reddit">Reddit (Permitted API / Mock)</option>
              <option value="rss">News & Press RSS</option>
              <option value="facebook">Facebook (Graph API / Mock)</option>
              <option value="web">Web & Blogs</option>
            </select>
          </div>

          <button
            type="button"
            onClick={handleTrigger}
            disabled={running}
            className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-2xs disabled:opacity-50 transition-colors cursor-pointer"
          >
            {running ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Trigger Collection Now</span>
              </>
            )}
          </button>
        </div>

        {/* Runs History Table */}
        <div className="p-4 max-h-[60vh] overflow-y-auto text-xs">
          {loading ? (
            <div className="text-center py-8 text-slate-400">Loading collection runs...</div>
          ) : runs.length === 0 ? (
            <div className="text-center py-8 text-slate-400">No collection runs logged yet.</div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold text-[10px] uppercase">
                  <th className="pb-2">Source</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Found</th>
                  <th className="pb-2">Added</th>
                  <th className="pb-2">Skipped</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="py-2.5 font-semibold text-slate-800 dark:text-slate-200 capitalize">{r.source}</td>
                    <td className="py-2.5">
                      {r.status === 'completed' && (
                        <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-medium">
                          <CheckCircle className="w-3 h-3" /> Completed
                        </span>
                      )}
                      {r.status === 'running' && (
                        <span className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400 font-medium animate-pulse">
                          <Clock className="w-3 h-3" /> Running
                        </span>
                      )}
                      {r.status === 'failed' && (
                        <span className="inline-flex items-center gap-1 text-rose-700 dark:text-rose-400 font-medium" title={r.error_message}>
                          <AlertCircle className="w-3 h-3" /> Failed
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 text-slate-600 dark:text-slate-400">{r.records_found}</td>
                    <td className="py-2.5 font-bold text-emerald-600 dark:text-emerald-400">+{r.records_added}</td>
                    <td className="py-2.5 text-slate-400">{r.records_skipped}</td>
                    <td className="py-2.5 text-slate-400 font-mono text-[11px]">
                      {new Date(r.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-100 shadow-2xs cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

