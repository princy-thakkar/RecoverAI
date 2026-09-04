import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  Bell,
  ChevronDown,
  Menu,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

import { Sidebar, type PageKey } from '@/components/layout/Sidebar';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import {
  getCustomers,
  getPayments,
  getRecoveryCases,
} from '@/services/api';
import type {
  Customer,
  Payment,
  RecoveryCase,
} from '@/types';

interface AppShellProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
  onOpenPayment?: (paymentId: string) => void;
  children: ReactNode;
}

type SearchResult = {
  id: string;
  title: string;
  subtitle: string;
  type: 'page' | 'payment' | 'customer' | 'recovery';
  page?: PageKey;
  paymentId?: string;
};

const pageResults: SearchResult[] = [
  { id: 'page-dashboard', title: 'Dashboard', subtitle: 'Overview and revenue recovery', type: 'page', page: 'dashboard' },
  { id: 'page-payments', title: 'Payments', subtitle: 'Transactions and payment status', type: 'page', page: 'payments' },
  { id: 'page-customers', title: 'Customers', subtitle: 'Customer payment history', type: 'page', page: 'customers' },
  { id: 'page-recovery', title: 'Recovery Center', subtitle: 'Recovery cases and actions', type: 'page', page: 'recovery' },
  { id: 'page-analytics', title: 'Analytics', subtitle: 'Recovery performance and benchmark', type: 'page', page: 'analytics' },
  { id: 'page-assistant', title: 'AI Assistant', subtitle: 'Ask RecoverAI about your payments', type: 'page', page: 'assistant' },
  { id: 'page-settings', title: 'Settings', subtitle: 'Merchant and recovery preferences', type: 'page', page: 'settings' },
];

