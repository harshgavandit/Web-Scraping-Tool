import React from 'react';
import {
  LayoutDashboard,
  MessagesSquare,
  Flame,
  Swords,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  X,
  Radio,
  Sparkles,
} from 'lucide-react';

export default function Sidebar({
  currentView = 'dashboard',
  onSelectView,
  isCollapsed = false,
  onToggleCollapse,
  viralCount = 0,
  activeBrand = null,
  darkMode = false,
  onToggleDarkMode,
  isMobileOpen = false,
  onCloseMobile,
}) {
  const mainNav = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Brand health overview',
    },
    {
      id: 'conversations',
      label: 'Conversations',
      icon: MessagesSquare,
      description: 'Indexed public chatter',
    },
    {
      id: 'viral',
      label: 'High Attention',
      icon: Flame,
      badge: viralCount > 0 ? viralCount : null,
      badgeColor: 'bg-violet-100 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300',
      description: 'Fast-moving discussions',
    },
  ];

  const intelligenceNav = [
    {
      id: 'competitors',
      label: 'Competitors',
      icon: Swords,
      description: 'Head-to-head benchmarking',
    },
    {
      id: 'topics',
      label: 'Topics',
      icon: TrendingUp,
      description: 'Emerging consumer themes',
    },
  ];

  const settingsNav = [
    {
      id: 'settings',
      label: 'Brand Settings',
      icon: Settings,
      description: 'Aliases & competitors',
    },
  ];

  const handleNavClick = (id) => {
    if (onSelectView) onSelectView(id);
    if (isMobileOpen && onCloseMobile) onCloseMobile();
  };

  const renderNavGroup = (items, groupTitle) => (
    <div className="space-y-0.5">
      {!isCollapsed && groupTitle && (
        <div className="px-3 pt-3 pb-1 text-[10px] font-bold uppercase tracking-[0.08em] text-slate-400 dark:text-slate-500">
          {groupTitle}
        </div>
      )}
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = currentView === item.id;
        return (
          <button
            type="button"
            key={item.id}
            onClick={() => handleNavClick(item.id)}
            aria-current={isActive ? 'page' : undefined}
            title={isCollapsed ? item.label : undefined}
            className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all relative group cursor-pointer ${
              isCollapsed ? 'justify-center px-0' : ''
            } ${
              isActive
                ? 'bg-gradient-to-r from-slate-950 to-slate-800 text-white shadow-[0_6px_16px_rgba(15,23,42,0.18)] dark:from-indigo-600 dark:to-violet-600 dark:text-white'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-900/80 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            <Icon
              className={`w-4 h-4 shrink-0 transition-colors ${
                isActive
                  ? 'text-indigo-100 dark:text-white'
                  : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300'
              }`}
            />
            {!isCollapsed && (
              <span className="flex-1 text-left truncate tracking-tight">{item.label}</span>
            )}
            {!isCollapsed && item.badge && (
              <span
                className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full shrink-0 ${item.badgeColor}`}
              >
                {item.badge}
              </span>
            )}
            {isCollapsed && item.badge && (
              <span className="absolute top-1 right-1.5 w-2 h-2 rounded-full bg-violet-500 ring-2 ring-white dark:ring-slate-950" />
            )}
          </button>
        );
      })}
    </div>
  );

  const sidebarContent = (
    <aside
      className={`h-full flex flex-col justify-between border-r border-slate-200/80 bg-white/90 backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/90 transition-all duration-200 select-none ${
        isCollapsed ? 'w-[68px]' : 'w-[248px]'
      }`}
    >
      {/* Top Section: Logo & Brand Context */}
      <div>
        <div
          className={`flex items-center h-16 border-b border-slate-100 dark:border-slate-800/80 px-3.5 ${
            isCollapsed ? 'justify-center' : 'justify-between'
          }`}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-slate-950 to-indigo-800 text-white shadow-[0_8px_16px_rgba(49,46,129,0.24)] ring-1 ring-black/5 dark:from-indigo-500 dark:to-violet-600 dark:ring-white/10">
              <Sparkles className="h-4 w-4 text-indigo-100" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-1.5">
                  Brand Intelligence
                </div>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate font-medium">
                  {activeBrand?.name ? `${activeBrand.name} workspace` : 'Live listening workspace'}
                </p>
              </div>
            )}
          </div>

          {/* Close button for mobile drawer */}
          {isMobileOpen && (
            <button
              type="button"
              onClick={onCloseMobile}
              aria-label="Close navigation"
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 lg:hidden cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="p-2.5 space-y-1">
          {renderNavGroup(mainNav, 'Overview')}
          {renderNavGroup(intelligenceNav, 'Intelligence')}
          {renderNavGroup(settingsNav, 'Management')}
        </nav>
      </div>

      {/* Bottom Section: Live Listening Status, Theme & Collapse */}
      <div className="p-2.5 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
        {!isCollapsed ? (
          <div className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/70 px-2.5 py-1.5 text-[11px] dark:border-slate-800 dark:bg-slate-900/50">
            <div className="flex items-center gap-2 min-w-0">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="truncate font-medium text-slate-700 dark:text-slate-300">
                Live sources
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-medium">Live</span>
          </div>
        ) : (
          <div className="flex justify-center py-1" title="Live source listening">
            <Radio className="h-3.5 w-3.5 text-emerald-500 animate-pulse" />
          </div>
        )}

        {/* Theme and Collapse Controls */}
        <div className={`flex items-center gap-1 ${isCollapsed ? 'flex-col' : 'justify-between'}`}>
          <button
            type="button"
            onClick={onToggleDarkMode}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            className="p-1.5 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors cursor-pointer"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Desktop collapse toggle */}
          <button
            type="button"
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="hidden lg:flex p-1.5 text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors cursor-pointer"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <div className="hidden lg:block sticky top-0 h-screen z-30 shrink-0">
        {sidebarContent}
      </div>

      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs lg:hidden"
          onClick={onCloseMobile}
        >
          <div
            className="fixed inset-y-0 left-0 w-[248px] z-50 animate-in slide-in-from-left duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
