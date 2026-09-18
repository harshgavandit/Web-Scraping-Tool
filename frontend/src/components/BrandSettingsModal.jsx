import React, { useState } from 'react';
import { X, Trash2, Check, Tag, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function BrandSettingsModal({ brand, onClose, onRefresh }) {
  const [newKeyword, setNewKeyword] = useState('');
  const [newCategory, setNewCategory] = useState('brand');
  const [newCompetitor, setNewCompetitor] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const refresh = async () => {
    if (onRefresh) await onRefresh();
  };

  const handleAddKeyword = async (e) => {
    e.preventDefault();
    if (!newKeyword.trim() || !brand?.id) return;
    setLoading(true);
    setStatus(null);
    try {
      await api.addKeyword(brand.id, {
        keyword: newKeyword.trim(),
        category: newCategory,
        active: true,
      });
      setNewKeyword('');
      await refresh();
      setStatus({ type: 'success', message: 'Tracked keyword added.' });
    } catch (err) {
      setStatus({ type: 'error', message: `Unable to add keyword. ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleAddCompetitor = async (e) => {
    e.preventDefault();
    if (!newCompetitor.trim() || !brand?.id) return;
    setLoading(true);
    setStatus(null);
    try {
      await api.addCompetitor(brand.id, {
        name: newCompetitor.trim(),
      });
      setNewCompetitor('');
      await refresh();
      setStatus({ type: 'success', message: 'Competitor added.' });
    } catch (err) {
      setStatus({ type: 'error', message: `Unable to add competitor. ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCompetitor = async (competitor) => {
    if (!brand?.id || loading) return;
    setLoading(true);
    setStatus(null);
    try {
      await api.deleteCompetitor(brand.id, competitor.id);
      await refresh();
      setStatus({ type: 'success', message: `${competitor.name} removed.` });
    } catch (err) {
      setStatus({ type: 'error', message: `Unable to remove ${competitor.name}. ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteKeyword = async (keyword) => {
    if (!brand?.id || loading) return;
    setLoading(true);
    setStatus(null);
    try {
      await api.deleteKeyword(brand.id, keyword.id);
      await refresh();
      setStatus({ type: 'success', message: `${keyword.keyword} removed.` });
    } catch (err) {
      setStatus({ type: 'error', message: `Unable to remove ${keyword.keyword}. ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  if (!brand) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center bg-slate-900/50 dark:bg-slate-950/70 backdrop-blur-xs p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-xl w-full shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-850">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Brand Configuration: {brand.name}</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Configure tracked products, competitors, and keywords</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close brand configuration"
            className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 text-xs max-h-[80vh] overflow-y-auto">
          {/* Tracked Competitors */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                Tracked Competitors
              </span>
              <span className="text-[11px] text-slate-400">{brand.competitors?.length || 0} configured</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {brand.competitors?.map((c) => (
                <span
                  key={c.id}
                  className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-lg border border-slate-200 dark:border-slate-700 font-medium flex items-center gap-1.5"
                >
                  <span>{c.name}</span>
                  <button
                    type="button"
                    onClick={() => handleDeleteCompetitor(c)}
                    disabled={loading}
                    aria-label={`Remove ${c.name} competitor`}
                    className="ml-0.5 rounded p-0.5 text-slate-400 hover:bg-rose-100 hover:text-rose-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 disabled:opacity-40 dark:hover:bg-rose-950/60"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>

            <form onSubmit={handleAddCompetitor} className="flex gap-2 pt-1">
              <input
                type="text"
                value={newCompetitor}
                onChange={(e) => setNewCompetitor(e.target.value)}
                placeholder="Add competitor (e.g. Asics, Hoka)..."
                className="flex-1 px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading || !newCompetitor.trim()}
                className="px-3.5 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-100 disabled:opacity-50 font-semibold shadow-2xs cursor-pointer"
              >
                Add
              </button>
            </form>
          </div>

          {/* Tracked Products & Keywords */}
          <div className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-4">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                Tracked Keywords & Products
              </span>
              <span className="text-[11px] text-slate-400">{brand.keywords?.length || 0} configured</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {brand.keywords?.map((k) => (
                <span
                  key={k.id}
                  className="px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-800 dark:text-indigo-300 rounded-lg border border-indigo-200 dark:border-indigo-800/60 font-medium flex items-center gap-1.5"
                >
                  <Tag className="w-3 h-3 text-indigo-500" />
                  <span>{k.keyword}</span>
                  <span className="text-[10px] text-indigo-400 font-normal">({k.category})</span>
                  <button
                    type="button"
                    onClick={() => handleDeleteKeyword(k)}
                    disabled={loading}
                    aria-label={`Remove ${k.keyword} keyword`}
                    className="ml-0.5 rounded p-0.5 text-indigo-400 hover:bg-rose-100 hover:text-rose-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 disabled:opacity-40 dark:hover:bg-rose-950/60"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>

            <form onSubmit={handleAddKeyword} className="flex gap-2 pt-1">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="Add keyword or product (e.g. Vomero, Air Jordan)..."
                className="flex-1 px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 focus:outline-none"
              />
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="px-2.5 py-1.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 focus:outline-none cursor-pointer"
              >
                <option value="brand">Brand</option>
                <option value="product">Product</option>
                <option value="campaign">Campaign</option>
              </select>
              <button
                type="submit"
                disabled={loading || !newKeyword.trim()}
                className="px-3.5 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-100 disabled:opacity-50 font-semibold shadow-2xs cursor-pointer"
              >
                Add
              </button>
            </form>
          </div>

          {status && (
            <div
              role="status"
              aria-live="polite"
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${
                status.type === 'success'
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300'
                  : 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300'
              }`}
            >
              {status.type === 'success' ? <Check className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
              <span>{status.message}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-100 shadow-2xs cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
