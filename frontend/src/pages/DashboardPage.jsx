import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  RefreshCw,
  Settings,
  Play,
  Calendar,
  Menu,
  AlertTriangle,
  Clock,
  ShieldAlert,
  FileSearch,
} from 'lucide-react';
import { api } from '../services/api';
import Sidebar from '../components/Sidebar';
import KpiCards from '../components/KpiCards';
import ExecutiveSummaryCard from '../components/ExecutiveSummaryCard';
import TrendingTopicsCard from '../components/TrendingTopicsCard';
import ProductRiskInsights from '../components/ProductRiskInsights';
import FilterBar from '../components/FilterBar';
import ChatterTable from '../components/ChatterTable';
import PostDetailsDrawer from '../components/PostDetailsDrawer';
import BrandSettingsModal from '../components/BrandSettingsModal';
import CollectionRunsModal from '../components/CollectionRunsModal';
import AlertsModal from '../components/AlertsModal';
import AuditTrailModal from '../components/AuditTrailModal';

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
  const [intelligence, setIntelligence] = useState({ products: [], risks: [] });
  const [posts, setPosts] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 25, total: 0, pages: 1 });
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const [dateRangeDays, setDateRangeDays] = useState(30);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const [loadingPosts, setLoadingPosts] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingIntelligence, setLoadingIntelligence] = useState(true);
  const [refreshingSummary, setRefreshingSummary] = useState(false);
  const [apiError, setApiError] = useState(null);

  const [selectedPost, setSelectedPost] = useState(null);
  const [showBrandSettings, setShowBrandSettings] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [openAlertCount, setOpenAlertCount] = useState(0);
  const analysisSweepBrandRef = useRef(null);

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

  // 3. Fetch trending topics independently so a partial API response stays usable.
  const fetchTrendingTopics = useCallback(async () => {
    if (!api.getTrendingTopics) return;
    setLoadingTrends(true);
    try {
      const topics = await api.getTrendingTopics(filters.brand_id || 1, dateRangeDays);
      setTrendingTopics(topics || []);
    } catch (err) {
      console.error('Failed to load trending topics:', err);
    } finally {
      setLoadingTrends(false);
    }
  }, [filters.brand_id, dateRangeDays]);

  const fetchIntelligence = useCallback(async () => {
    if (!api.getIntelligenceOverview) return;
    setLoadingIntelligence(true);
    try {
      const overview = await api.getIntelligenceOverview(filters.brand_id || 1, dateRangeDays);
      setIntelligence(overview || { products: [], risks: [] });
    } catch (err) {
      console.error('Failed to load product intelligence:', err);
    } finally {
      setLoadingIntelligence(false);
    }
  }, [filters.brand_id, dateRangeDays]);

  const fetchAlertsCount = useCallback(async () => {
    if (!api.getAlerts) return;
    try {
      const openAlerts = await api.getAlerts(filters.brand_id || 1, 'open');
      setOpenAlertCount((openAlerts || []).length);
    } catch (_) {}
  }, [filters.brand_id]);

  const rebuildIntelligence = useCallback(async () => {
    if (!api.rebuildIntelligence) return;
    setLoadingIntelligence(true);
    setApiError(null);
    try {
      await api.rebuildIntelligence(filters.brand_id || 1);
      await Promise.all([fetchIntelligence(), fetchAlertsCount()]);
    } catch (err) {
      console.error('Failed to analyze existing conversations:', err);
      setApiError('Unable to analyze the existing conversations.');
    } finally {
      setLoadingIntelligence(false);
    }
  }, [filters.brand_id, fetchIntelligence, fetchAlertsCount]);

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
        date_from: new Date(Date.now() - dateRangeDays * 24 * 60 * 60 * 1000).toISOString(),
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
  }, [filters, dateRangeDays]);

  useEffect(() => {
    fetchBrandData();
  }, [fetchBrandData]);

  useEffect(() => {
    fetchDashboardSummary();
    fetchTrendingTopics();
    fetchIntelligence();
    fetchAlertsCount();
  }, [fetchDashboardSummary, fetchTrendingTopics, fetchIntelligence, fetchAlertsCount]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  useEffect(() => {
    if (!posts.length || !api.triggerAnalysis) return;
    const brandId = filters.brand_id || 1;
    const hasUnanalyzedNews = posts.some((post) => !post.analysis?.summary);
    if (!hasUnanalyzedNews || analysisSweepBrandRef.current === brandId) return;
    analysisSweepBrandRef.current = brandId;
    let cancelled = false;
    (async () => {
      try {
        await api.triggerAnalysis(brandId, true, 200);
        if (!cancelled) {
          await Promise.all([fetchPosts(), fetchIntelligence(), fetchDashboardSummary()]);
        }
      } catch (error) {
        console.error('Failed to analyze dashboard conversations:', error);
        if (!cancelled) analysisSweepBrandRef.current = null;
      }
    })();
    return () => { cancelled = true; };
  }, [posts, filters.brand_id, fetchPosts, fetchIntelligence, fetchDashboardSummary]);

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.pages) return;
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleDateRangeChange = (event) => {
    setDateRangeDays(Number(event.target.value));
    setFilters((current) => current.page === 1 ? current : { ...current, page: 1 });
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
    fetchIntelligence();
    fetchAlertsCount();
    fetchPosts();
  };

  const focusConversationTable = () => {
    const tableElem = document.getElementById('main-intelligence-table');
    if (tableElem?.scrollIntoView) tableElem.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Handle Sidebar Navigation selection
  const handleSelectNavView = (viewId) => {
    setCurrentNavView(viewId);
    if (viewId === 'dashboard') {
      handleResetFilters();
    } else if (viewId === 'viral') {
      setFilters((prev) => ({
        ...DEFAULT_FILTERS,
        brand_id: prev.brand_id,
        viral: true,
        sort_by: 'highest_virality',
      }));
      focusConversationTable();
    } else if (viewId === 'conversations') {
      setFilters((prev) => ({ ...DEFAULT_FILTERS, brand_id: prev.brand_id }));
      focusConversationTable();
    } else if (viewId === 'competitors') {
      if (competitorOptions.length) {
        setFilters((prev) => ({ ...DEFAULT_FILTERS, brand_id: prev.brand_id, competitor: 'any' }));
        focusConversationTable();
      }
    } else if (viewId === 'topics') {
      const firstTopic = trendingTopics[0]?.topic;
      if (firstTopic) {
        setFilters((prev) => ({ ...DEFAULT_FILTERS, brand_id: prev.brand_id, topic: firstTopic }));
        focusConversationTable();
      }
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
    <div className="min-h-screen bg-[#f7f8fa] text-slate-900 dark:bg-slate-950 dark:text-slate-100 flex transition-colors">
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
        <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 shadow-[0_1px_0_rgba(15,23,42,0.03)] backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/85">
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
                  <h1 className="text-sm sm:text-base font-bold tracking-[-0.02em] text-slate-950 dark:text-white leading-tight truncate">
                    <span className="sm:hidden">{activeBrand?.name || 'Nike'} Chatter</span>
                    <span className="hidden sm:inline">
                      {activeBrand?.name || 'Nike'} Brand Intelligence
                    </span>
                  </h1>
                </div>
                <p className="hidden sm:block text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate">
                  Live signals, source evidence, and decision-ready guidance.
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
                  onChange={handleDateRangeChange}
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
                  fetchIntelligence();
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
                aria-label="Collect live intelligence"
                title="Collect live intelligence"
                className="flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 p-2 text-xs font-semibold text-indigo-700 transition-colors hover:bg-indigo-100 sm:px-3 sm:py-1.5 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 dark:hover:bg-indigo-900/60"
              >
                <Play className="w-3 h-3 fill-indigo-600 dark:fill-indigo-400" />
                <span className="hidden xl:inline">Collect intelligence</span>
              </button>

              {/* Reputation Risk Alerts Action */}
              <button
                type="button"
                onClick={() => setShowAlertsModal(true)}
                aria-label="Reputation Risk Alerts"
                title="Reputation Risk Alerts"
                className="relative flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium transition-colors cursor-pointer"
              >
                <ShieldAlert className={`w-3.5 h-3.5 ${openAlertCount > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-500 dark:text-slate-400'}`} />
                <span className="hidden xl:inline">Alerts</span>
                {openAlertCount > 0 && (
                  <span className="inline-flex items-center justify-center px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-rose-600 text-white">
                    {openAlertCount}
                  </span>
                )}
              </button>

              {/* Brand Settings Action */}
              <button
                type="button"
                onClick={() => setShowAuditModal(true)}
                aria-label="Source and AI Audit Trail"
                title="Source and AI Audit Trail"
                className="flex items-center gap-1.5 p-2 sm:px-3 sm:py-1.5 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium transition-colors"
              >
                <FileSearch className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                <span className="hidden xl:inline">Audit</span>
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
        <main
          aria-label={`${activeBrand?.name || 'Nike'} intelligence command center`}
          className="max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 pt-5"
        >
          <section className="mb-5 flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white/80 px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] sm:flex-row sm:items-center sm:justify-between sm:px-5 dark:border-slate-800 dark:bg-slate-900/65">
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-indigo-600 dark:text-indigo-300">Brand intelligence workspace</p>
              <h2 className="mt-1 text-lg font-semibold tracking-[-0.025em] text-slate-950 dark:text-white">See the signal. Decide the next move.</h2>
              <p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-400">A focused view of conversation, momentum, product risk, and AI-recommended actions for {activeBrand?.name || 'your brand'}.</p>
            </div>
            <a href="#main-intelligence-table" className="inline-flex shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/60 dark:hover:text-indigo-200 dark:focus-visible:ring-offset-slate-950">
              Review live posts
            </a>
          </section>
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
                windowDays={dateRangeDays}
              />
            </div>
          </div>

          <ProductRiskInsights
            brandId={filters.brand_id || 1}
            products={intelligence.products}
            risks={intelligence.risks}
            praises={intelligence.praises}
            competitors={intelligence.competitors}
            loading={loadingIntelligence}
            onSelectProduct={(product) => {
              setFilters((prev) => ({ ...prev, product, page: 1 }));
              focusConversationTable();
            }}
            onSelectCompetitor={(comp) => {
              setFilters((prev) => ({ ...prev, competitor: comp, page: 1 }));
              focusConversationTable();
            }}
            onOpenAlerts={() => setShowAlertsModal(true)}
            onRebuild={rebuildIntelligence}
          />

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
        <PostDetailsDrawer
          post={selectedPost}
          onClose={() => setSelectedPost(null)}
          onPostUpdated={(updatedPost) => {
            setSelectedPost(updatedPost);
            setPosts((current) => current.map((item) => item.id === updatedPost.id ? updatedPost : item));
          }}
        />
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
          brandId={filters.brand_id}
          onClose={() => setShowCollectionModal(false)}
          onCollectionComplete={() => {
            fetchPosts();
            fetchDashboardSummary(true);
            fetchTrendingTopics();
            fetchIntelligence();
            fetchAlertsCount();
          }}
        />
      )}

      <AlertsModal
        isOpen={showAlertsModal}
        onClose={() => setShowAlertsModal(false)}
        brandId={filters.brand_id || 1}
        onAlertStatusChanged={fetchAlertsCount}
      />
      <AuditTrailModal
        isOpen={showAuditModal}
        onClose={() => setShowAuditModal(false)}
        brandId={filters.brand_id || 1}
      />
    </div>
  );
}
