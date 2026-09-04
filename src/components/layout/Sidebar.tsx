import { useState } from 'react';
import {
  BarChart3,
  Bot,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
} from 'lucide-react';

import { useAuth } from '@/context/AuthContext';


export type PageKey =
  | 'dashboard'
  | 'payments'
  | 'customers'
  | 'recovery'
  | 'analytics'
  | 'assistant'
  | 'settings';


interface SidebarProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}


const navItems: {
  key: PageKey;
  label: string;
  icon: typeof LayoutDashboard;
  badge?: string;
}[] = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
  },
  {
    key: 'payments',
    label: 'Payments',
    icon: CreditCard,
    badge: '12',
  },
  {
    key: 'customers',
    label: 'Customers',
    icon: Users,
  },
  {
    key: 'recovery',
    label: 'Recovery Center',
    icon: ShieldCheck,
    badge: '5',
  },
  {
    key: 'analytics',
    label: 'Analytics',
    icon: BarChart3,
  },
];


const bottomItems: {
  key: PageKey;
  label: string;
  icon: typeof Settings;
}[] = [
  {
    key: 'assistant',
    label: 'AI Assistant',
    icon: Bot,
  },
  {
    key: 'settings',
    label: 'Settings',
    icon: Settings,
  },
];


export function Sidebar({
  activePage,
  onNavigate,
}: SidebarProps) {
  const [collapsed, setCollapsed] =
    useState(false);

  const { logout } = useAuth();


  const handleLogout = () => {
    logout();
  };


  return (
    <aside
      className={`hidden lg:flex fixed left-0 top-0 bottom-0 z-30 flex-col bg-white border-r border-slate-200 transition-all ${
        collapsed
          ? 'w-20'
          : 'w-64'
      }`}
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        className={`h-16 flex items-center border-b border-slate-100 ${
          collapsed
            ? 'justify-center'
            : 'px-6'
        }`}
      >
        <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center shrink-0">
          <Sparkles className="h-4 w-4 text-white" />
        </div>

        {!collapsed && (
          <span className="ml-2 font-bold text-lg tracking-tight text-slate-800">
            Recover
            <span className="text-brand-600">
              AI
            </span>
          </span>
        )}
      </div>


      {/* =====================================================
          NAVIGATION
      ===================================================== */}

      <div className="flex-1 px-3 py-6 flex flex-col">

        <p
          className={`text-[10px] font-semibold tracking-wider text-slate-400 uppercase mb-3 ${
            collapsed
              ? 'text-center'
              : 'px-3'
          }`}
        >
          {collapsed
            ? '•'
            : 'Workspace'}
        </p>


        <nav className="space-y-1">

          {navItems.map(
            ({
              key,
              label,
              icon: Icon,
              badge,
            }) => (
              <button
                key={key}
                type="button"
                onClick={() =>
                  onNavigate(key)
                }
                title={
                  collapsed
                    ? label
                    : undefined
                }
                className={`w-full flex items-center rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  collapsed
                    ? 'justify-center'
                    : 'gap-3'
                } ${
                  activePage === key
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                <Icon
                  className={`h-[18px] w-[18px] shrink-0 ${
                    activePage === key
                      ? 'text-brand-600'
                      : 'text-slate-400'
                  }`}
                />

                {!collapsed && (
                  <>
                    <span className="flex-1 text-left">
                      {label}
                    </span>

                    {badge && (
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                          activePage === key
                            ? 'bg-brand-100 text-brand-700'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        {badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            ),
          )}

        </nav>


        {/* ===================================================
            MANAGE
        =================================================== */}

        <p
          className={`text-[10px] font-semibold tracking-wider text-slate-400 uppercase mt-8 mb-3 ${
            collapsed
              ? 'text-center'
              : 'px-3'
          }`}
        >
          {collapsed
            ? '•'
            : 'Manage'}
        </p>


        <nav className="space-y-1">

          {bottomItems.map(
            ({
              key,
              label,
              icon: Icon,
            }) => (
              <button
                key={key}
                type="button"
                onClick={() =>
                  onNavigate(key)
                }
                title={
                  collapsed
                    ? label
                    : undefined
                }
                className={`w-full flex items-center rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  collapsed
                    ? 'justify-center'
                    : 'gap-3'
                } ${
                  activePage === key
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                <Icon
                  className={`h-[18px] w-[18px] shrink-0 ${
                    activePage === key
                      ? 'text-brand-600'
                      : 'text-slate-400'
                  }`}
                />

                {!collapsed && (
                  <span className="flex-1 text-left">
                    {label}
                  </span>
                )}
              </button>
            ),
          )}

        </nav>

      </div>


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <div className="p-3 border-t border-slate-100">

        {!collapsed && (
          <div className="rounded-lg bg-slate-50 p-3">

            <div className="flex items-center gap-2 mb-2">
              <CircleDollarSign className="h-4 w-4 text-brand-600" />

              <span className="text-xs font-semibold text-slate-700">
                Recovery this month
              </span>
            </div>

            <p className="text-lg font-bold text-slate-800">
              ₹6.12L
            </p>

            <p className="text-[10px] text-success-600 mt-0.5">
              ↑ 18.4% from last month
            </p>

          </div>
        )}


        {/* ===================================================
            COLLAPSE BUTTON
        =================================================== */}

        <button
          type="button"
          onClick={() =>
            setCollapsed(
              !collapsed,
            )
          }
          className="mt-2 w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs text-slate-500 hover:bg-slate-100"
          title={
            collapsed
              ? 'Expand sidebar'
              : 'Collapse sidebar'
          }
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              Collapse
            </>
          )}
        </button>


        {/* ===================================================
            SIGN OUT
        =================================================== */}

        {!collapsed && (
          <button
            type="button"
            onClick={handleLogout}
            className="w-full mt-1 flex items-center gap-3 px-3 py-2.5 text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
          >
            <LogOut className="h-[18px] w-[18px]" />

            <span>
              Sign out
            </span>
          </button>
        )}

      </div>

    </aside>
  );
}