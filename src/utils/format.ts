/**
 * Shared formatting utilities.
 */
import type {
  PaymentStatus,
  RecoveryStatus,
  FailureReason,
} from '@/types';

export function formatINR(
  amount: number
): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatINRCompact(
  amount: number
): string {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)}Cr`;
  }

  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)}L`;
  }

  if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(0)}K`;
  }

  return formatINR(amount);
}

export function formatDate(
  iso: string
): string {
  if (!iso) return '—';

  return new Date(iso).toLocaleDateString(
    'en-IN',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }
  );
}

export function formatDateTime(
  iso: string
): string {
  if (!iso) return '—';

  return new Date(iso).toLocaleString(
    'en-IN',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }
  );
}

export function timeAgo(
  iso: string
): string {
  if (!iso) return '—';

  const diff =
    Date.now() -
    new Date(iso).getTime();

  const hours = Math.floor(
    diff / 3600000
  );

  const days = Math.floor(
    hours / 24
  );

  if (days > 0) {
    return `${days}d ago`;
  }

  if (hours > 0) {
    return `${hours}h ago`;
  }

  const mins = Math.floor(
    diff / 60000
  );

  if (mins > 0) {
    return `${mins}m ago`;
  }

  return 'just now';
}

export function getProbabilityColor(
  prob: number
): string {
  if (prob >= 70) {
    return 'text-success-600';
  }

  if (prob >= 40) {
    return 'text-warning-600';
  }

  return 'text-danger-600';
}

export function getProbabilityBgColor(
  prob: number
): string {
  if (prob >= 70) {
    return 'bg-success-500';
  }

  if (prob >= 40) {
    return 'bg-warning-500';
  }

  return 'bg-danger-500';
}

export function getProbabilityLabel(
  prob: number
): string {
  if (prob >= 70) return 'High';
  if (prob >= 40) return 'Medium';
  return 'Low';
}

const paymentStatusStyles: Record<
  string,
  string
> = {
  successful:
    'bg-success-100 text-success-700',
  failed:
    'bg-danger-100 text-danger-700',
  at_risk:
    'bg-warning-100 text-warning-700',
  recovering:
    'bg-brand-100 text-brand-700',
  recovered:
    'bg-success-100 text-success-700',
};

export function getPaymentStatusClass(
  status: PaymentStatus
): string {
  return (
    paymentStatusStyles[status] ||
    'bg-slate-100 text-slate-700'
  );
}

const recoveryStatusStyles: Record<
  string,
  string
> = {
  pending:
    'bg-warning-100 text-warning-700',
  in_progress:
    'bg-brand-100 text-brand-700',
  awaiting_customer:
    'bg-warning-100 text-warning-700',
  retry_scheduled:
    'bg-brand-100 text-brand-700',
  recovered:
    'bg-success-100 text-success-700',
  failed:
    'bg-danger-100 text-danger-700',
};

export function getRecoveryStatusClass(
  status: RecoveryStatus
): string {
  return (
    recoveryStatusStyles[status] ||
    'bg-slate-100 text-slate-700'
  );
}

export function getFailureReasonColor(
  reason: FailureReason
): string {
  const colors: Record<
    FailureReason,
    string
  > = {
    'Insufficient Funds': '#f59e0b',
    'Card Expired': '#8b5cf6',
    'Network Error': '#0ea5e9',
    'Authentication Failed': '#ef4444',
    'Invalid Card': '#ec4899',
    'Bank Declined': '#64748b',
    'Fraud Suspected': '#dc2626',
    'Limit Exceeded': '#f97316',
  };

  return colors[reason];
}