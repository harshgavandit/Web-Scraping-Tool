import React, { useEffect, useState } from 'react';
import { ExternalLink, FileSearch, RefreshCw, X } from 'lucide-react';

import { api } from '../services/api';
import { safeExternalUrl } from '../utils/safeUrl';

export default function AuditTrailModal({ isOpen, brandId = 1, onClose }) {
  const [data, setData] = useState({ source_runs: [], ai_analyses: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    setLoading(true);
    api.getAuditTrail(brandId)
      .then((result) => { if (active) setData(result || { source_runs: [], ai_analyses: [] }); })
      .catch((error) => console.error('Failed to load audit trail:', error))
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [isOpen, brandId]);

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-[2px]" role="dialog" aria-modal="true" aria-labelledby="audit-title">
      <div className="flex max-h-[86vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <span className="rounded-lg bg-indigo-50 p-2 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-300"><FileSearch className="h-4 w-4" /></span>
            <div><h2 id="audit-title" className="text-sm font-bold text-slate-900 dark:text-white">Source &amp; AI Audit Trail</h2><p className="text-[11px] text-slate-500 dark:text-slate-400">Trace discovery queries, source results, Gemini models and completion status</p></div>
          </div>
          <button type="button" onClick={onClose} aria-label="Close audit trail" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><X className="h-4 w-4" /></button>
        </header>
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? <div className="flex min-h-40 items-center justify-center text-xs text-slate-500"><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Loading audit records…</div> : (
            <div className="grid gap-5 lg:grid-cols-2">
              <section><h3 className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">Google source runs</h3><div className="space-y-2">{data.source_runs.length ? data.source_runs.map((run) => <div key={run.id} className="rounded-lg border border-slate-200 p-3 text-xs dark:border-slate-800"><div className="flex justify-between gap-3"><span className="font-semibold text-slate-900 dark:text-white">{run.query}</span><span className="capitalize text-emerald-600">{run.status}</span></div><p className="mt-1 text-[11px] text-slate-500">{run.provider} · {String(run.category || '').replaceAll('_', ' ')} · {run.results_found} found / {run.results_new} new</p></div>) : <Empty label="No source runs recorded yet." />}</div></section>
              <section><h3 className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">AI analyses</h3><div className="space-y-2">{data.ai_analyses.length ? data.ai_analyses.map((item) => { const url = safeExternalUrl(item.source_url); return <div key={item.id} className="rounded-lg border border-slate-200 p-3 text-xs dark:border-slate-800"><div className="flex justify-between gap-3"><span className="truncate font-semibold text-slate-900 dark:text-white">{item.title || `Post ${item.post_id}`}</span><span className="capitalize text-slate-500">{item.status}</span></div><div className="mt-1 flex items-center justify-between gap-2 text-[11px] text-slate-500"><span>{item.provider} · <span>{item.model}</span></span>{url && <a href={url} target="_blank" rel="noopener noreferrer" aria-label={`Open source for ${item.title || item.post_id}`} className="inline-flex items-center gap-1 text-indigo-600 hover:underline">Open source<ExternalLink className="h-3 w-3" /></a>}</div></div>; }) : <Empty label="No AI analyses recorded yet." />}</div></section>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Empty({ label }) {
  return <div className="rounded-lg border border-dashed border-slate-200 px-4 py-8 text-center text-xs text-slate-500 dark:border-slate-700">{label}</div>;
}
