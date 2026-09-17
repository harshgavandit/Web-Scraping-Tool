import React, { useState } from 'react';
import {
  ExternalLink,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  RotateCcw,
  Eye,
  User,
  Clock,
  Target,
  ThumbsUp,
  MessagesSquare,
  Share2,
} from 'lucide-react';
import SourceBadge from './SourceBadge';
import SentimentBadge from './SentimentBadge';
import ViralityBadge from './ViralityBadge';
import { safeExternalUrl } from '../utils/safeUrl';

const formatDate = (isoValue) => {
  if (!isoValue) return 'Unknown time';
  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) return isoValue;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

export default function ChatterTable({
  posts,
  loading,
  pagination,
  onPageChange,
  onSelectPost,
  onResetFilters,
  brandName = 'Nike',
}) {
  const [expandedRows, setExpandedRows] = useState({});

  const toggleRow = (id, event) => {
    event.stopPropagation();
    setExpandedRows((current) => ({ ...current, [id]: !current[id] }));
  };

  if (loading) {
    return (
      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-subtle dark:border-slate-800 dark:bg-slate-900" aria-label="Loading brand conversations" aria-busy="true">
        <div className="grid min-w-[760px] grid-cols-[2.2fr_1.1fr_1fr_1.1fr_1.8fr_44px] gap-5 border-b border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/40">
          {[28, 18, 16, 20, 30, 6].map((width, index) => <div key={index} className="h-3 rounded bg-slate-200 dark:bg-slate-800 animate-pulse" style={{ width: `${width * 3}px` }} />)}
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {[...Array(7)].map((_, row) => (
            <div key={row} className="grid min-w-[760px] grid-cols-[2.2fr_1.1fr_1fr_1.1fr_1.8fr_44px] gap-5 px-4 py-4">
              {[42, 24, 20, 24, 38, 8].map((width, index) => <div key={index} className="h-4 rounded bg-slate-100 dark:bg-slate-800 animate-shimmer" style={{ width: `${Math.min(width * 3, 180)}px` }} />)}
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!posts?.length) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white px-6 py-14 text-center shadow-subtle dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"><MessageSquare className="h-5 w-5" /></div>
        <h3 className="mt-4 text-sm font-semibold text-slate-900 dark:text-white">No conversations found</h3>
        <p className="mx-auto mt-1.5 max-w-sm text-xs leading-5 text-slate-500 dark:text-slate-400">Try changing your filters or expanding the analysis window.</p>
        {onResetFilters && <button type="button" onClick={onResetFilters} className="mt-4 inline-flex h-9 items-center gap-1.5 rounded-lg bg-slate-900 px-3 text-xs font-semibold text-white transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 dark:bg-white dark:text-slate-950"><RotateCcw className="h-3.5 w-3.5" />Clear filters</button>}
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-subtle dark:border-slate-800 dark:bg-slate-900" aria-label="Brand conversations">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Brand conversations</h2>
          <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Open a conversation for complete AI analysis and recommended action.</p>
        </div>
        <span className="hidden rounded-md bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-500 sm:inline dark:bg-slate-800 dark:text-slate-300">{pagination.total.toLocaleString()} results</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] table-fixed border-collapse text-left text-xs">
          <thead className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur dark:bg-slate-950/95">
            <tr className="border-b border-slate-200 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="w-[34%] px-4 py-3">Conversation</th>
              <th className="hidden w-[17%] px-3 py-3 md:table-cell">Context</th>
              <th className="w-[15%] px-3 py-3">Sentiment</th>
              <th className="w-[18%] px-3 py-3">Impact</th>
              <th className="hidden w-[28%] px-3 py-3 xl:table-cell">Intelligence</th>
              <th className="w-12 px-3 py-3"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {posts.map((post) => {
              const analysis = post.analysis || {};
              const externalUrl = safeExternalUrl(post.url);
              const expanded = Boolean(expandedRows[post.id]);
              const isViral = analysis.is_viral || String(analysis.virality_level).toLowerCase() === 'viral';
              const title = post.title || post.content?.slice(0, 72) || 'Untitled conversation';

              return (
                <React.Fragment key={post.id}>
                  <tr
                    tabIndex={0}
                    aria-label={`${title}. ${analysis.sentiment || 'Neutral'} sentiment. Open conversation details.`}
                    onClick={() => onSelectPost(post)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onSelectPost(post);
                      }
                    }}
                    className={`group cursor-pointer outline-none transition-colors focus-visible:bg-indigo-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500/50 dark:focus-visible:bg-indigo-950/30 ${isViral ? 'bg-violet-50/35 hover:bg-violet-50/70 dark:bg-violet-950/10 dark:hover:bg-violet-950/25' : 'hover:bg-slate-50/80 dark:hover:bg-slate-950/40'}`}
                  >
                    <td className="px-4 py-3 align-top">
                      <div className="flex items-start gap-2.5">
                        <button type="button" aria-expanded={expanded} aria-label={`${expanded ? 'Collapse' : 'Expand'} ${title}`} onClick={(event) => toggleRow(post.id, event)} className="mt-0.5 rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:hover:bg-slate-800 dark:hover:text-white">
                          {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                        </button>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2"><SourceBadge source={post.source} /><span className="truncate font-semibold text-slate-900 transition group-hover:text-indigo-700 dark:text-white dark:group-hover:text-indigo-300">{title}</span></div>
                          <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-slate-500 dark:text-slate-400">{post.content}</p>
                          <div className="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[10px] text-slate-400 dark:text-slate-500">
                            {post.author && <span className="inline-flex items-center gap-1"><User className="h-3 w-3" />{post.author}</span>}
                            <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{formatDate(post.published_at)}</span>
                            {externalUrl && <a href={externalUrl} target="_blank" rel="noopener noreferrer" onClick={(event) => event.stopPropagation()} aria-label={`Open original ${post.source} conversation`} className="inline-flex items-center gap-1 font-medium text-indigo-600 hover:underline dark:text-indigo-400"><ExternalLink className="h-3 w-3" />Original</a>}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="hidden px-3 py-3 align-top md:table-cell">
                      <div className="space-y-1.5">
                        <span className="inline-flex max-w-full truncate rounded-md bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">{analysis.topic || 'General'}</span>
                        <div className="truncate text-[10px] text-slate-500 dark:text-slate-400">{brandName}{analysis.competitor ? ` vs ${analysis.competitor}` : ''}</div>
                        {analysis.product && <div className="truncate text-[10px] font-medium text-slate-600 dark:text-slate-300">{analysis.product}</div>}
                      </div>
                    </td>

                    <td className="px-3 py-3 align-top"><SentimentBadge sentiment={analysis.sentiment} score={analysis.sentiment_score} showScore={false} /></td>

                    <td className="px-3 py-3 align-top">
                      <ViralityBadge score={analysis.virality_score} level={analysis.virality_level} isViral={analysis.is_viral} showOutOfHundred={isViral} velocity={post.engagement_velocity} comments={post.comments} shares={post.shares} />
                      <div className="mt-2 flex items-center gap-2 text-[10px] tabular-nums text-slate-500 dark:text-slate-400">
                        <span className="font-semibold text-slate-700 dark:text-slate-200">{(post.engagement_count || 0).toLocaleString()}</span>
                        <span title="Likes" className="hidden items-center gap-0.5 sm:inline-flex"><ThumbsUp className="h-3 w-3" />{post.likes || 0}</span>
                        <span title="Comments" className="hidden items-center gap-0.5 lg:inline-flex"><MessagesSquare className="h-3 w-3" />{post.comments || 0}</span>
                      </div>
                    </td>

                    <td className="hidden px-3 py-3 align-top xl:table-cell">
                      <p className="line-clamp-2 text-[11px] leading-4 text-slate-600 dark:text-slate-300" title={analysis.summary}>{analysis.summary || 'AI summary unavailable.'}</p>
                      <div className="mt-2 flex items-start gap-1.5 rounded-lg border border-emerald-200/70 bg-emerald-50/70 p-2 text-[10px] leading-4 text-emerald-900 dark:border-emerald-800/50 dark:bg-emerald-950/30 dark:text-emerald-200"><Target className="mt-0.5 h-3 w-3 shrink-0" /><span className="line-clamp-2">{analysis.recommendation || 'Continue monitoring.'}</span></div>
                    </td>

                    <td className="px-3 py-3 text-right align-top">
                      <button type="button" onClick={(event) => { event.stopPropagation(); onSelectPost(post); }} aria-label={`View details for ${title}`} className="rounded-lg p-2 text-slate-400 transition hover:bg-indigo-50 hover:text-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:hover:bg-indigo-950/50 dark:hover:text-indigo-300"><Eye className="h-4 w-4" /></button>
                    </td>
                  </tr>

                  {expanded && (
                    <tr className="bg-slate-50/80 dark:bg-slate-950/40">
                      <td colSpan={6} className="px-5 py-4 sm:pl-12">
                        <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
                          <div><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Full conversation</div><p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-slate-700 dark:text-slate-200">{post.content}</p></div>
                          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">AI signal</div><p className="mt-2 text-xs leading-5 text-slate-700 dark:text-slate-200">{analysis.summary || 'AI summary unavailable.'}</p>{analysis.key_positive && <p className="mt-2 text-[11px] text-emerald-700 dark:text-emerald-300"><strong>Positive:</strong> {analysis.key_positive}</p>}{analysis.key_negative && <p className="mt-1 text-[11px] text-rose-700 dark:text-rose-300"><strong>Concern:</strong> {analysis.key_negative}</p>}</div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <footer className="flex flex-col items-center justify-between gap-3 border-t border-slate-200 bg-slate-50/70 px-4 py-3 text-xs text-slate-500 sm:flex-row dark:border-slate-800 dark:bg-slate-950/30 dark:text-slate-400">
        <span>Showing <strong className="text-slate-900 dark:text-white">{(pagination.page - 1) * pagination.page_size + 1}–{Math.min(pagination.page * pagination.page_size, pagination.total)}</strong> of <strong className="text-slate-900 dark:text-white">{pagination.total.toLocaleString()}</strong></span>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => onPageChange(pagination.page - 1)} disabled={pagination.page <= 1} className="h-8 rounded-lg border border-slate-200 bg-white px-3 font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800">Previous</button>
          <span className="min-w-20 text-center tabular-nums">Page {pagination.page} of {pagination.pages || 1}</span>
          <button type="button" onClick={() => onPageChange(pagination.page + 1)} disabled={pagination.page >= pagination.pages} className="h-8 rounded-lg border border-slate-200 bg-white px-3 font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800">Next</button>
        </div>
      </footer>
    </section>
  );
}