export function AppShell({
  activePage,
  onNavigate,
  onOpenPayment,
  children,
}: AppShellProps) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [payments, setPayments] = useState<Payment[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [recoveryCases, setRecoveryCases] = useState<RecoveryCase[]>([]);

  const profileRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const displayName =
    user?.name?.trim() ||
    user?.email?.split('@')[0] ||
    'Merchant';

  const role = user?.role?.trim() || 'Merchant';
  const initials = getInitials(displayName);

  const formattedDate = new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target as Node)
      ) {
        setProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }

      if (event.key === 'Escape') {
        setSearchOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (!searchOpen) {
      return;
    }

    const timer = window.setTimeout(() => {
      searchInputRef.current?.focus();
    }, 20);

    return () => window.clearTimeout(timer);
  }, [searchOpen]);

  useEffect(() => {
    if (!searchOpen || (payments.length > 0 && customers.length > 0)) {
      return;
    }

    let cancelled = false;

    const loadSearchData = async () => {
      setSearchLoading(true);
      setSearchError('');

      const [paymentsResult, customersResult, recoveryResult] =
        await Promise.allSettled([
          getPayments(),
          getCustomers(),
          getRecoveryCases(),
        ]);

      if (cancelled) {
        return;
      }

      const errors: string[] = [];

      if (paymentsResult.status === 'fulfilled') {
        setPayments(paymentsResult.value);
      } else {
        errors.push('payments');
      }

      if (customersResult.status === 'fulfilled') {
        setCustomers(customersResult.value);
      } else {
        errors.push('customers');
      }

      if (recoveryResult.status === 'fulfilled') {
        setRecoveryCases(recoveryResult.value);
      } else {
        errors.push('recovery cases');
      }

      if (errors.length === 3) {
        setSearchError('Unable to load search data. Please try again.');
      } else if (errors.length > 0) {
        setSearchError(`Some search data could not be loaded: ${errors.join(', ')}.`);
      }

      setSearchLoading(false);
    };

    void loadSearchData();

    return () => {
      cancelled = true;
    };
  }, [searchOpen, payments.length, customers.length]);

  const handleNavigate = (page: PageKey) => {
    setMobileMenuOpen(false);
    setProfileOpen(false);
    setSearchOpen(false);
    setSearchQuery('');
    onNavigate(page);
  };

  const handleLogout = () => {
    setProfileOpen(false);
    setMobileMenuOpen(false);
    setSearchOpen(false);
    logout();
  };

  const results = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) {
      return pageResults;
    }

    const matches = (value: unknown) =>
      String(value ?? '').toLowerCase().includes(query);

    const pageMatches = pageResults.filter(
      (item) => matches(item.title) || matches(item.subtitle),
    );

    const paymentMatches: SearchResult[] = payments
      .filter((payment) =>
        [
          payment.id,
          payment.customerName,
          payment.customerEmail,
          payment.status,
          payment.failureReason,
          payment.paymentMethod,
          payment.amount,
          payment.recommendedAction,
        ].some(matches),
      )
      .slice(0, 6)
      .map((payment) => ({
        id: `payment-${payment.id}`,
        title: payment.customerName || 'Payment',
        subtitle: `${formatSearchAmount(payment.amount)} · ${payment.status}${payment.failureReason ? ` · ${payment.failureReason}` : ''}`,
        type: 'payment',
        paymentId: payment.id,
      }));

    const customerMatches: SearchResult[] = customers
      .filter((customer) =>
        [
          customer.id,
          customer.name,
          customer.email,
          customer.phone,
          customer.riskProfile,
        ].some(matches),
      )
      .slice(0, 5)
      .map((customer) => ({
        id: `customer-${customer.id}`,
        title: customer.name,
        subtitle: `${customer.email} · ${customer.totalPayments} payments`,
        type: 'customer',
        page: 'customers',
      }));

    const recoveryMatches: SearchResult[] = recoveryCases
      .filter((item) =>
        [
          item.id,
          item.paymentId,
          item.customerName,
          item.failureReason,
          item.status,
          item.recommendedAction,
          item.amountAtRisk,
        ].some(matches),
      )
      .slice(0, 5)
      .map((item) => ({
        id: `recovery-${item.id}`,
        title: item.customerName,
        subtitle: `${formatSearchAmount(item.amountAtRisk)} at risk · ${item.status}`,
        type: 'recovery',
        page: 'recovery',
      }));

    return [
      ...pageMatches,
      ...paymentMatches,
      ...customerMatches,
      ...recoveryMatches,
    ].slice(0, 12);
  }, [searchQuery, payments, customers, recoveryCases]);

  const groupedResults = useMemo(() => ({
    pages: results.filter((item) => item.type === 'page'),
    payments: results.filter((item) => item.type === 'payment'),
    customers: results.filter((item) => item.type === 'customer'),
    recovery: results.filter((item) => item.type === 'recovery'),
  }), [results]);

  const handleSearchResult = (result: SearchResult) => {
    setSearchOpen(false);
    setSearchQuery('');

    if (result.type === 'payment' && result.paymentId && onOpenPayment) {
      onOpenPayment(result.paymentId);
      return;
    }

    if (result.page) {
      onNavigate(result.page);
    }
  };

  const refreshSearch = () => {
    setPayments([]);
    setCustomers([]);
    setRecoveryCases([]);
    setSearchError('');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar activePage={activePage} onNavigate={handleNavigate} />

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-slate-950/40"
            onClick={() => setMobileMenuOpen(false)}
          />

          <div className="relative h-full w-72 max-w-[85vw] bg-white shadow-xl">
            <div className="flex h-16 items-center justify-between border-b border-slate-100 px-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <span className="font-bold text-lg tracking-tight text-slate-800">
                  Recover<span className="text-brand-600">AI</span>
                </span>
              </div>

              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <MobileNavigation
              activePage={activePage}
              onNavigate={handleNavigate}
              onLogout={handleLogout}
            />
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-20">
          <div className="flex items-center gap-3 lg:hidden">
            <button
              type="button"
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              aria-label="Open menu"
              aria-expanded={mobileMenuOpen}
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-brand-600 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span className="font-bold text-slate-800">
                Recover<span className="text-brand-600">AI</span>
              </span>
            </div>
          </div>

          <div className="hidden lg:flex items-center text-sm text-slate-500">
            <span className="text-slate-800 font-medium">
              Good morning, {displayName}
            </span>
            <span className="mx-2 text-slate-300">/</span>
            <span>{formattedDate}</span>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 ml-auto">
            <button
              type="button"
              className="hidden md:flex items-center gap-2 w-48 h-9 rounded-lg border border-slate-200 px-3 text-slate-400 hover:border-slate-300 hover:text-slate-500 transition-colors"
              onClick={() => setSearchOpen(true)}
              aria-label="Search RecoverAI"
            >
              <Search className="h-4 w-4" />
              <span className="text-xs truncate">Search anything...</span>
              <span className="ml-auto text-[10px] border border-slate-200 rounded px-1 whitespace-nowrap">
                ⌘ K
              </span>
            </button>

            <button
              type="button"
              className="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100"
              aria-label="View recovery notifications"
              onClick={() => handleNavigate('recovery')}
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-danger-500 ring-2 ring-white" />
            </button>

            <button
              type="button"
              className="hidden sm:flex p-2 rounded-lg text-slate-500 hover:bg-slate-100"
              aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              onClick={toggleTheme}
            >
              <span className="text-xs font-semibold">
                {theme === 'dark' ? '☀' : '☾'}
              </span>
            </button>

            <div className="h-8 w-px bg-slate-200 hidden sm:block" />

            <div ref={profileRef} className="relative">
              <button
                type="button"
                className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-50"
                aria-label="Open profile menu"
                aria-expanded={profileOpen}
                onClick={() => setProfileOpen((open) => !open)}
              >
                <div className="h-8 w-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-semibold">
                  {initials}
                </div>

                <div className="hidden sm:block text-left">
                  <p className="text-xs font-medium text-slate-700">{displayName}</p>
                  <p className="text-[10px] text-slate-400">{role}</p>
                </div>

                <ChevronDown
                  className={`h-4 w-4 text-slate-400 hidden sm:block transition-transform ${profileOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
                  <div className="px-3 py-2 border-b border-slate-100 mb-1">
                    <p className="text-sm font-semibold text-slate-800 truncate">{displayName}</p>
                    <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleNavigate('settings')}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-50"
                  >
                    Settings
                  </button>

                  <button
                    type="button"
                    onClick={toggleTheme}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-50"
                  >
                    {theme === 'dark' ? 'Use light theme' : 'Use dark theme'}
                  </button>

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-danger-600 hover:bg-danger-50"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8 max-w-[1600px] mx-auto">
          {children}
        </main>
      </div>

      {searchOpen && (
        <div
          className="fixed inset-0 z-[70] flex items-start justify-center bg-slate-950/50 p-4 pt-[10vh]"
          role="dialog"
          aria-modal="true"
          aria-label="Search RecoverAI"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setSearchOpen(false);
              setSearchQuery('');
            }
          }}
        >
          <div className="w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
            <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
              <Search className="h-5 w-5 text-slate-400" />
              <input
                ref={searchInputRef}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search payments, customers, recovery cases, or pages..."
                className="flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
                aria-label="Search payments, customers, recovery cases, or pages"
              />
              <kbd className="rounded border border-slate-200 px-2 py-1 text-[10px] text-slate-400">Esc</kbd>
            </div>

            <div className="max-h-[65vh] overflow-y-auto p-2">
              {searchLoading && (
                <div className="px-4 py-8 text-center text-sm text-slate-500">
                  Searching your RecoverAI workspace...
                </div>
              )}

              {!searchLoading && searchError && (
                <div className="m-2 rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-xs text-warning-700">
                  <div className="flex items-center justify-between gap-3">
                    <span>{searchError}</span>
                    <button
                      type="button"
                      className="font-semibold underline"
                      onClick={refreshSearch}
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}

              {!searchLoading && results.length === 0 && (
                <div className="px-4 py-10 text-center">
                  <Search className="mx-auto h-7 w-7 text-slate-300" />
                  <p className="mt-3 text-sm font-medium text-slate-700">No results found</p>
                  <p className="mt-1 text-xs text-slate-400">Try a customer name, email, payment ID, failure reason, or page name.</p>
                </div>
              )}

              {!searchLoading && groupedResults.pages.length > 0 && (
                <SearchGroup title="Workspace">
                  {groupedResults.pages.map((result) => (
                    <SearchResultButton key={result.id} result={result} onSelect={handleSearchResult} />
                  ))}
                </SearchGroup>
              )}

              {!searchLoading && groupedResults.payments.length > 0 && (
                <SearchGroup title="Payments">
                  {groupedResults.payments.map((result) => (
                    <SearchResultButton key={result.id} result={result} onSelect={handleSearchResult} />
                  ))}
                </SearchGroup>
              )}

              {!searchLoading && groupedResults.customers.length > 0 && (
                <SearchGroup title="Customers">
                  {groupedResults.customers.map((result) => (
                    <SearchResultButton key={result.id} result={result} onSelect={handleSearchResult} />
                  ))}
                </SearchGroup>
              )}

              {!searchLoading && groupedResults.recovery.length > 0 && (
                <SearchGroup title="Recovery cases">
                  {groupedResults.recovery.map((result) => (
                    <SearchResultButton key={result.id} result={result} onSelect={handleSearchResult} />
                  ))}
                </SearchGroup>
              )}
            </div>

            <div className="border-t border-slate-100 px-4 py-2 text-[10px] text-slate-400">
              Search is scoped to your authenticated RecoverAI workspace.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SearchGroup({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="mb-3 last:mb-0">
      <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </p>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

function SearchResultButton({
  result,
  onSelect,
}: {
  result: SearchResult;
  onSelect: (result: SearchResult) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(result)}
      className="w-full rounded-xl px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
    >
      <p className="text-sm font-medium text-slate-800 truncate">{result.title}</p>
      <p className="mt-0.5 text-xs text-slate-400 truncate">{result.subtitle}</p>
    </button>
  );
}

function MobileNavigation({
  activePage,
  onNavigate,
  onLogout,
}: {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
  onLogout: () => void;
}) {
  const items: { key: PageKey; label: string }[] = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'payments', label: 'Payments' },
    { key: 'customers', label: 'Customers' },
    { key: 'recovery', label: 'Recovery Center' },
    { key: 'analytics', label: 'Analytics' },
    { key: 'assistant', label: 'AI Assistant' },
    { key: 'settings', label: 'Settings' },
  ];

  return (
    <div className="flex h-[calc(100%-4rem)] flex-col p-3">
      <nav className="space-y-1">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => onNavigate(item.key)}
            className={`w-full rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
              activePage === item.key
                ? 'bg-brand-50 text-brand-700 font-medium'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <button
        type="button"
        onClick={onLogout}
        className="mt-auto w-full rounded-lg px-3 py-2.5 text-left text-sm text-danger-600 hover:bg-danger-50"
      >
        Sign out
      </button>
    </div>
  );
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) return 'M';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function formatSearchAmount(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}