/**
 * RecoverAI API service.
 *
 * FastAPI + MongoDB are the source of truth.
 *
 * This file contains API communication only.
 * Business/recovery decisions remain on the backend.
 */

import {
  API_BASE_URL,
  API_ENDPOINTS,
} from '@/config/env';

import type {
  AIResponse,
  AnalyticsData,
  ChatMessage,
  Customer,
  DashboardData,
  MerchantSettings,
  Payment,
  RecoveryActionResponse,
  RecoveryCase,
  RecommendedAction,
} from '@/types';


/* =========================================================
   TYPES
========================================================= */

export type DemoRequest = {
  name: string;
  email: string;
  company?: string;
};


export type DemoRequestResponse = {
  success: boolean;
  message: string;

  access_token?: string;

  token?: string;

  user?: {
    id?: string;
    email: string;
    name?: string;
    role?: string;
  };
};


/* =========================================================
   RECOVERY BENCHMARK TYPES
========================================================= */

export type RecoveryBenchmarkStrategy = {
  strategy: string;
  batch_size: number;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  successful_recoveries: number;
  automated_actions: number;
  customer_actions: number;
  escalations: number;
  total_interventions: number;
  stopped: number;
  attempts: number;
  unsafe_actions_blocked: number;
  automated_attempts_per_successful_recovery: number;
  interventions_per_successful_recovery: number;
  revenue_recovered_per_automated_attempt: number;
  attempt_reduction_vs_retry_all_pct: number;
};


export type RecoveryBenchmark = {
  synthetic: boolean;
  seed: number;
  batch_size: number;
  ground_truth: string;
  recoverai_pipeline: string;
  strategies: RecoveryBenchmarkStrategy[];
};


/* =========================================================
   STORAGE
========================================================= */

const TOKEN_KEY =
  'recoverai_access_token';


/* =========================================================
   API FETCH
========================================================= */

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {

  const url =
    `${API_BASE_URL}${endpoint}`;


  const token =
    localStorage.getItem(
      TOKEN_KEY,
    );


  const headers =
    new Headers(
      options.headers,
    );


  if (
    !headers.has(
      'Content-Type',
    ) &&
    options.body
  ) {

    headers.set(
      'Content-Type',
      'application/json',
    );

  }


  /* -----------------------------------------------
     ATTACH JWT
  ------------------------------------------------ */

  if (
    token &&
    !headers.has(
      'Authorization',
    )
  ) {

    headers.set(
      'Authorization',
      `Bearer ${token}`,
    );

  }


  const response =
    await fetch(
      url,
      {
        ...options,
        headers,
      },
    );


  /* -----------------------------------------------
     HANDLE UNAUTHORIZED
  ------------------------------------------------ */

  if (
    response.status === 401
  ) {

    localStorage.removeItem(
      TOKEN_KEY,
    );

    localStorage.removeItem(
      'recoverai_user',
    );

    throw new Error(
      'Your session has expired. Please sign in again.',
    );

  }


  /* -----------------------------------------------
     HANDLE OTHER ERRORS
  ------------------------------------------------ */

  if (!response.ok) {

    let message =
      `API error: ${response.status}`;


    try {

      const errorBody =
        await response.json();


      if (
        errorBody?.detail
      ) {

        if (
          typeof errorBody.detail ===
          'string'
        ) {

          message =
            errorBody.detail;

        } else {

          message =
            JSON.stringify(
              errorBody.detail,
            );

        }

      }

    } catch {
      // Ignore invalid error response.
    }


    throw new Error(
      message,
    );
  }


  /* -----------------------------------------------
     NO CONTENT
  ------------------------------------------------ */

  if (
    response.status === 204
  ) {

    return undefined as T;

  }


  /* -----------------------------------------------
     JSON RESPONSE
  ------------------------------------------------ */

  return response.json() as Promise<T>;
}


/* =========================================================
   PASSWORD RESET
========================================================= */

export type PasswordResetResponse = {
  success: boolean;
  message: string;
};

export async function requestPasswordReset(
  email: string,
): Promise<PasswordResetResponse> {
  return apiFetch<PasswordResetResponse>(
    API_ENDPOINTS.requestPasswordReset,
    {
      method: 'POST',
      body: JSON.stringify({ email: email.trim() }),
    },
  );
}

export async function resetPassword(
  token: string,
  password: string,
): Promise<PasswordResetResponse> {
  return apiFetch<PasswordResetResponse>(
    API_ENDPOINTS.resetPassword,
    {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    },
  );
}


/* =========================================================
   REQUEST DEMO
========================================================= */

