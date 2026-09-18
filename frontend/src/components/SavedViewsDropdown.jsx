import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bookmark,
  ChevronDown,
  Plus,
  Trash2,
  Check,
  Users,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';

export default function SavedViewsDropdown({
  brandId = 1,
  currentFilters,
  onApplyView,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [views, setViews] = useState([]);
  const [activeViewId, setActiveViewId] = useState(null);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [newViewName, setNewViewName] = useState('');
  const [newViewTeam, setNewViewTeam] = useState('brand');
  const [saving, setSaving] = useState(false);
  const dropdownRef = useRef(null);

  const fetchSavedViews = useCallback(async () => {
    try {
      const data = await api.getSavedViews(brandId);
      setViews(data || []);
    } catch (err) {
      console.error('Failed to load saved views:', err);
    }
  }, [brandId]);

  useEffect(() => {
    fetchSavedViews();
  }, [fetchSavedViews]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
        setShowSaveForm(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectView = (view) => {
    setActiveViewId(view.id);
    onApplyView(view.filters || {});
    setIsOpen(false);
  };

  const handleSaveView = async (e) => {
    e.preventDefault();
    if (!newViewName.trim()) return;
    setSaving(true);
    try {
      const cleanFilters = {
        source: currentFilters.source,
        sentiment: currentFilters.sentiment,
        topic: currentFilters.topic,
        product: currentFilters.product,
        competitor: currentFilters.competitor,
        virality_level: currentFilters.virality_level,
        viral: currentFilters.viral,
        search: currentFilters.search,
        sort_by: currentFilters.sort_by,
      };
      const created = await api.createSavedView({
        brand_id: brandId,
        name: newViewName.trim(),
        team: newViewTeam,
        filters: cleanFilters,
      });
      await fetchSavedViews();
      setActiveViewId(created.id);
      setShowSaveForm(false);
      setNewViewName('');
    } catch (err) {
      console.error('Failed to create saved view:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteView = async (e, viewId) => {
    e.stopPropagation();
    try {
      await api.deleteSavedView(viewId);
      if (activeViewId === viewId) setActiveViewId(null);
      await fetchSavedViews();
    } catch (err) {
      console.error('Failed to delete saved view:', err);
    }
  };

  const activeView = views.find((v) => v.id === activeViewId);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <Bookmark className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
        <span className="truncate max-w-[130px]">
          {activeView ? activeView.name : 'Saved Views'}
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute left-0 sm:right-0 sm:left-auto mt-1.5 w-72 origin-top-right rounded-xl border border-slate-200 bg-white p-2 shadow-lg ring-1 ring-black/5 focus:outline-none z-30 dark:border-slate-800 dark:bg-slate-900">
          <div className="px-2 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Team Views
          </div>

          <div className="max-h-52 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
            {views.length === 0 ? (
              <div className="py-3 text-center text-xs text-slate-400">
                No saved views yet. Save current filters below.
              </div>
            ) : (
              views.map((view) => (
                <div
                  key={view.id}
                  onClick={() => handleSelectView(view)}
                  className="group flex cursor-pointer items-center justify-between px-2 py-2 text-xs rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate font-semibold text-slate-800 dark:text-slate-100">
                        {view.name}
                      </span>
                      {activeViewId === view.id && (
                        <Check className="h-3 w-3 text-indigo-600" />
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400 capitalize">
                      {view.team} team
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteView(e, view.id)}
                    aria-label={`Delete ${view.name}`}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Save Current View Action */}
          <div className="border-t border-slate-100 pt-2 mt-1 dark:border-slate-800">
            {!showSaveForm ? (
              <button
                type="button"
                onClick={() => setShowSaveForm(true)}
                className="flex w-full items-center gap-1.5 px-2 py-1.5 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 rounded-lg dark:text-indigo-400 dark:hover:bg-indigo-950/40 cursor-pointer"
              >
                <Plus className="h-3.5 w-3.5" />
                Save Current Filters as View
              </button>
            ) : (
              <form onSubmit={handleSaveView} className="p-1 space-y-2">
                <input
                  type="text"
                  placeholder="View name (e.g. Running Issues)"
                  value={newViewName}
                  onChange={(e) => setNewViewName(e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-2 py-1 text-xs outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                  autoFocus
                />
                <select
                  value={newViewTeam}
                  onChange={(e) => setNewViewTeam(e.target.value)}
                  className="w-full rounded-md border border-slate-200 px-2 py-1 text-xs outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                >
                  <option value="brand">Brand Strategy</option>
                  <option value="category">Category / Running</option>
                  <option value="regional">Regional PR</option>
                  <option value="executive">Executive</option>
                </select>
                <div className="flex justify-end gap-1.5 pt-1">
                  <button
                    type="button"
                    onClick={() => setShowSaveForm(false)}
                    className="px-2 py-1 text-[11px] font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving || !newViewName.trim()}
                    className="rounded bg-indigo-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save View'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
