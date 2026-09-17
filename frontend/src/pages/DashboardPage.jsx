import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  RefreshCw,
  Settings,
  Play,
  Calendar,
  Menu,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import Sidebar from '../components/Sidebar';
import KpiCards from '../components/KpiCards';
import ExecutiveSummaryCard from '../components/ExecutiveSummaryCard';
import TrendingTopicsCard from '../components/TrendingTopicsCard';
import FilterBar from '../components/FilterBar';
import ChatterTable from '../components/ChatterTable';
import PostDetailsDrawer from '../components/PostDetailsDrawer';
import BrandSettingsModal from '../components/BrandSettingsModal';
import CollectionRunsModal from '../components/CollectionRunsModal';

const DEFAULT_FILTERS = {
  brand_id: 1,
  source: 'all',
  sentiment: 'all',
  topic: 'all',
  product: 'all',
  competitor: 'all',
  virality_level: 'all',
  viral: false,
  search: '',
  sort_by: 'newest',
  page: 1,
  page_size: 25,
};

export default function DashboardPage() {
  const [brands, setBrands] = useState([]);
  const [activeBrand, setActiveBrand] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [trendingTopics, setTrendingTopics] = useState([]);
  const [posts, setPosts] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 25, total: 0, pages: 1 });
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const [dateRangeDays, setDateRangeDays] = useState(30);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const [loadingPosts, setLoadingPosts] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [refreshingSummary, setRefreshingSummary] = useState(false);
  const [apiError, setApiError] = useState(null);

  const [selectedPost, setSelectedPost] = useState(null);
  const [showBrandSettings, setShowBrandSettings] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);

  // Sidebar & Layout states
  const [currentNavView, setCurrentNavView] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Dark Mode State with Safe LocalStorage & OS Preference
  const [darkMode, setDarkMode] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const saved = window.localStorage.getItem('bc_theme');
        if (saved) return saved === 'dark';
        return !!window.matchMedia?.('(prefers-color-scheme: dark)')?.matches;
      }
    } catch (_) {}
    return false;
  });

  useEffect(() => {
    try {
      if (darkMode) {
        document.documentElement.classList.add('dark');
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem('bc_theme', 'dark');
        }
      } else {
        document.documentElement.classList.remove('dark');
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem('bc_theme', 'light');
        }
      }
    } catch (_) {}
  }, [darkMode]);

  // 1. Fetch Brands and Active Brand details
  const fetchBrandData = useCallback(async () => {
    try {
      const allBrands = await api.getBrands();
      setBrands(allBrands || []);
      const currentId = filters.brand_id || (allBrands && allBrands[0] ? allBrands[0].id : 1);
      const detail = await api.getBrand(currentId);
      setActiveBrand(detail);
    } catch (err) {
      console.error('Failed to load brands:', err);
      setApiError('Unable to connect to backend server. Please verify the API is running.');
    }
  }, [filters.brand_id]);

  // 2. Fetch Dashboard KPIs & Executive AI Summary
  const fetchDashboardSummary = useCallback(async (forceRefresh = false) => {
    if (forceRefresh) setRefreshingSummary(true);
    else setLoadingSummary(true);
    try {
      const data = await api.getDashboardSummary(filters.brand_id || 1, dateRangeDays, forceRefresh);
      setSummaryData(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load dashboard summary:', err);
      setApiError('Unable to load dashboard summary metrics.');
    } finally {
      setLoadingSummary(false);
      setRefreshingSummary(false);
    }
  }, [filters.brand_id, dateRangeDays]);

  // 3. Fetch Trending Topics (guarded in case mock doesn't include it)
  const fetchTrendingTopics = useCallback(async () => {
    if (!api.getTrendingTopics) return;
    setLoadingTrends(true);
    try {
      const topics = await api.getTrendingTopics(filters.brand_id || 1, 7);
      setTrendingTopics(topics || []);
    } catch (err) {
      console.error('Failed to load trending topics:', err);
    } finally {
      setLoadingTrends(false);
    }
  }, [filters.brand_id]);

  // 4. Fetch Posts with server-side pagination and filters
  const fetchPosts = useCallback(async () => {
    setLoadingPosts(true);
    try {
      const resp = await api.getPosts({
        brand_id: filters.brand_id,
        source: filters.source !== 'all' ? filters.source : undefined,
        sentiment: filters.sentiment !== 'all' ? filters.sentiment : undefined,
        topic: filters.topic !== 'all' ? filters.topic : undefined,
        product: filters.product !== 'all' ? filters.product : undefined,
        competitor: filters.competitor !== 'all' ? filters.competitor : undefined,
        virality_level: filters.virality_level !== 'all' ? filters.virality_level : undefined,
        viral: filters.viral ? true : undefined,
        search: filters.search || undefined,
        sort_by: filters.sort_by,
        page: filters.page,
        page_size: filters.page_size,
      });

      setPosts(resp.items);
      setPagination({
        page: resp.page,
        page_size: resp.page_size,
        total: resp.total,
        pages: resp.pages,
      });
    } catch (err) {
      console.error('Failed to load posts:', err);
      setApiError('Unable to fetch chatter posts from the server.');
    } finally {
      setLoadingPosts(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchBrandData();
  }, [fetchBrandData]);

  useEffect(() => {
    fetchDashboardSummary();
    fetchTrendingTopics();
  }, [fetchDashboardSummary, fetchTrendingTopics]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.pages) return;
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleResetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS, brand_id: filters.brand_id });
    setCurrentNavView('dashboard');
  };

  const handleRetry = () => {
    setApiError(null);
    fetchBrandData();
    fetchDashboardSummary();
    fetchTrendingTopics();
    fetchPosts();
  };

  // Handle Sidebar Navigation selection
  const handleSelectNavView = (viewId) => {
    setCurrentNavView(viewId);
    if (viewId === 'dashboard') {
      handleResetFilters();
    } else if (viewId === 'viral') {
      setFilters((prev) => ({ ...prev, viral: true, page: 1 }));
    } else if (viewId === 'conversations') {
      // Clear quick filter overrides and focus on table
      setFilters((prev) => ({ ...prev, viral: false, sentiment: 'all', page: 1 }));
      const tableElem = document.getElementById('main-intelligence-table');
      if (tableElem) tableElem.scrollIntoView({ behavior: 'smooth' });
    } else if (viewId === 'competitors') {
      const comp = competitorOptions[0];
      if (comp) setFilters((prev) => ({ ...prev, competitor: comp, page: 1 }));
    } else if (viewId === 'topics') {
      const firstTopic = trendingTopics[0]?.topic;
      if (firstTopic) setFilters((prev) => ({ ...prev, topic: firstTopic, page: 1 }));
    } else if (viewId === 'settings') {
      setShowBrandSettings(true);
    }
  };

  // Derive products & competitors lists for the filter dropdowns
  const productOptions = useMemo(() => {
    return activeBrand?.keywords
      ?.filter((k) => k.category === 'product')
      .map((k) => k.keyword) || [];
  }, [activeBrand]);

  const competitorOptions = useMemo(() => {
    return activeBrand?.competitors?.map((c) => c.name) || [];
  }, [activeBrand]);

  // Relative time helper for header
  const getRelativeTime = () => {
    const diffMins = Math.round((new Date() - lastUpdated) / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins === 1) return '1 minute ago';
    return `${diffMins} minutes ago`;
  };

  return (
    <div className="min-h-screen bg-[#f7f8fa] dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex transition-colors">
      {/* 1. Collapsible Sidebar */}
      <Sidebar
        currentView={currentNavView}
        onSelectView={handleSelectNavView}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        viralCount={summaryData?.kpis?.viral_posts_count || 0}
        activeBrand={activeBrand}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* 2. Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-16">
        {/* Top Header */}
        <header className="bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800 sticky top-0 z-20">
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 min-h-[68px] py-2.5 flex items-center justify-between gap-3">
            {/* Left: Mobile Menu + Brand Context */}
            <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
              <button
                type="button"
                onClick={() => setIsMobileSidebarOpen(true)}
                className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white lg:hidden"
                aria-label="Open mobile menu"
              >
                <Menu className="w-5 h-5" />
              </button>

              <div className="w-9 h-9 shrink-0 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center font-bold text-base shadow-xs">
                {activeBrand?.name ? activeBrand.name.charAt(0) : 'B'}
              </div>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white tracking-tight leading-tight truncate">
                    <span className="sm:hidden">{activeBrand?.name || 'Nike'} Chatter</span>
                    <span className="hidden sm:inline">
                      {activeBrand?.name || 'Nike'} Brand Intelligence
                    </span>
                  </h1>
                </div>
                <p className="hidden sm:block text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate">
                  Understand what customers are saying across the web.
                </p>
              </div>
            </div>

            {/* Right: Date Range + Refresh + Action Buttons */}
            <div className="flex shrink-0 items-center gap-2">
              {/* Date Range Selector */}
              {brands.length > 1 && <select
                aria-label="Selected brand"
                value={filters.brand_id}
                onChange={(event) => setFilters((current) => ({ ...current, brand_id: Number(event.target.value), page: 1 }))}
                className="hidden lg:block h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              >
                {brands.map((brand) => <option key={brand.id} value={brand.id}>{brand.name}</option>)}
              </select>}

              <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <label className="sr-only" htmlFor="analysis-window">Analysis window</label>
                <select
                  id="analysis-window"
                  value={dateRangeDays}
                  onChange={(e) => setDateRangeDays(Number(e.target.value))}
                  className="bg-transparent text-slate-700 dark:text-slate-300 font-medium focus:outline-none cursor-pointer"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
              </div>

              {/* Relative Last Updated Time & Refresh Button */}
              <div className="hidden xl:flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 mr-1">
                <Clock className="w-3 h-3" />
                <span>Last updated {getRelativeTime()}</span>
              </div>

              <button
                type="button"
                onClick={() => {
                  fetchDashboardSummary(true);
                  fetchTrendingTopics();
                  fetchPosts();
                }}
                disabled={refreshingSummary || loadingPosts}
                aria-label="Refresh Dashboard Data"
                title="Refresh latest brand chatter"
                className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshingSummary || loadingPosts ? 'animate-spin' : ''}`} />
              </button>

              {/* Quick Collect Action */}
              <button
                type="button"
                onClick={() => setShowCollectionModal(true)}
                aria-label="Collect Chatter"
                title="Collect Chatter"
                className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800 rounded-lg text-xs font-semibold transition-colors"
              >
                <Play className="w-3 h-3 fill-indigo-600 dark:fill-indigo-400" />
                <span className="hidden xl:inline">Collect Chatter</span>
              </button>

              {/* Brand Settings Action */}
              <button
                type="button"
                onClick={() => setShowBrandSettings(true)}
                aria-label="Configure Brand"
                title="Configure Brand"
                className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium transition-colors"
              >
                <Settings className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden xl:inline">Configure Brand</span>
              </button>
            </div>
          </div>
        </header>

        {/* Main Body */}
        <main className="max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 pt-5">
          {/* API Error Alert Banner */}
          {apiError && (
            <div
              role="alert"
              data-testid="api-error-banner"
              className="mb-6 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-center justify-between shadow-2xs transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-rose-100 dark:bg-rose-900/60 flex items-center justify-center shrink-0">
                  <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-rose-900 dark:text-rose-200">Unable to load the latest conversations</h4>
                  <p className="text-xs text-rose-700 dark:text-rose-300">{apiError} Please try again.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRetry}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* Compact KPI Cards Row */}
          <KpiCards kpis={summaryData?.kpis} loading={loadingSummary} />

          {/* AI Executive Brand Pulse & Trending Topics (Dual High-Signal Section) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            <div className="lg:col-span-2">
              <ExecutiveSummaryCard
                summary={summaryData?.executive_summary}
                onRefresh={() => fetchDashboardSummary(true)}
                refreshing={refreshingSummary}
                loading={loadingSummary}
              />
            </div>
            <div className="lg:col-span-1">
              <TrendingTopicsCard
                topics={trendingTopics}
                loading={loadingTrends}
                onSelectTopic={(topic) => setFilters((prev) => ({ ...prev, topic, page: 1 }))}
                competitors={competitorOptions}
                onSelectCompetitor={(comp) => setFilters((prev) => ({ ...prev, competitor: comp, page: 1 }))}
                activeTopic={filters.topic}
                activeCompetitor={filters.competitor}
              />
            </div>
          </div>

          {/* Search and Filters Bar */}
          <FilterBar
            filters={filters}
            onChange={setFilters}
            onReset={handleResetFilters}
            brands={brands}
            competitors={competitorOptions}
            products={productOptions}
            topics={trendingTopics.map((item) => item.topic).filter(Boolean)}
          />

          {/* Core Hero Intelligence Table */}
          <div id="main-intelligence-table">
            <ChatterTable
              posts={posts}
              brandName={activeBrand?.name || 'Nike'}
              loading={loadingPosts}
              pagination={pagination}
              onPageChange={handlePageChange}
              onSelectPost={(post) => setSelectedPost(post)}
              onResetFilters={handleResetFilters}
            />
          </div>
        </main>
      </div>

      {/* Drawers and Modals */}
      {selectedPost && (
        <PostDetailsDrawer post={selectedPost} onClose={() => setSelectedPost(null)} />
      )}

      {showBrandSettings && (
        <BrandSettingsModal
          brand={activeBrand}
          onClose={() => setShowBrandSettings(false)}
          onRefresh={fetchBrandData}
        />
      )}

      {showCollectionModal && (
        <CollectionRunsModal
          onClose={() => setShowCollectionModal(false)}
          onCollectionComplete={() => {
            fetchPosts();
            fetchDashboardSummary(true);
            fetchTrendingTopics();
          }}
        />
      )}
    </div>
  );
}
