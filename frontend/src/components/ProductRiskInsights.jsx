import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Download,
  FileText,
  PackageSearch,
  ShieldAlert,
  Swords,
  ThumbsUp,
} from 'lucide-react';

const riskTone = {
  Critical: 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-200',
  Elevated: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-200',
  Watch: 'bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-200',
  Monitor: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
};

function LoadingRows() {
  return (
    <div className="space-y-2" aria-label="Loading intelligence">
      {[0, 1, 2].map((row) => (
        <div key={row} className="h-14 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
      ))}
    </div>
  );
}

export default function ProductRiskInsights({
  brandId = 1,
  products = [],
  risks = [],
  praises = [],
  competitors = [],
  loading = false,
  onSelectProduct,
  onSelectCompetitor,
  onOpenAlerts,
  onRebuild,
}) {
  return (
    <section className="mb-4 space-y-4" aria-label="Product and reputation intelligence">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Product Intelligence Card */}
        <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85">
          <header className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-50 p-1.5 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-300">
                <PackageSearch className="h-4 w-4" aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Product Intelligence</h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Evidence from indexed public pages</p>
              </div>
            </div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">Attention</span>
          </header>

          {loading ? <LoadingRows /> : products.length ? (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {products.slice(0, 5).map((item) => (
                <button
                  type="button"
                  key={item.product}
                  aria-label={`Filter conversations for ${item.product}`}
                  onClick={() => onSelectProduct?.(item.product)}
                  className="group grid w-full grid-cols-[minmax(0,1fr)_auto] gap-3 py-2.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 cursor-pointer"
                >
                  <span className="min-w-0">
                    <span className="flex items-center gap-2">
                      <span className="truncate text-xs font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-300">{item.product}</span>
                      <span className="text-[10px] text-slate-400">{item.mention_count} mentions</span>
                    </span>
                    <span className="mt-1 grid grid-cols-2 gap-2 text-[11px]">
                      <span className="truncate text-emerald-700 dark:text-emerald-300">
                        <span className="text-slate-400">Praise:</span> {item.top_praise || 'Not enough evidence'}
                      </span>
                      <span className="truncate text-rose-700 dark:text-rose-300">
                        <span className="text-slate-400">Complaint:</span> {item.top_complaint || 'Not enough evidence'}
                      </span>
                    </span>
                  </span>
                  <span className="flex items-center gap-1 self-center text-xs font-semibold tabular-nums text-slate-700 dark:text-slate-200">
                    {Math.round(item.average_attention || 0)} / 100
                    <ArrowRight className="h-3.5 w-3.5 text-slate-400 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex min-h-28 flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-200 px-4 text-center text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
              <span>Product insights will appear after tracked products are found on public pages.</span>
              {onRebuild && (
                <button
                  type="button"
                  onClick={onRebuild}
                  className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 font-semibold text-indigo-700 transition-colors hover:bg-indigo-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-300"
                >
                  Analyze existing conversations
                </button>
              )}
            </div>
          )}
        </article>

        {/* Reputation Risks Card */}
        <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85">
          <header className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-amber-50 p-1.5 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
                <ShieldAlert className="h-4 w-4" aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Reputation Risks</h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Prioritized by volume, source diversity and growth</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {onOpenAlerts && (
                <button
                  type="button"
                  onClick={onOpenAlerts}
                  className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-[11px] font-semibold text-amber-800 hover:bg-amber-100 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-200 cursor-pointer"
                >
                  Manage Alerts
                </button>
              )}
              <a
                href={`/api/intelligence/export.csv?brand_id=${brandId}`}
                download={`brand_${brandId}_intelligence.csv`}
                className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                title="Download CSV export"
              >
                <Download className="h-3 w-3 text-slate-500" />
                Export CSV
              </a>
              <a
                href={`/api/intelligence/export.pdf?brand_id=${brandId}`}
                download={`brand_${brandId}_intelligence.pdf`}
                className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                title="Download PDF report"
              >
                <FileText className="h-3 w-3 text-slate-500" />
                Export PDF
              </a>
            </div>
          </header>

          {loading ? <LoadingRows /> : risks.length ? (
            <div className="space-y-2">
              {risks.slice(0, 5).map((risk) => (
                <div key={risk.id || `${risk.product}-${risk.aspect}`} className="rounded-lg border border-slate-100 px-3 py-2.5 dark:border-slate-800">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" aria-hidden="true" />
                        <h3 className="truncate text-xs font-semibold text-slate-900 dark:text-slate-100">{risk.title}</h3>
                      </div>
                      <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                        {risk.mention_count} negative mentions · <span>{risk.unique_sources} independent sources</span>
                        {risk.growth_pct > 0 ? ` · ${Math.round(risk.growth_pct)}% growth` : ''}
                      </p>
                    </div>
                    <span className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-semibold ${riskTone[risk.risk_level] || riskTone.Monitor}`}>
                      {risk.risk_level || 'Monitor'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex min-h-28 items-center justify-center rounded-lg border border-dashed border-slate-200 px-4 text-center text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
              No evidence-backed reputation risks were detected in this period.
            </div>
          )}
        </article>
      </div>

      {/* Competitor Intelligence & Praise Highlights (Phase 3 Enterprise Analytics) */}
      {(competitors.length > 0 || praises.length > 0) && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {/* Competitor Comparisons */}
          {competitors.length > 0 && (
            <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85">
              <header className="mb-3 flex items-center justify-between border-b border-slate-100 pb-2.5 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-violet-50 p-1.5 text-violet-600 dark:bg-violet-950/60 dark:text-violet-300">
                    <Swords className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Head-to-Head Competitor Intelligence</h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">Direct consumer comparisons across categories</p>
                  </div>
                </div>
              </header>

              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {competitors.slice(0, 4).map((c) => (
                  <button
                    key={c.competitor}
                    type="button"
                    onClick={() => onSelectCompetitor?.(c.competitor)}
                    className="flex w-full items-center justify-between py-2 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 rounded px-1 transition cursor-pointer"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{c.competitor}</span>
                        <span className="text-[10px] text-slate-400">{c.mention_count} comparisons</span>
                      </div>
                      <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400">
                        <span>Topics: {c.top_topics?.join(', ') || 'General'}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium">
                      <span className="text-emerald-600 dark:text-emerald-400">+{c.positive_count}</span>
                      <span className="text-rose-600 dark:text-rose-400">-{c.negative_count}</span>
                      <ArrowRight className="h-3 w-3 text-slate-400" />
                    </div>
                  </button>
                ))}
              </div>
            </article>
          )}

          {/* Praise Highlights */}
          {praises.length > 0 && (
            <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85">
              <header className="mb-3 flex items-center justify-between border-b border-slate-100 pb-2.5 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-emerald-50 p-1.5 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-300">
                    <ThumbsUp className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Praise Clusters</h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">Aspects driving organic brand love and recommendations</p>
                  </div>
                </div>
              </header>

              <div className="space-y-2">
                {praises.slice(0, 3).map((p, idx) => (
                  <div key={idx} className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800/60">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-900 dark:text-slate-100">
                        {p.product ? `${p.product} · ${p.aspect}` : p.aspect}
                      </span>
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
                        {p.mention_count} positive mentions
                      </span>
                    </div>
                    {p.top_quote && (
                      <p className="mt-1 text-[11px] italic text-slate-600 dark:text-slate-300 line-clamp-2">
                        “{p.top_quote}”
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </article>
          )}
        </div>
      )}
    </section>
  );
}
