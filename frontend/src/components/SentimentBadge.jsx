import React from 'react';
import { TrendingUp, TrendingDown, Minus, Shuffle } from 'lucide-react';

export default function SentimentBadge({ sentiment, score, showScore = true }) {
  const norm = (sentiment || 'Neutral').toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800/60 dark:text-slate-300 dark:border-slate-700/60';
  let Icon = Minus;
  let iconColor = 'text-slate-500 dark:text-slate-400';

  if (norm === 'positive') {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200/80 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/50';
    Icon = TrendingUp;
    iconColor = 'text-emerald-600 dark:text-emerald-400';
  } else if (norm === 'negative') {
    styles = 'bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/50';
    Icon = TrendingDown;
    iconColor = 'text-rose-600 dark:text-rose-400';
  } else if (norm === 'mixed') {
    styles = 'bg-amber-50 text-amber-800 border-amber-200/80 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/50';
    Icon = Shuffle;
    iconColor = 'text-amber-600 dark:text-amber-400';
  }

  const formattedScore = score !== undefined && score !== null
    ? (score > 0 ? `+${score}` : `${score}`)
    : null;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles} transition-colors`}
      title={formattedScore ? `Sentiment: ${sentiment || 'Neutral'} (${formattedScore})` : `Sentiment: ${sentiment || 'Neutral'}`}
    >
      <Icon className={`w-3 h-3 ${iconColor} shrink-0`} aria-hidden="true" />
      <span>{sentiment || 'Neutral'}</span>
      {showScore && formattedScore && (
        <span className="opacity-60 text-[10px] font-mono tracking-tight ml-0.5">
          ({formattedScore})
        </span>
      )}
    </span>
  );
}

