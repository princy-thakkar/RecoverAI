import {
  CheckCircle2,
  Info,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';

import type {
  RecoveryBenchmark,
  RecoveryBenchmarkStrategy,
} from '@/types';

import { Button } from '@/components/ui/Button';

import {
  Card,
  CardBody,
  CardHeader,
} from '@/components/ui/Card';

import { Badge } from '@/components/ui/Badge';

import {
  formatINRCompact,
} from '@/utils/format';

interface RecoveryBenchmarkCardProps {
  benchmark: RecoveryBenchmark;
  onRetry?: () => void;
}

function findStrategy(
  benchmark: RecoveryBenchmark,
  strategy: string,
): RecoveryBenchmarkStrategy | undefined {
  return benchmark.strategies.find(
    (item) => item.strategy === strategy,
  );
}

function Metric({
  label,
  value,
  secondary,
  description,
}: {
  label: string;
  value: string;
  secondary?: string;
  description?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-4">
      <p className="text-[10px] uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <div className="flex items-end gap-2 mt-1">
        <p className="text-lg font-bold text-slate-800">
          {value}
        </p>

        {secondary && (
          <span className="text-xs text-slate-400 mb-0.5">
            {secondary}
          </span>
        )}
      </div>

      {description && (
        <p className="text-xs text-slate-500 mt-1">
          {description}
        </p>
      )}
    </div>
  );
}

function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatCount(value: number): string {
  return value.toLocaleString('en-IN');
}

export function RecoveryBenchmarkCard({
  benchmark,
  onRetry,
}: RecoveryBenchmarkCardProps) {
  const recoverAI = findStrategy(
    benchmark,
    'RECOVERAI',
  );

  const retryAll = findStrategy(
    benchmark,
    'RETRY_ALL_ONCE',
  );

  if (!recoverAI || !retryAll) {
    return (
      <Card className="mb-6">
        <CardBody>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-800">
                Benchmark data unavailable
              </p>

              <p className="text-xs text-slate-500 mt-1">
                The benchmark response did not contain the
                expected strategies.
              </p>
            </div>

            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
              >
                Retry benchmark
              </Button>
            )}
          </div>
        </CardBody>
      </Card>
    );
  }

  const recoveredRevenueRatio =
    retryAll.revenue_recovered > 0
      ? (recoverAI.revenue_recovered /
          retryAll.revenue_recovered) *
        100
      : 0;

  const recoveryRate = recoverAI.recovery_rate;
  const attemptReduction =
    recoverAI.attempt_reduction_vs_retry_all_pct;

  return (
    <Card className="mb-6 overflow-hidden">
      <CardHeader
        title="Recovery benchmark"
        subtitle={
          `Independent ${benchmark.batch_size}-payment evaluation · ` +
          `seed ${benchmark.seed}`
        }
        action={
          <Badge className="bg-success-50 text-success-700">
            <CheckCircle2 className="h-3 w-3" />
            Independently simulated
          </Badge>
        }
      />

      <CardBody className="pt-4">
        {/* =====================================================
            HEADLINE
        ===================================================== */}

        <div className="rounded-xl border border-brand-100 bg-brand-50/50 p-5">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-brand-600" />

                <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">
                  Batch recovery result
                </p>
              </div>

              <h3 className="text-xl sm:text-2xl font-bold text-slate-900">
                {formatINRCompact(
                  recoverAI.revenue_recovered,
                )}{' '}
                recovered from{' '}
                {formatINRCompact(
                  recoverAI.revenue_at_risk,
                )}{' '}
                at-risk revenue
              </h3>

              <p className="text-sm text-slate-500 mt-2 max-w-2xl">
                RecoverAI recovered{' '}
                {formatPercentage(recoveryRate)} of the
                synthetic batch while reducing unnecessary
                automated payment attempts.
              </p>
            </div>

            <div className="lg:text-right shrink-0">
              <p className="text-3xl font-bold text-brand-700">
                {formatPercentage(recoveryRate)}
              </p>

              <p className="text-xs text-slate-500">
                recovery rate
              </p>
            </div>
          </div>
        </div>

        {/* =====================================================
            COMPARISON
        ===================================================== */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
          <Metric
            label="Revenue recovered"
            value={formatINRCompact(
              recoverAI.revenue_recovered,
            )}
            secondary={`vs ${formatINRCompact(
              retryAll.revenue_recovered,
            )}`}
            description={`${recoveredRevenueRatio.toFixed(
              1,
            )}% of retry-all recovered revenue`}
          />

          <Metric
            label="Automated payment attempts"
            value={formatCount(
              recoverAI.attempts,
            )}
            secondary={`vs ${formatCount(
              retryAll.attempts,
            )}`}
            description={`${attemptReduction.toFixed(
              0,
            )}% fewer automated attempts`}
          />

          <Metric
            label="Successful recoveries"
            value={formatCount(
              recoverAI.successful_recoveries,
            )}
            secondary={`vs ${formatCount(
              retryAll.successful_recoveries,
            )}`}
            description="Payment outcomes are simulated independently"
          />
        </div>

        {/* =====================================================
            SAFETY / INTERVENTION SUMMARY
        ===================================================== */}

        <div className="mt-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
            <div>
              <p className="text-sm font-semibold text-slate-800">
                Intervention breakdown
              </p>

              <p className="text-xs text-slate-400">
                RecoverAI chooses between automation,
                customer action, escalation, and stopping.
              </p>
            </div>

            <Badge className="bg-slate-100 text-slate-600">
              {formatCount(
                recoverAI.total_interventions,
              )}{' '}
              interventions
            </Badge>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="flex items-center gap-2">
                <Target className="h-3.5 w-3.5 text-brand-600" />

                <p className="text-lg font-bold text-slate-800">
                  {formatCount(
                    recoverAI.automated_actions,
                  )}
                </p>
              </div>

              <p className="text-[11px] text-slate-500 mt-1">
                Automated retries
              </p>
            </div>

            <div className="rounded-lg bg-slate-50 p-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-3.5 w-3.5 text-success-600" />

                <p className="text-lg font-bold text-slate-800">
                  {formatCount(
                    recoverAI.customer_actions,
                  )}
                </p>
              </div>

              <p className="text-[11px] text-slate-500 mt-1">
                Customer actions
              </p>
            </div>

            <div className="rounded-lg bg-slate-50 p-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-3.5 w-3.5 text-warning-600" />

                <p className="text-lg font-bold text-slate-800">
                  {formatCount(
                    recoverAI.escalations,
                  )}
                </p>
              </div>

              <p className="text-[11px] text-slate-500 mt-1">
                Support escalations
              </p>
            </div>

            <div className="rounded-lg bg-slate-50 p-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-slate-500" />

                <p className="text-lg font-bold text-slate-800">
                  {formatCount(
                    recoverAI.stopped,
                  )}
                </p>
              </div>

              <p className="text-[11px] text-slate-500 mt-1">
                Stopped by policy
              </p>
            </div>
          </div>
        </div>

        {/* =====================================================
            EVALUATOR TAKEAWAY
        ===================================================== */}

        <div className="mt-5 rounded-xl border border-slate-100 bg-slate-50 p-4">
          <div className="flex items-start gap-3">
            <Target className="h-4 w-4 text-brand-600 mt-0.5 shrink-0" />

            <div>
              <p className="text-sm font-semibold text-slate-800">
                What this benchmark demonstrates
              </p>

              <p className="text-xs leading-relaxed text-slate-500 mt-1">
                RecoverAI recovered{' '}
                {formatINRCompact(
                  recoverAI.revenue_recovered,
                )}{' '}
                while using{' '}
                {attemptReduction.toFixed(0)}%
                fewer automated payment attempts than
                retrying every failed payment once.
                The benchmark also records customer
                actions, support escalations, and
                policy-enforced stops instead of treating
                every failed payment as a retry candidate.
              </p>
            </div>
          </div>
        </div>

        {/* =====================================================
            METHODOLOGY
        ===================================================== */}

        <div className="flex items-start gap-2 mt-5 pt-4 border-t border-slate-100">
          <Info className="h-3.5 w-3.5 text-slate-400 mt-0.5 shrink-0" />

          <p className="text-[11px] leading-relaxed text-slate-400">
            Ground truth: {benchmark.ground_truth}.
            RecoverAI pipeline: {benchmark.recoverai_pipeline}.
            The simulator determines payment outcomes independently
            from the ML probability, preventing the benchmark from
            becoming a circular test of the model itself.
          </p>
        </div>
      </CardBody>
    </Card>
  );
}