import React from 'react';
import {
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
  Flame,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';

const clampPct = (value) => `${Math.min(100, Math.max(4, Number(value) || 0))}%`;

export default function KpiCards({ kpis, loading }) {
  if (loading) {
    return (
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6" aria-label="Loading brand metrics">
        {[...Array(6)].map((_, index) => (
          <div
            key={index}
            className="h-[114px] animate-shimmer rounded-2xl border border-slate-200/80 bg-white/80 dark:border-slate-800/80 dark:bg-slate-900/80"
          />
        ))}
      </div>
    );
  }

  const items = [
    {
      label: 'Total Mentions',
      value: (kpis?.total_mentions || 0).toLocaleString(),
      helper: 'Conversations in this window',
      icon: MessageCircle,
      tone: 'slate',
    },
    {
      label: 'Positive Sentiment',
      value: `${kpis?.positive_pct || 0}%`,
      helper: 'Favorable conversations',
      icon: ThumbsUp,
      tone: 'emerald',
      progress: clampPct(kpis?.positive_pct),
    },
    {
      label: 'Negative Sentiment',
      value: `${kpis?.negative_pct || 0}%`,
      helper: 'Needs attention',
      icon: ThumbsDown,
      tone: 'rose',
      progress: clampPct(kpis?.negative_pct),
    },
    {
      label: 'Viral Posts',
      value: `${kpis?.viral_posts_count || 0}`,
      helper: 'High-momentum conversations',
      icon: Flame,
      tone: 'violet',
    },
    {
      label: 'Trending Topic',
      value: kpis?.top_trending_topic || 'No trend yet',
      helper: 'Most discussed theme',
      icon: TrendingUp,
      tone: 'indigo',
      isText: true,
    },
    {
      label: 'Top Complaint',
      value: kpis?.top_complaint || 'No complaint yet',
      helper: 'Most common concern',
      icon: AlertTriangle,
      tone: 'amber',
      isText: true,
    },
  ];

  const tones = {
    slate: [
      'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
      'text-slate-950 dark:text-white',
      'bg-slate-500',
      'group-hover:border-slate-300 dark:group-hover:border-slate-600',
    ],
    emerald: [
      'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
      'text-emerald-700 dark:text-emerald-400',
      'bg-emerald-500',
      'group-hover:border-emerald-300 dark:group-hover:border-emerald-800',
    ],
    rose: [
      'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
      'text-rose-700 dark:text-rose-400',
      'bg-rose-500',
      'group-hover:border-rose-300 dark:group-hover:border-rose-800',
    ],
    violet: [
      'bg-violet-50 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300',
      'text-violet-700 dark:text-violet-400',
      'bg-violet-500',
      'group-hover:border-violet-300 dark:group-hover:border-violet-800',
    ],
    indigo: [
      'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300',
      'text-slate-950 dark:text-white',
      'bg-indigo-500',
      'group-hover:border-indigo-300 dark:group-hover:border-indigo-800',
    ],
    amber: [
      'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
      'text-slate-950 dark:text-white',
      'bg-amber-500',
      'group-hover:border-amber-300 dark:group-hover:border-amber-800',
    ],
  };

  return (
    <section className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6" aria-label="Brand health metrics">
      {items.map((item) => {
        const Icon = item.icon;
        const [iconTone, valueTone, barTone, hoverBorder] = tones[item.tone];
        return (
          <article
            key={item.label}
            data-testid="kpi-card"
            className={`group relative min-w-0 rounded-2xl border border-slate-200/80 bg-white/90 p-3.5 shadow-[0_8px_22px_rgba(15,23,42,0.04)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_14px_28px_rgba(15,23,42,0.08)] dark:border-slate-800/80 dark:bg-slate-900/85 dark:hover:shadow-black/20 ${hoverBorder}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
                {item.label}
              </span>
              <span className={`rounded-xl p-1.5 ${iconTone} transition-transform duration-200 group-hover:scale-105`} aria-hidden="true">
                <Icon className="h-3.5 w-3.5" />
              </span>
            </div>
            <div
              title={item.value}
              className={`mt-2.5 truncate font-bold tracking-[-0.03em] ${valueTone} ${
                item.isText ? 'text-xs sm:text-sm' : 'text-xl tabular-nums'
              }`}
            >
              {item.value}
            </div>
            <div className="mt-1.5 truncate text-[10px] text-slate-400 dark:text-slate-500">
              {item.helper}
            </div>
            {item.progress && (
              <div
                className="mt-2.5 h-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
                aria-hidden="true"
              >
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barTone}`}
                  style={{ width: item.progress }}
                />
              </div>
            )}
          </article>
        );
      })}
    </section>
  );
}
