import React from 'react';
import { Flame, Zap, Activity, Minus } from 'lucide-react';

export default function ViralityBadge({ score, level, isViral, showOutOfHundred = false, velocity = null, comments = 0, shares = 0 }) {
  const norm = (level || 'Low').toLowerCase();
  const roundedScore = Math.round(score || 0);

  const evidence = [];
  if (Number(velocity) >= 50) evidence.push(`rapid engagement growth (${Math.round(Number(velocity))}/hr)`);
  if (Number(comments) >= 100) evidence.push(`high comment activity (${Number(comments).toLocaleString()})`);
  if (Number(shares) >= 50) evidence.push(`strong sharing activity (${Number(shares).toLocaleString()})`);
  if (evidence.length === 0) evidence.push('strong combined engagement');

  const tooltipText = isViral || norm === 'viral'
    ? `Virality: ${roundedScore}/100 • ${evidence.join(', ')}.`
    : `Virality score: ${roundedScore}/100 • ${level || 'Low'}.`;

  if (isViral || norm === 'viral') {
    return (
      <span
        title={tooltipText}
        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200/80 shadow-xs dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800/60 transition-all hover:border-purple-300 dark:hover:border-purple-700"
      >
        <Flame className="w-3.5 h-3.5 text-purple-600 fill-purple-500 shrink-0 dark:text-purple-400 dark:fill-purple-400" />
        <span>{roundedScore}{showOutOfHundred ? ' / 100' : ''}</span>
        <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400">
          Viral
        </span>
      </span>
    );
  }

  if (norm === 'high') {
    return (
      <span
        title={tooltipText}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200/80 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/50 transition-colors"
      >
        <Zap className="w-3 h-3 text-amber-600 fill-amber-500 shrink-0 dark:text-amber-400 dark:fill-amber-400" />
        <span>{roundedScore}</span>
        <span className="text-[10px] opacity-75">High</span>
      </span>
    );
  }

  if (norm === 'medium') {
    return (
      <span
        title={tooltipText}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-sky-50 text-sky-800 border border-sky-200/80 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800/50 transition-colors"
      >
        <Activity className="w-3 h-3 text-sky-600 shrink-0 dark:text-sky-400" />
        <span>{roundedScore}</span>
        <span className="text-[10px] opacity-75">Medium</span>
      </span>
    );
  }

  return (
    <span
      title={tooltipText}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 dark:bg-slate-800/60 dark:text-slate-400 dark:border-slate-700/60 transition-colors"
    >
      <Minus className="w-3 h-3 text-slate-400 shrink-0" />
      <span>{roundedScore}</span>
      <span className="text-[10px] opacity-75">Low</span>
    </span>
  );
}
