/**
 * RecoverAI frontend domain types.
 *
 * The backend/FastAPI + MongoDB remains
 * the source of truth.
 */


/* =========================================================
   PAYMENT
========================================================= */

export type PaymentStatus =
  | 'pending'
  | 'successful'
  | 'failed'
  | 'at_risk'
  | 'recovering'
  | 'recovered'
  | string;


export type FailureReason =
  | 'Insufficient Funds'
  | 'Card Expired'
  | 'Network Error'
  | 'Authentication Failed'
  | 'Invalid Card'
  | 'Bank Declined'
  | 'Fraud Suspected'
  | 'Limit Exceeded'
  | string;


export type PaymentMethod =
  | 'UPI'
  | 'Credit Card'
  | 'Debit Card'
  | 'Net Banking'
  | 'Wallet'
  | string;


/* =========================================================
   RECOVERY ACTION
========================================================= */

export type RecommendedAction =
  | 'STOP'
  | 'REMINDER'
  | 'PAYMENT_METHOD_SUGGESTION'
  | 'SUPPORT_ESCALATION'
  | 'SMART_RETRY'
  | string;


export type RecoveryStatus =
  | 'pending'
  | 'in_progress'
  | 'awaiting_customer'
  | 'retry_scheduled'
  | 'recovered'
  | 'failed'
  | string;


export type PaymentAttemptStatus =
  | 'pending'
  | 'success'
  | 'failed'
  | string;


export type TimelineEventStatus =
  | 'completed'
  | 'current'
  | 'pending'
  | string;


/* =========================================================
   TIMELINE
========================================================= */

export interface TimelineEvent {

  id: string;

  type?: string;

  title: string;

  description: string;

  timestamp?:
    | string
    | null;

  status:
    TimelineEventStatus;
}


/* =========================================================
   PAYMENT ATTEMPT
========================================================= */

export interface PaymentAttempt {

  id: string;

  paymentId?: string;

  attemptNumber: number;

  method: PaymentMethod;

  amount: number;

  status: PaymentAttemptStatus;

  reason?:
    | string
    | null;

  failureReason?:
    | string
    | null;

  timestamp: string;
}


/* =========================================================
   PAYMENT
========================================================= */

export interface Payment {

  id: string;

  customerId: string;

  customerName: string;

  customerEmail: string;

  amount: number;

  paymentMethod:
    PaymentMethod;

  status:
    PaymentStatus;

  failureReason:
    | FailureReason
    | null;

  recoveryProbability:
    number;

  lastAttempt?:
    | string
    | null;

  recommendedAction:
    RecommendedAction;

  createdAt:
    string;

  attempts:
    PaymentAttempt[];

  timeline:
    TimelineEvent[];
}


/* =========================================================
   CUSTOMER
========================================================= */

export interface Customer {

  id: string;

  name: string;

  email: string;

  phone?: string;

  totalPayments:
    number;

  successfulPayments:
    number;

  failedPayments:
    number;

  totalAmount:
    number;

  recoveryProbability:
    number;

  riskProfile:
    string;

  avatarColor?: string;

  joinedAt?:
    | string
    | null;
}


/* =========================================================
   RECOVERY CASE
========================================================= */

export interface RecoveryCase {

  id: string;

  paymentId: string;

  customerId: string;

  customerName: string;

  amountAtRisk:
    number;

  failureReason:
    FailureReason;

  recoveryProbability:
    number;

  recommendedAction:
    RecommendedAction;

  status:
    RecoveryStatus;

  attempts:
    number;

  createdAt?:
    | string
    | null;

  lastUpdated?:
    | string
    | null;
}


/* =========================================================
   DASHBOARD
========================================================= */

export interface DashboardStats {

  totalTransactions:
    number;

  successfulPayments:
    number;

  failedPayments:
    number;

  revenueAtRisk:
    number;

  revenueRecovered:
    number;

  recoveryRate:
    number;
}


export interface RevenuePoint {

  label: string;

  recovered: number;

  atRisk: number;
}


export interface PaymentStatusPoint {

  label: string;

  successful: number;

  failed: number;
}


export interface FailureReasonStat {

  reason:
    FailureReason;

  count:
    number;

  amount:
    number;
}


export interface AIRecommendation {

  id: string;

  paymentId: string;

  customerName: string;

  amount: number;

  reason:
    FailureReason;

  probability:
    number;

  action:
    RecommendedAction;

  rationale:
    string;
}


export interface RecentRecoveryAttempt {

  id: string;

  customerName: string;

  amount:
    number;

  action:
    RecommendedAction;

