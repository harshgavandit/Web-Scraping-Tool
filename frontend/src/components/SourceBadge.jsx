import React from 'react';
import { MessageSquare, Globe, Rss, Facebook, Twitter } from 'lucide-react';

export default function SourceBadge({ source }) {
  const s = (source || 'web').toLowerCase();

  if (s === 'reddit') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-orange-50 text-orange-700 border border-orange-200/80 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800/50">
        <MessageSquare className="w-3 h-3 text-orange-600 dark:text-orange-400 shrink-0" />
        Reddit
      </span>
    );
  }

  if (s === 'facebook') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/80 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800/50">
        <Facebook className="w-3 h-3 text-blue-600 dark:text-blue-400 shrink-0" />
        Facebook
      </span>
    );
  }

  if (s === 'twitter') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200/80 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800/50">
        <Twitter className="w-3 h-3 text-sky-500 dark:text-sky-400 shrink-0" />
        Twitter / X
      </span>
    );
  }

  if (s === 'news_rss' || s === 'rss') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/50">
        <Rss className="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
        Google News
      </span>
    );
  }

  if (s === 'publisher_rss') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-violet-50 text-violet-700 border border-violet-200/80 dark:bg-violet-950/40 dark:text-violet-300 dark:border-violet-800/50">
        <Rss className="w-3 h-3 text-violet-600 dark:text-violet-400 shrink-0" />
        Publisher RSS
      </span>
    );
  }

  if (s === 'google_search') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/80 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800/50">
        <Globe className="w-3 h-3 text-blue-600 dark:text-blue-400 shrink-0" />
        Google Search
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800/60 dark:text-slate-300 dark:border-slate-700/60">
      <Globe className="w-3 h-3 text-slate-500 dark:text-slate-400 shrink-0" />
      {source || 'Web'}
    </span>
  );
}
