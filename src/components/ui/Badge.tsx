import { type ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  className?: string;
}

export function Badge({
  children,
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}
    >
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const statusClasses: Record<string, string> = {
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
  pending:
    'bg-warning-100 text-warning-700',
  in_progress:
    'bg-brand-100 text-brand-700',
  awaiting_customer:
    'bg-warning-100 text-warning-700',
  retry_scheduled:
    'bg-brand-100 text-brand-700',
  success:
    'bg-success-100 text-success-700',

  Successful:
    'bg-success-100 text-success-700',
  Failed:
    'bg-danger-100 text-danger-700',
  'At Risk':
    'bg-warning-100 text-warning-700',
  Recovering:
    'bg-brand-100 text-brand-700',
  Recovered:
    'bg-success-100 text-success-700',
  Pending:
    'bg-warning-100 text-warning-700',
  'In Progress':
    'bg-brand-100 text-brand-700',
  'Awaiting Customer':
    'bg-warning-100 text-warning-700',
  'Retry Scheduled':
    'bg-brand-100 text-brand-700',
  'Low Risk':
    'bg-success-100 text-success-700',
  'Medium Risk':
    'bg-warning-100 text-warning-700',
  'High Risk':
    'bg-danger-100 text-danger-700',
};

function formatStatusLabel(
  status: string
): string {
  const labels: Record<string, string> = {
    successful: 'Successful',
    failed: 'Failed',
    at_risk: 'At Risk',
    recovering: 'Recovering',
    recovered: 'Recovered',
    pending: 'Pending',
    in_progress: 'In Progress',
    awaiting_customer:
      'Awaiting Customer',
    retry_scheduled:
      'Retry Scheduled',
    success: 'Successful',
  };

  return labels[status] ?? status;
}

export function StatusBadge({
  status,
  className = '',
}: StatusBadgeProps) {
  const cls =
    statusClasses[status] ||
    'bg-slate-100 text-slate-700';

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cls} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60" />
      {formatStatusLabel(status)}
    </span>
  );
}