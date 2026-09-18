import React, { useState } from 'react';
import {
  Flame,
  SlidersHorizontal,
  RotateCcw,
  X,
  TrendingDown,
  TrendingUp,
  Swords,
  ArrowUpDown,
  ChevronDown,
} from 'lucide-react';
import SearchBar from './SearchBar';
import SavedViewsDropdown from './SavedViewsDropdown';

const controlClass = 'h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200';

export default function FilterBar({
  filters,
  onChange,
  onReset,
  brands = [],
  competitors = [],
  products = [],
  topics = [],
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const update = (key, value) => onChange({ ...filters, [key]: value, page: 1 });
  const applyQuickFilter = (changes) => onChange({
    ...filters,
    sentiment: 'all',
    competitor: 'all',
    viral: false,
    sort_by: 'newest',
    ...changes,
    page: 1,
  });
  const resetValue = (key) => update(key, key === 'viral' ? false : key === 'search' ? '' : 'all');

  const chips = [];
  const chip = (key, label) => chips.push({ key, label, onRemove: () => resetValue(key) });
  if (filters.viral) chip('viral', 'Viral');
  if (filters.sentiment && filters.sentiment !== 'all') chip('sentiment', filters.sentiment);
  if (filters.source && filters.source !== 'all') chip('source', filters.source === 'news_rss' ? 'News' : filters.source === 'publisher_rss' ? 'Publisher RSS' : filters.source);
  if (filters.topic && filters.topic !== 'all') chip('topic', filters.topic);
  if (filters.competitor && filters.competitor !== 'all') chip('competitor', filters.competitor);
  if (filters.product && filters.product !== 'all') chip('product', filters.product);
  if (filters.virality_level && filters.virality_level !== 'all') chip('virality_level', filters.virality_level);
  if (filters.search?.trim()) chip('search', `“${filters.search}”`);

  const advancedCount = [filters.source, filters.topic, filters.product, filters.competitor, filters.virality_level]
    .filter((value) => value && value !== 'all').length;
  const quickClass = (active, activeStyle) => `inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 ${active ? activeStyle : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'}`;
  const competitorSelected = filters.competitor && filters.competitor !== 'all';
  const allSelected = !filters.viral
    && (!filters.sentiment || filters.sentiment === 'all')
    && (!filters.source || filters.source === 'all')
    && (!filters.topic || filters.topic === 'all')
    && (!filters.product || filters.product === 'all')
    && (!filters.competitor || filters.competitor === 'all')
    && (!filters.virality_level || filters.virality_level === 'all')
    && !filters.search?.trim();

  return (
    <section className="mb-4 rounded-2xl border border-slate-200/80 bg-white/90 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-slate-800 dark:bg-slate-900/85" aria-label="Search and filter conversations">
      <div className="flex flex-col gap-3 p-3.5 2xl:flex-row 2xl:items-center">
        <div className="min-w-0 flex-1 2xl:max-w-md">
          <SearchBar value={filters.search} onChange={(value) => update('search', value)} />
        </div>

        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5" aria-label="Quick filters">
          <button type="button" aria-pressed={allSelected} onClick={onReset} className={quickClass(allSelected, 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-950')}>All</button>
          <button type="button" aria-pressed={filters.sentiment === 'Negative'} onClick={() => applyQuickFilter(filters.sentiment === 'Negative' ? {} : { sentiment: 'Negative', sort_by: 'most_negative' })} className={quickClass(filters.sentiment === 'Negative', 'border-rose-600 bg-rose-600 text-white')}><TrendingDown className="h-3.5 w-3.5" />Negative</button>
          <button type="button" aria-pressed={filters.sentiment === 'Positive'} onClick={() => applyQuickFilter(filters.sentiment === 'Positive' ? {} : { sentiment: 'Positive', sort_by: 'most_positive' })} className={quickClass(filters.sentiment === 'Positive', 'border-emerald-600 bg-emerald-600 text-white')}><TrendingUp className="h-3.5 w-3.5" />Positive</button>
          <button type="button" aria-label="Viral Only" aria-pressed={filters.viral} onClick={() => applyQuickFilter(filters.viral ? {} : { viral: true, sort_by: 'highest_virality' })} className={quickClass(filters.viral, 'border-violet-600 bg-violet-600 text-white')}><Flame className="h-3.5 w-3.5" />Viral</button>
          <button type="button" aria-pressed={Boolean(competitorSelected)} onClick={() => applyQuickFilter(competitorSelected ? {} : { competitor: 'any' })} className={quickClass(competitorSelected, 'border-indigo-600 bg-indigo-600 text-white')}><Swords className="h-3.5 w-3.5" />Competitors</button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 2xl:justify-end">
          <SavedViewsDropdown
            brandId={filters.brand_id || 1}
            currentFilters={filters}
            onApplyView={(viewFilters) => onChange({ ...filters, ...viewFilters, page: 1 })}
          />

          <button
            type="button"
            aria-expanded={showAdvanced}
            aria-controls="advanced-conversation-filters"
            onClick={() => setShowAdvanced((open) => !open)}
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            {showAdvanced ? 'Hide filters' : 'More filters'}
            {advancedCount > 0 && <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[10px] text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{advancedCount}</span>}
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          </button>
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
            <label className="sr-only" htmlFor="conversation-sort">Sort conversations</label>
            <select id="conversation-sort" value={filters.sort_by || 'newest'} onChange={(event) => update('sort_by', event.target.value)} className={controlClass}>
              <option value="newest">Newest First</option>
              <option value="highest_virality">Most Viral</option>
              <option value="highest_engagement">Highest Engagement</option>
              <option value="most_negative">Most Negative</option>
              <option value="most_positive">Most Positive</option>
              <option value="oldest">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {showAdvanced && (
        <div id="advanced-conversation-filters" className="grid grid-cols-2 gap-2 border-t border-slate-100 bg-slate-50/70 p-3.5 sm:grid-cols-3 lg:grid-cols-6 dark:border-slate-800 dark:bg-slate-950/30">
          {brands.length > 1 && (
            <select aria-label="Filter by brand" value={filters.brand_id || 1} onChange={(event) => update('brand_id', Number(event.target.value))} className={controlClass}>
              {brands.map((brand) => <option key={brand.id} value={brand.id}>{brand.name}</option>)}
            </select>
          )}
          <select aria-label="Filter by source" value={filters.source || 'all'} onChange={(event) => update('source', event.target.value)} className={controlClass}>
            <option value="all">All Live Sources</option><option value="news_rss">Google News</option><option value="publisher_rss">Publisher RSS / Atom</option><option value="google_search">Google Search</option>
          </select>
          <select aria-label="Filter by sentiment" value={filters.sentiment || 'all'} onChange={(event) => update('sentiment', event.target.value)} className={controlClass}>
            <option value="all">All Sentiments</option><option value="Positive">Positive</option><option value="Negative">Negative</option><option value="Mixed">Mixed</option><option value="Neutral">Neutral</option>
          </select>
          <select aria-label="Filter by topic" value={filters.topic || 'all'} onChange={(event) => update('topic', event.target.value)} className={controlClass}>
            <option value="all">All Topics</option>{topics.map((topic) => <option key={topic} value={topic}>{topic}</option>)}
          </select>
          <select aria-label="Filter by product" value={filters.product || 'all'} onChange={(event) => update('product', event.target.value)} className={controlClass}>
            <option value="all">All Products</option>{products.map((product) => <option key={product} value={product}>{product}</option>)}
          </select>
          <select aria-label="Filter by competitor" value={filters.competitor || 'all'} onChange={(event) => update('competitor', event.target.value)} className={controlClass}>
            <option value="all">All Competitors</option>{competitors.map((competitor) => <option key={competitor} value={competitor}>{competitor}</option>)}
          </select>
          <select aria-label="Filter by virality" value={filters.virality_level || 'all'} onChange={(event) => update('virality_level', event.target.value)} className={controlClass}>
            <option value="all">All Virality</option><option value="Viral">Viral</option><option value="High">High</option><option value="Medium">Medium</option><option value="Low">Low</option>
          </select>
        </div>
      )}

      {chips.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 border-t border-slate-100 px-3.5 py-2.5 dark:border-slate-800" aria-label="Active filters">
          {chips.map((item) => (
            <span key={item.key} className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200">
              {item.label}
              <button type="button" onClick={item.onRemove} aria-label={`Remove ${item.label} filter`} className="rounded-sm text-slate-400 hover:text-rose-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"><X className="h-3 w-3" /></button>
            </span>
          ))}
          <button type="button" onClick={onReset} className="ml-1 inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 hover:text-rose-600 dark:text-slate-400"><RotateCcw className="h-3 w-3" />Clear all</button>
        </div>
      )}
    </section>
  );
}