  status:
    RecoveryStatus;

  timestamp?:
    | string
    | null;
}


export interface DashboardData {

  stats:
    DashboardStats;

  revenueChart:
    RevenuePoint[];

  statusChart:
    PaymentStatusPoint[];

  recentAttempts:
    RecentRecoveryAttempt[];

  topFailureReasons:
    FailureReasonStat[];

  recommendations:
    AIRecommendation[];
}


/* =========================================================
   ANALYTICS
========================================================= */

export interface AnalyticsData {

  revenueAtRisk:
    number;

  revenueRecovered:
    number;

  recoveryRate:
    number;

  recoveryAttempts:
    number;

  successfulRecoveries:
    number;


  recoveryByMethod: {

    method:
      PaymentMethod;

    recovered:
      number;

    attempted:
      number;

  }[];


  recoveryByReason: {

    reason:
      FailureReason;

    recovered:
      number;

    attempted:
      number;

  }[];


  performanceOverTime:
    RevenuePoint[];
}

/* =========================================================
   RECOVERY BENCHMARK
========================================================= */

export interface RecoveryBenchmarkStrategy {

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
}


export interface RecoveryBenchmark {

  synthetic: boolean;

  seed: number;

  batch_size: number;

  ground_truth: string;

  recoverai_pipeline: string;

  strategies: RecoveryBenchmarkStrategy[];
}


/* =========================================================
   AI ASSISTANT
========================================================= */

export interface ChatMessage {

  id: string;

  role:
    | 'user'
    | 'assistant';

  content:
    string;

  timestamp:
    string;
}


export interface AIResponse {

  type:
    string;

  reply:
    string;

  conversationId?:
    | string
    | null;

  paymentId?:
    | string
    | null;

  analysis?:
    Record<string, unknown>
    | null;

  payments?:
    Record<string, unknown>[]
    | null;

  failureReasons?:
    Record<string, unknown>[]
    | null;
}


/* =========================================================
   SETTINGS
========================================================= */

export interface MerchantSettings {

  merchantName:
    string;

  merchantEmail:
    string;

  merchantPhone:
    string;

  businessName:
    string;

  gstin:
    string;


  maxRetryAttempts:
    number;

  retryIntervalHours:
    number;

  minRecoveryProbability:
    number;


  emailNotifications:
    boolean;

  smsNotifications:
    boolean;

  weeklyReport:
    boolean;

  recoveryAlerts:
    boolean;
}


/* =========================================================
   AUTH
========================================================= */

export interface AuthState {

  isAuthenticated:
    boolean;

  merchantEmail:
    string | null;
}


/* =========================================================
   AI ANALYSIS
========================================================= */

export interface AIAnalysis {

  probability:
    number;

  probabilityPercent:
    number;

  riskLevel:
    string;

  recommendedAction:
    RecommendedAction;

  summary:
    string;

  reasoning:
    string;

  nextStep:
    string;

  paymentAmount:
    number;

  paymentMethod:
    string;

  failureReason:
    string;

  previousAttempts:
    number;

  failedAttempts:
    number;
}


/* =========================================================
   RECOVERY ACTION RESULT
========================================================= */

export interface RecoveryActionResult {

  payment?:
    Payment | null;

  recoveryCase?:
    RecoveryCase | null;

  paymentAttempt?:
    PaymentAttempt | null;

  auditLog?:
    Record<string, unknown>
    | null;

  probability?:
    number | null;

  action?:
    RecommendedAction
    | null;

  recommendedAction?:
    RecommendedAction
    | null;

  success:
    boolean;

  aiExplanation?:
    AIAnalysis | null;

  message?:
    string | null;

  /* -----------------------------------------------
     POLICY / SAFETY
  ------------------------------------------------ */

  policyAllowed?:
    boolean
    | null;

  policyRule?:
    string
    | null;

  policyReason?:
    string
    | null;
}


/* =========================================================
   RECOVERY ACTION RESPONSE
========================================================= */

export interface RecoveryActionResponse {

  success:
    boolean;

  paymentId:
    string;

  requestedAction?:
    RecommendedAction
    | null;

  recommendedAction?:
    RecommendedAction
    | null;

  selectedAction?:
    RecommendedAction
    | null;

  actionOverridden:
    boolean;

  /* -----------------------------------------------
     POLICY / SAFETY
  ------------------------------------------------ */

  policyAllowed?:
    boolean
    | null;

  policyRule?:
    string
    | null;

  policyReason?:
    string
    | null;

  result?:
    RecoveryActionResult
    | null;
}