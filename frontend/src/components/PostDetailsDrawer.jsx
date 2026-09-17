import React, { useEffect, useMemo, useRef } from 'react';
import {
  X,
  ExternalLink,
  ThumbsUp,
  MessageSquare,
  Share2,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Target,
  Swords,
  Clock,
  User,
  Activity,
} from 'lucide-react';
import SourceBadge from './SourceBadge';
import SentimentBadge from './SentimentBadge';
import ViralityBadge from './ViralityBadge';
import { safeExternalUrl } from '../utils/safeUrl';

export default function PostDetailsDrawer({ post, onClose }) {
  const closeRef = useRef(null);

  useEffect(() => {
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus?.();
    };
  }, [onClose]);

  const viralityReason = useMemo(() => {
    if (!post) return '';
    const reasons = [];
    if ((post.engagement_velocity || 0) >= 50) reasons.push('rapid engagement growth');
    if ((post.comments || 0) >= 100) reasons.push('high comment activity');
    if ((post.shares || 0) >= 50) reasons.push('strong sharing activity');
    if (reasons.length === 0) reasons.push('current engagement volume and momentum');
    return `${reasons[0].charAt(0).toUpperCase()}${reasons[0].slice(1)}${reasons.length > 1 ? `, ${reasons.slice(1).join(', ')}` : ''}.`;
  }, [post]);

  if (!post) return null;
  const analysis = post.analysis || {};
  const externalUrl = safeExternalUrl(post.url);
  const isViral = analysis.is_viral || String(analysis.virality_level).toLowerCase() === 'viral';
  const why = analysis.key_positive && analysis.key_negative
    ? `The conversation balances praise for ${analysis.key_positive} with concern about ${analysis.key_negative}.`
    : analysis.key_negative
      ? `The main concern is ${analysis.key_negative}.`
      : analysis.key_positive
        ? `The strongest positive signal is ${analysis.key_positive}.`
        : analysis.summary || `The language and context indicate ${String(analysis.sentiment || 'neutral').toLowerCase()} sentiment.`;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/45 backdrop-blur-[2px]" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="conversation-intelligence-title"
        className="flex h-full w-full max-w-2xl animate-drawer-in flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900"
      >
        <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3.5 sm:px-6 dark:border-slate-800">
          <div className="min-w-0">
            <div className="flex items-center gap-2"><SourceBadge source={post.source} />{isViral && <span className="rounded-md bg-violet-100 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-violet-700 dark:bg-violet-950/60 dark:text-violet-300">Viral</span>}</div>
            <h2 id="conversation-intelligence-title" className="mt-1.5 text-sm font-semibold text-slate-900 dark:text-white">Conversation intelligence</h2>
          </div>
          <button ref={closeRef} type="button" onClick={onClose} aria-label="Close conversation intelligence" className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:hover:bg-slate-800 dark:hover:text-white"><X className="h-5 w-5" /></button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
          <section>
            <div className="flex items-center justify-between gap-3"><h3 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">Original Post</h3>{externalUrl && <a href={externalUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline dark:text-indigo-400">View original<ExternalLink className="h-3.5 w-3.5" /></a>}</div>
            <h4 className="mt-3 text-lg font-semibold leading-6 text-slate-950 dark:text-white">{post.title || 'Brand conversation'}</h4>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center gap-1"><User className="h-3.5 w-3.5" />{post.author || 'Anonymous'}</span>
              <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{post.published_at ? new Date(post.published_at).toLocaleString() : 'Unknown time'}</span>
            </div>
            <p className="mt-4 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200">{post.content}</p>
          </section>

          <section className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Conversation performance">
            <Metric icon={ThumbsUp} label="Likes" value={post.likes || 0} />
            <Metric icon={MessageSquare} label="Comments" value={post.comments || 0} />
            <Metric icon={Share2} label="Shares" value={post.shares || 0} />
            <Metric icon={Activity} label="Per hour" value={post.engagement_velocity || 0} />
          </section>

          <section className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-indigo-700 dark:text-indigo-300"><Sparkles className="h-4 w-4" />AI Summary</div>
            <p className="mt-2 text-sm leading-6 text-slate-800 dark:text-slate-200">{analysis.summary || 'AI summary is not available for this conversation yet.'}</p>
          </section>

          <section className="mt-6 grid gap-3 sm:grid-cols-2">
            <InfoCard label="Sentiment"><SentimentBadge sentiment={analysis.sentiment} score={analysis.sentiment_score} /></InfoCard>
            <InfoCard label="Why"><p className="text-xs leading-5 text-slate-700 dark:text-slate-200">{why}</p></InfoCard>
            <InfoCard label="Key Positive" icon={CheckCircle2} tone="positive"><p className="text-xs leading-5">{analysis.key_positive || 'No clear positive driver identified.'}</p></InfoCard>
            <InfoCard label="Key Negative" icon={AlertTriangle} tone="negative"><p className="text-xs leading-5">{analysis.key_negative || 'No clear negative driver identified.'}</p></InfoCard>
          </section>

          <section className="mt-6 grid gap-3 sm:grid-cols-2">
            <InfoCard label="Context">
              <dl className="space-y-2 text-xs">
                <div className="flex justify-between gap-3"><dt className="text-slate-500">Topic</dt><dd className="text-right font-semibold text-slate-800 dark:text-slate-200">{analysis.topic || 'General'}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-slate-500">Product</dt><dd className="text-right font-semibold text-slate-800 dark:text-slate-200">{analysis.product || 'Not identified'}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-slate-500">Competitor</dt><dd className="inline-flex items-center gap-1 text-right font-semibold text-slate-800 dark:text-slate-200">{analysis.competitor && <Swords className="h-3.5 w-3.5" />}{analysis.competitor || 'None mentioned'}</dd></div>
              </dl>
            </InfoCard>
            <InfoCard label="Virality">
              <ViralityBadge score={analysis.virality_score} level={analysis.virality_level} isViral={analysis.is_viral} showOutOfHundred velocity={post.engagement_velocity} comments={post.comments} shares={post.shares} />
              <p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{viralityReason}</p>
            </InfoCard>
          </section>

          <section className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800/60 dark:bg-emerald-950/30">
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em] text-emerald-800 dark:text-emerald-300"><Target className="h-4 w-4" />Recommended Action</div>
            <p className="mt-2 text-sm font-semibold leading-6 text-emerald-950 dark:text-emerald-100">{analysis.recommendation || 'Continue monitoring this conversation for meaningful changes.'}</p>
          </section>
        </div>
      </aside>
    </div>
  );
}

function Metric({ icon: Icon, label, value }) {
  return <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950/30"><div className="flex items-center gap-1.5 text-[10px] font-medium text-slate-500 dark:text-slate-400"><Icon className="h-3.5 w-3.5" />{label}</div><div className="mt-1 text-base font-semibold tabular-nums text-slate-900 dark:text-white">{Number(value).toLocaleString()}</div></div>;
}

function InfoCard({ label, icon: Icon, tone, children }) {
  const toneClass = tone === 'positive' ? 'border-emerald-200 bg-emerald-50/70 text-emerald-900 dark:border-emerald-800/50 dark:bg-emerald-950/30 dark:text-emerald-200' : tone === 'negative' ? 'border-rose-200 bg-rose-50/70 text-rose-900 dark:border-rose-800/50 dark:bg-rose-950/30 dark:text-rose-200' : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950/30';
  return <div className={`rounded-xl border p-4 ${toneClass}`}><div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">{Icon && <Icon className="h-3.5 w-3.5" />}{label}</div>{children}</div>;
}
