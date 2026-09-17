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
  CircleCheck
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
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Brand health & intelligence overview',
    },
    {
      id: 'conversations',
      label: 'Conversations',
      icon: MessagesSquare,
      description: 'All social chatter & threads',
    },
    {
      id: 'viral',
      label: 'Viral Posts',
      icon: Flame,
      badge: viralCount > 0 ? viralCount : null,
      badgeColor: 'bg-purple-100 text-purple-700 dark:bg-purple-900/60 dark:text-purple-300',
      description: 'High velocity discussions',
    },
    {
      id: 'competitors',
      label: 'Competitors',
      icon: Swords,
      description: 'Rival mentions & benchmarks',
    },
    {
      id: 'topics',
      label: 'Topics',
      icon: TrendingUp,
      description: 'Trending themes & shifts',
    },
    {
      id: 'settings',
      label: 'Brand Settings',
      icon: Settings,
      description: 'Keywords & competitor config',
    },
  ];

  const handleNavClick = (id) => {
    if (onSelectView) onSelectView(id);
    if (isMobileOpen && onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <aside
      className={`h-full flex flex-col justify-between bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 transition-all duration-200 select-none ${
        isCollapsed ? 'w-[68px]' : 'w-[240px]'
      }`}
    >
      {/* Top Section: Logo & Brand Context */}
      <div>
        <div className={`flex items-center h-16 border-b border-slate-100 dark:border-slate-800/80 px-4 ${
          isCollapsed ? 'justify-center' : 'justify-between'
        }`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-slate-900 text-white dark:bg-white dark:text-slate-900 flex items-center justify-center font-bold text-sm shrink-0 shadow-xs">
              BC
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-1.5">
                  Brand Chatter
                </div>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                  {activeBrand?.name ? `${activeBrand.name} Intelligence` : 'Social Listening'}
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
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                title={isCollapsed ? item.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all relative ${
                  isCollapsed ? 'justify-center px-0' : ''
                } ${
                  isActive
                    ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive
                      ? 'text-white dark:text-slate-950'
                      : 'text-slate-400 dark:text-slate-500'
                  }`}
                />
                {!isCollapsed && (
                  <span className="flex-1 text-left truncate">{item.label}</span>
                )}
                {!isCollapsed && item.badge && (
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full shrink-0 ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
                {isCollapsed && item.badge && (
                  <span className="absolute top-1.5 right-2 w-2 h-2 rounded-full bg-purple-500" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section: verified workspace context, theme, collapse */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
        {!isCollapsed ? (
          <div className="flex items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-[11px] dark:border-slate-800 dark:bg-slate-900/50">
            <CircleCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            <div className="min-w-0">
              <div className="truncate font-medium text-slate-700 dark:text-slate-200">{activeBrand?.name || 'Brand'} workspace</div>
              <div className="text-[10px] text-slate-400 dark:text-slate-500">Data connected</div>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-1" title={`${activeBrand?.name || 'Brand'} data connected`}>
            <CircleCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
        )}

        {/* Theme and Collapse Controls */}
        <div className={`flex items-center gap-1 ${isCollapsed ? 'flex-col' : 'justify-between'}`}>
          <button
            type="button"
            onClick={onToggleDarkMode}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            className="p-1.5 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Desktop collapse toggle */}
          <button
            type="button"
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="hidden lg:flex p-1.5 text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors"
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
            className="fixed inset-y-0 left-0 w-[240px] z-50 animate-in slide-in-from-left duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
