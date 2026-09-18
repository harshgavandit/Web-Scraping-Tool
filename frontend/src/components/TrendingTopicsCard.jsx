import React from 'react';
import { TrendingUp, ArrowUpRight, ArrowDownRight, Swords } from 'lucide-react';

export default function TrendingTopicsCard({
  topics = [],
  loading = false,
  onSelectTopic,
  competitors = [],
  onSelectCompetitor,
  activeTopic = 'all',
  activeCompetitor = 'all',
  windowDays = 7,
}) {
  const displayTopics = topics?.slice(0, 4) || [];
  const displayCompetitors = competitors?.slice(0, 4) || [];

  return (
    <div className="flex flex-col justify-between rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] transition-all dark:border-slate-800 dark:bg-slate-900/85">
      {/* Header */}
      <div>
        <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-indigo-50 p-1.5 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
              <TrendingUp className="w-3.5 h-3.5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Trending Now
            </h3>
          </div>
          <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500">
            Prior {windowDays} days
          </span>
        </div>

        {/* Topics List */}
        {loading ? (
          <div className="space-y-2 py-1">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-7 bg-slate-100 dark:bg-slate-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : displayTopics.length > 0 ? (
          <div className="space-y-1.5">
            {displayTopics.map((item, idx) => {
              const isPositive = (item.pct_change || 0) >= 0;
              const isSelected = activeTopic && activeTopic.toLowerCase() === item.topic.toLowerCase();

              return (
                <button
                  type="button"
                  key={idx}
                  aria-pressed={isSelected}
                  onClick={() => onSelectTopic && onSelectTopic(isSelected ? 'all' : item.topic)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all group ${
                    isSelected
                      ? 'border border-indigo-200 bg-indigo-50 text-indigo-900 font-semibold dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-200'
                      : 'border border-transparent text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800/60'
                  }`}
                  title={`Click to filter chatter by ${item.topic}`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500 w-3">
                      {idx + 1}.
                    </span>
                    <span className="truncate font-medium text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                      {item.topic}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <span
                      className={`inline-flex items-center text-[11px] font-semibold ${
                        isPositive
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {isPositive ? (
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      ) : (
                        <ArrowDownRight className="w-3.5 h-3.5" />
                      )}
                      <span>{Math.abs(Math.round(item.pct_change || 0))}%</span>
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="flex min-h-28 items-center justify-center rounded-xl border border-dashed border-slate-200 px-4 text-center text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
            Trending topics will appear as conversation volume changes.
          </div>
        )}
      </div>

      {/* Competitor Benchmarking Pills */}
      {displayCompetitors.length > 0 && <div className="pt-3 mt-3 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-2">
          <Swords className="w-3 h-3 text-slate-400" />
          <span>Competitor Mentions</span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {displayCompetitors.map((comp) => {
            const isSelected = activeCompetitor && activeCompetitor.toLowerCase() === comp.toLowerCase();
            return (
              <button
                type="button"
                key={comp}
                aria-pressed={isSelected}
                onClick={() => onSelectCompetitor && onSelectCompetitor(isSelected ? 'all' : comp)}
                className={`text-[10px] px-2 py-0.5 rounded-md font-medium transition-all ${
                  isSelected
                    ? 'bg-rose-600 text-white shadow-2xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200/60 dark:border-slate-700/60'
                }`}
                title={`Filter discussions mentioning ${comp}`}
              >
                vs {comp}
              </button>
            );
          })}
        </div>
      </div>}
    </div>
  );
}
