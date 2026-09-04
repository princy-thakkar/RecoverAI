import { useState } from 'react';

import { AppShell } from '@/components/layout/AppShell';
import type { PageKey } from '@/components/layout/Sidebar';

import {
  DashboardPage,
  PaymentsPage,
  CustomersPage,
  RecoveryPage,
  AnalyticsPage,
} from '@/pages/Pages';

import {
  AssistantPage,
  LoginPage,
  ResetPasswordPage,
  PaymentDetailsPage,
  SettingsPage,
} from '@/pages/ExtraPages';

import {
  AuthProvider,
  useAuth,
} from '@/context/AuthContext';

import { ThemeProvider } from '@/context/ThemeContext';

function ProtectedApplication() {
  const hasPasswordResetToken = new URLSearchParams(
    window.location.search,
  ).has('reset_token');

  if (hasPasswordResetToken) {
    return <ResetPasswordPage />;
  }

  const { authenticated, loading } = useAuth();

  const [page, setPage] =
    useState<PageKey>('dashboard');

  const [paymentId, setPaymentId] =
    useState<string | null>(null);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-sm text-slate-500">
          Loading RecoverAI...
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return <LoginPage />;
  }

  const navigate = (nextPage: PageKey) => {
    setPaymentId(null);
    setPage(nextPage);
  };

  const openPayment = (id: string) => {
    setPage('payments');
    setPaymentId(id);
  };

  const content = paymentId ? (
    <PaymentDetailsPage
      id={paymentId}
      onBack={() => setPaymentId(null)}
    />
  ) : (
    (() => {
      switch (page) {
        case 'dashboard':
          return (
            <DashboardPage
              onNavigate={navigate}
            />
          );

        case 'payments':
          return (
            <PaymentsPage
              onNavigate={navigate}
            />
          );

        case 'customers':
          return <CustomersPage />;

        case 'recovery':
          return <RecoveryPage />;

        case 'analytics':
          return <AnalyticsPage />;

        case 'assistant':
          return <AssistantPage />;

        case 'settings':
          return <SettingsPage />;

        default:
          return (
            <DashboardPage
              onNavigate={navigate}
            />
          );
      }
    })()
  );

  return (
    <AppShell
      activePage={page}
      onNavigate={navigate}
      onOpenPayment={openPayment}
    >
      {content}
    </AppShell>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ProtectedApplication />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;