export async function requestDemo(
  data: DemoRequest,
): Promise<DemoRequestResponse> {

  return apiFetch<DemoRequestResponse>(
    API_ENDPOINTS.requestDemo,
    {
      method: 'POST',

      body: JSON.stringify({
        name:
          data.name.trim(),

        email:
          data.email
            .trim()
            .toLowerCase(),

        business_name:
          data.company?.trim() ||
          '',
      }),
    },
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

export async function getDashboardStats(): Promise<DashboardData> {

  return apiFetch<DashboardData>(
    API_ENDPOINTS.dashboardStats,
  );

}


/* =========================================================
   PAYMENTS
========================================================= */

export type CreatePaymentRequest = {
  customerId: string;
  amount: number;
  currency?: string;
  status: Payment["status"];
  paymentMethod: string;
  failureReason?: string | null;
};


export async function createPayment(
  data: CreatePaymentRequest,
): Promise<Payment> {

  return apiFetch<Payment>(
    API_ENDPOINTS.payments,
    {
      method: 'POST',

      body: JSON.stringify({
        customerId: data.customerId,
        amount: data.amount,
        currency: data.currency || 'INR',
        status: data.status,
        paymentMethod: data.paymentMethod,
        failureReason:
          data.failureReason || null,
      }),
    },
  );

}


export async function getPayments(): Promise<Payment[]> {

  return apiFetch<Payment[]>(
    API_ENDPOINTS.payments,
  );

}


/* =========================================================
   PAYMENT DETAILS
========================================================= */

export async function getPaymentDetails(
  id: string,
): Promise<Payment | null> {

  try {

    return await apiFetch<Payment>(
      API_ENDPOINTS.paymentDetails(
        id,
      ),
    );

  } catch (error) {

    console.error(
      'Unable to load payment details:',
      error,
    );

    return null;

  }

}


/* =========================================================
   CUSTOMERS
========================================================= */

export async function getCustomers(): Promise<Customer[]> {

  return apiFetch<Customer[]>(
    API_ENDPOINTS.customers,
  );

}

export type CreateCustomerRequest = {
  name: string;
  email: string;
  phone?: string;
  riskScore?: number;
};

export async function createCustomer(
  data: CreateCustomerRequest,
): Promise<Customer> {

  return apiFetch<Customer>(
    API_ENDPOINTS.customers,
    {
      method: 'POST',

      body: JSON.stringify({
        name: data.name.trim(),
        email: data.email.trim().toLowerCase(),
        phone: data.phone?.trim() || null,
        riskScore: data.riskScore ?? 0.5,
      }),
    },
  );
}


/* =========================================================
   RECOVERY CASES
========================================================= */

export async function getRecoveryCases(): Promise<
  RecoveryCase[]
> {

  return apiFetch<RecoveryCase[]>(
    API_ENDPOINTS.recoveryCases,
  );

}


/* =========================================================
   RECOVERY BENCHMARK
========================================================= */

export async function getRecoveryBenchmark(
  batchSize = 250,
  seed = 2026,
): Promise<RecoveryBenchmark> {

  const query =
    `?batch_size=${encodeURIComponent(batchSize)}` +
    `&seed=${encodeURIComponent(seed)}`;

  return apiFetch<RecoveryBenchmark>(
    `${API_ENDPOINTS.recoveryCases}/benchmark${query}`,
  );

}


/* =========================================================
   RECOVERY ACTION
========================================================= */

export async function sendRecoveryAction(
  paymentId: string,
  action: RecommendedAction,
): Promise<RecoveryActionResponse> {

  return apiFetch<RecoveryActionResponse>(
    API_ENDPOINTS.recoveryAction(
      paymentId,
    ),
    {
      method: 'POST',

      body: JSON.stringify({
        action,
      }),
    },
  );

}


/* =========================================================
   ANALYTICS
========================================================= */

export async function getAnalytics(): Promise<AnalyticsData> {

  return apiFetch<AnalyticsData>(
    API_ENDPOINTS.analytics,
  );

}


/* =========================================================
   AI ASSISTANT
========================================================= */

export async function sendAIMessage(
  message: string,
  history: ChatMessage[] = [],
): Promise<AIResponse> {

  return apiFetch<AIResponse>(
    API_ENDPOINTS.aiMessage,
    {
      method: 'POST',

      body: JSON.stringify({
        message,
        history,
      }),
    },
  );

}


/* =========================================================
   SETTINGS
========================================================= */

export async function getSettings(): Promise<MerchantSettings> {

  return apiFetch<MerchantSettings>(
    API_ENDPOINTS.settings,
  );

}


/* =========================================================
   UPDATE SETTINGS
========================================================= */

export async function updateSettings(
  settings: Partial<MerchantSettings>,
): Promise<{
  success: boolean;
  settings: MerchantSettings;
}> {

  return apiFetch<{
    success: boolean;
    settings: MerchantSettings;
  }>(
    API_ENDPOINTS.settings,
    {
      method: 'PUT',

      body: JSON.stringify(
        settings,
      ),
    },
  );

}