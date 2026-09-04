/**
 * Centralized RecoverAI environment configuration.
 *
 * FastAPI backend:
 * http://127.0.0.1:8000
 *
 * All API routes are prefixed with /api.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000';

export const USE_MOCK_DATA = false;

export const API_ENDPOINTS = {
  /* =========================================================
     AUTHENTICATION
  ========================================================= */

  login: '/api/auth/login',

  me: '/api/auth/me',

  requestDemo: '/api/auth/request-demo',

  requestPasswordReset: '/api/auth/request-password-reset',

  resetPassword: '/api/auth/reset-password',

  /* =========================================================
     DASHBOARD
  ========================================================= */

  dashboardStats: '/api/dashboard/stats',

  /* =========================================================
     PAYMENTS
  ========================================================= */

  payments: '/api/payments',

  paymentDetails: (id: string) =>
    `/api/payments/${encodeURIComponent(id)}`,

  /* =========================================================
     CUSTOMERS
  ========================================================= */

  customers: '/api/customers',

  /* =========================================================
     RECOVERY
  ========================================================= */

  recoveryCases: '/api/recovery-cases',

  recoveryAction: (id: string) =>
    `/api/recovery-cases/action/${encodeURIComponent(id)}`,

  /* =========================================================
     ANALYTICS
  ========================================================= */

  analytics: '/api/analytics',

  /* =========================================================
     AI ASSISTANT
  ========================================================= */

  aiMessage: '/api/ai/message',

  /* =========================================================
     SETTINGS
  ========================================================= */

  settings: '/api/settings',
} as const;