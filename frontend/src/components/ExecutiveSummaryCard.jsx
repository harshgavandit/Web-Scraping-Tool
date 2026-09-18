import React from 'react';
import { Sparkles, RefreshCw, Lightbulb, Target, Heart, AlertTriangle } from 'lucide-react';

export default function ExecutiveSummaryCard({ summary, onRefresh, refreshing, loading = false }) {
  if (loading) {
    return <div className="h-full min-h-[210px] rounded-2xl border border-slate-200/80 bg-white/85 p-4 dark:border-slate-800 dark:bg-slate-900/85" aria-label="Loading brand pulse"><div className="h-5 w-36 rounded bg-slate-100 animate-pulse dark:bg-slate-800" /><div className="mt-5 grid gap-3 md:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="h-32 animate-shimmer rounded-xl bg-slate-100 dark:bg-slate-800" />)}</div></div>;
  }

  if (!summary) {
    return <div className="flex h-full min-h-[210px] items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white/85 p-6 text-center text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-900/85 dark:text-slate-400">Brand pulse will appear after conversations have been analyzed.</div>;
  }

  return (
    <section className="h-full rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85" aria-labelledby="brand-pulse-title">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2"><span className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300"><Sparkles className="h-3.5 w-3.5" /></span><h2 id="brand-pulse-title" className="text-sm font-semibold text-slate-900 dark:text-white">Brand Pulse</h2></div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">The signals that deserve your team’s attention now.</p>
        </div>
        <button type="button" onClick={onRefresh} disabled={refreshing} aria-label="Refresh AI brand pulse" className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 text-[11px] font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"><RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />Refresh</button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <PulseItem icon={Heart} label="Current mood">
          <p className="text-sm font-semibold leading-5 text-slate-900 dark:text-white">{summary.overall_sentiment}</p>
          <div className="mt-3 space-y-1.5 text-[11px]">
            <p className="flex items-start gap-1.5 text-emerald-700 dark:text-emerald-300"><Heart className="mt-0.5 h-3 w-3 shrink-0" /><span className="line-clamp-2">{summary.top_positive_topic || 'No clear positive theme yet'}</span></p>
            <p className="flex items-start gap-1.5 text-rose-700 dark:text-rose-300"><AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" /><span className="line-clamp-2">{summary.top_negative_topic || 'No clear complaint yet'}</span></p>
          </div>
        </PulseItem>
        <PulseItem icon={Lightbulb} label="What changed">
          <p className="line-clamp-4 text-xs leading-5 text-slate-700 dark:text-slate-200">
            {summary.key_insight || 'No material change has been identified.'}
          </p>
          {summary.top_risk_cluster && (
            <div className="mt-2 text-[11px] text-amber-700 dark:text-amber-300 font-medium">
              <span className="text-slate-400">Emerging risk:</span> {summary.top_risk_cluster}
            </div>
          )}
        </PulseItem>
        <div className="flex flex-col justify-between rounded-lg border border-emerald-200 bg-emerald-50/70 p-3.5 dark:border-emerald-800/50 dark:bg-emerald-950/30">
          <div>
            <div className="flex items-center justify-between gap-1.5 mb-1.5">
              <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.1em] text-emerald-800 dark:text-emerald-300">
                <Target className="h-3.5 w-3.5" />
                Action
              </div>
              <div className="flex items-center gap-1">
                {summary.recommendation_priority && (
                  <span className={`rounded px-1.5 py-0.2 text-[9px] font-bold ${
                    summary.recommendation_priority === 'P0'
                      ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200'
                      : summary.recommendation_priority === 'P1'
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200'
                      : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
                  }`}>
                    {summary.recommendation_priority}
                  </span>
                )}
              </div>
            </div>
            <p className="line-clamp-3 text-xs font-semibold leading-5 text-emerald-950 dark:text-emerald-100">
              {summary.recommended_action || 'Continue monitoring for a stronger signal.'}
            </p>
          </div>

          <div className="mt-2.5 pt-2 border-t border-emerald-100 dark:border-emerald-900/50 text-[10px] text-emerald-800/80 dark:text-emerald-300/80">
            <span className="font-medium text-emerald-900 dark:text-emerald-200">Owner:</span>{' '}
            {summary.recommendation_owner || 'Brand Strategy'}
          </div>
        </div>
      </div>

      {summary.evidence_quotes && summary.evidence_quotes.length > 0 && (
        <div className="mt-3 rounded-lg bg-slate-50 p-2.5 border border-slate-100 dark:bg-slate-950/40 dark:border-slate-800/60">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Original Consumer Evidence
          </div>
          <div className="space-y-1">
            {summary.evidence_quotes.slice(0, 2).map((quote, idx) => (
              <p key={idx} className="truncate text-[11px] italic text-slate-600 dark:text-slate-300">
                “{quote}”
              </p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function PulseItem({ icon: Icon, label, children }) {
  return <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-3.5 dark:border-slate-800 dark:bg-slate-950/30"><div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400"><Icon className="h-3.5 w-3.5" />{label}</div>{children}</div>;
}
