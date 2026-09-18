import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { api } from '../services/api';

export default function PostDetailsDrawer({ post, onClose, onPostUpdated }) {
  const closeRef = useRef(null);
  const [livePost, setLivePost] = useState(post);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const refreshedPostId = useRef(null);

  const refreshGeminiAnalysis = useCallback(async () => {
    if (!post?.id || !api.refreshPostAnalysis || refreshedPostId.current === post.id) return;
    refreshedPostId.current = post.id;
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const refreshed = await api.refreshPostAnalysis(post.id);
      if (refreshed) {
        setLivePost(refreshed);
        onPostUpdated?.(refreshed);
      }
    } catch (error) {
      setAnalysisError(error.message || 'Gemini analysis is temporarily unavailable.');
      try {
        const current = await api.getPostDetail(post.id);
        if (current) setLivePost(current);
      } catch (_) {}
    } finally {
      setAnalysisLoading(false);
    }
  }, [post?.id]);

  useEffect(() => {
    setLivePost(post);
    const analysis = post?.analysis;
    if (post?.id && (!analysis?.summary || analysis?.analysis_provider !== 'gemini' || analysis?.analysis_status !== 'completed')) {
      refreshGeminiAnalysis();
    }
  }, [post, refreshGeminiAnalysis]);

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
    if (!livePost) return '';
    const reasons = [];
    if ((livePost.engagement_velocity || 0) >= 50) reasons.push('rapid engagement growth');
    if ((livePost.comments || 0) >= 100) reasons.push('high comment activity');
    if ((livePost.shares || 0) >= 50) reasons.push('strong sharing activity');
    if (reasons.length === 0) reasons.push('current engagement volume and momentum');
    return `${reasons[0].charAt(0).toUpperCase()}${reasons[0].slice(1)}${reasons.length > 1 ? `, ${reasons.slice(1).join(', ')}` : ''}.`;
  }, [livePost]);

  if (!livePost) return null;
  const analysis = livePost.analysis || {};
  const sourceDocument = livePost.document;
  const latestSnapshot = sourceDocument?.snapshots?.[0];
  const productEvidence = latestSnapshot?.extracted_data?.product_data || {};
  const externalUrl = safeExternalUrl(livePost.url);
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
        className="flex h-full w-full max-w-[760px] animate-drawer-in flex-col border-l border-slate-200/80 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900"
      >
        <header className="flex items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 py-4 backdrop-blur sm:px-6 dark:border-slate-800 dark:bg-slate-900/90">
          <div className="min-w-0">
            <div className="flex items-center gap-2"><SourceBadge source={livePost.source} />{isViral && <span className="rounded-md bg-violet-100 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-violet-700 dark:bg-violet-950/60 dark:text-violet-300">Viral</span>}</div>
            <h2 id="conversation-intelligence-title" className="mt-1.5 text-sm font-semibold text-slate-900 dark:text-white">Conversation intelligence</h2>
          </div>
          <button ref={closeRef} type="button" onClick={onClose} aria-label="Close conversation intelligence" className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:hover:bg-slate-800 dark:hover:text-white"><X className="h-5 w-5" /></button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
          <section>
            <div className="flex items-center justify-between gap-3"><h3 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">Original Post</h3>{externalUrl && <a href={externalUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline dark:text-indigo-400">View original<ExternalLink className="h-3.5 w-3.5" /></a>}</div>
            <h4 className="mt-3 text-lg font-semibold leading-6 text-slate-950 dark:text-white">{livePost.title || 'Brand conversation'}</h4>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center gap-1"><User className="h-3.5 w-3.5" />{livePost.author || 'Anonymous'}</span>
              <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{livePost.published_at ? new Date(livePost.published_at).toLocaleString() : 'Unknown time'}</span>
            </div>
            <p className="mt-4 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200">{livePost.content}</p>
          </section>

          {sourceDocument && (
            <section className="mt-5 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/30" aria-label="Original source evidence">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">Original Source Evidence</h3>
                <span className={`rounded-md px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${sourceDocument.content_status === 'fetched' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'}`}>
                  {sourceDocument.content_status === 'fetched' ? 'Source fetched' : sourceDocument.content_status}
                </span>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
                <div><dt className="text-slate-500">Publisher</dt><dd className="mt-0.5 font-semibold text-slate-800 dark:text-slate-200">{sourceDocument.publisher || sourceDocument.domain || 'Unknown'}</dd></div>
                <div><dt className="text-slate-500">Source type</dt><dd className="mt-0.5 font-semibold capitalize text-slate-800 dark:text-slate-200">{String(sourceDocument.source_type || 'article').replaceAll('_', ' ')}</dd></div>
                <div><dt className="text-slate-500">Language</dt><dd className="mt-0.5 font-semibold uppercase text-slate-800 dark:text-slate-200">{sourceDocument.language || 'Unknown'}</dd></div>
                <div><dt className="text-slate-500">Crawler access</dt><dd className="mt-0.5 font-semibold text-slate-800 dark:text-slate-200">{sourceDocument.robots_allowed === true ? 'Allowed' : sourceDocument.robots_allowed === false ? 'Blocked' : 'Not checked'}</dd></div>
              </dl>
              {(productEvidence.rating_value != null || productEvidence.review_count != null) && (
                <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3 text-xs dark:border-slate-800">
                  {productEvidence.name && <span className="font-semibold text-slate-800 dark:text-slate-200">{productEvidence.name}</span>}
                  {productEvidence.rating_value != null && <span className="rounded-md bg-amber-50 px-2 py-0.5 font-semibold text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">{productEvidence.rating_value} / 5</span>}
                  {productEvidence.review_count != null && <span className="text-slate-500">{Number(productEvidence.review_count).toLocaleString()} reviews</span>}
                </div>
              )}
            </section>
          )}

          <section className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Conversation performance">
            <Metric icon={ThumbsUp} label="Likes" value={livePost.likes || 0} />
            <Metric icon={MessageSquare} label="Comments" value={livePost.comments || 0} />
            <Metric icon={Share2} label="Shares" value={livePost.shares || 0} />
            <Metric icon={Activity} label="Per hour" value={livePost.engagement_velocity || 0} />
          </section>

          <section className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-indigo-700 dark:text-indigo-300"><Sparkles className="h-4 w-4" />AI Summary</div>
            <p className="mt-2 text-sm leading-6 text-slate-800 dark:text-slate-200">{analysisLoading ? 'Gemini is analyzing this article...' : analysis.summary || 'Gemini analysis is not available for this article yet.'}</p>
            {analysisError && <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-800/60 dark:bg-amber-950/30 dark:text-amber-200"><span>Gemini could not complete the live analysis.</span><button type="button" onClick={refreshGeminiAnalysis} className="shrink-0 font-semibold text-indigo-700 hover:underline dark:text-indigo-300">Retry Gemini</button></div>}
          </section>

          <section className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-400" aria-label="AI audit trail">
            <span className="font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">AI audit</span>
            <span>Provider: <strong className="font-semibold text-slate-700 dark:text-slate-200">{analysis.analysis_provider || 'gemini'}</strong></span>
            <span>Model: <strong className="font-semibold text-slate-700 dark:text-slate-200">{analysis.model_used || 'Gemini configured model'}</strong></span>
            <span>Status: <strong className="font-semibold text-slate-700 dark:text-slate-200">{analysisLoading ? 'processing' : analysis.analysis_status || 'pending'}</strong></span>
            <span>Version: <strong className="font-semibold text-slate-700 dark:text-slate-200">{analysis.analysis_version || '1.0'}</strong></span>
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
              <ViralityBadge score={analysis.virality_score} level={analysis.virality_level} isViral={analysis.is_viral} showOutOfHundred velocity={livePost.engagement_velocity} comments={livePost.comments} shares={livePost.shares} />
              <p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{viralityReason}</p>
            </InfoCard>
          </section>

          <section className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800/60 dark:bg-emerald-950/30">
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.1em] text-emerald-800 dark:text-emerald-300"><Target className="h-4 w-4" />Recommended Action</div>
            <p className="mt-2 text-sm font-semibold leading-6 text-emerald-950 dark:text-emerald-100">{analysis.recommendation || 'Waiting for Gemini analysis.'}</p>
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
