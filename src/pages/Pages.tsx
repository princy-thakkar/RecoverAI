import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { FormEvent } from 'react';

import {
  Activity,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
  Clock3,
  Download,
  Filter,
  Info,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  X,
} from 'lucide-react';

import {
  getAnalytics,
  getCustomers,
  getDashboardStats,
  createPayment,
  getPaymentDetails,
  getPayments,
  getRecoveryBenchmark,
  getRecoveryCases,
  sendRecoveryAction,
  createCustomer,
} from '@/services/api';

import type {
  AnalyticsData,
  Customer,
  DashboardData,
  Payment,
  RecoveryCase,
} from '@/types';

import { Button } from '@/components/ui/Button';

import {
  Card,
  CardBody,
  CardHeader,
} from '@/components/ui/Card';

import {
  Badge,
  StatusBadge,
} from '@/components/ui/Badge';

import {
  ErrorState,
  EmptyState,
  Spinner,
} from '@/components/ui/States';

import { ProbabilityBar } from '@/components/ui/ProbabilityBar';

import {
  DonutChart,
  PaymentStatusChart,
  RevenueChart,
} from '@/components/ui/Charts';

import { PageHeader } from '@/components/ui/PageHeader';

import { StatCard } from '@/components/ui/StatCard';

import {
  formatDateTime,
  formatINR,
  formatINRCompact,
  getFailureReasonColor,
  getProbabilityColor,
  timeAgo,
} from '@/utils/format';

import type { PageKey } from '@/components/layout/Sidebar';

import { RecoveryBenchmarkCard } from '@/components/recovery/RecoveryBenchmarkCard';


/* =========================================================
   ASYNC HOOK
========================================================= */

function useAsync<T>(
  loader: () => Promise<T>,
  deps: unknown[] = []
) {

  const [data, setData] =
    useState<T | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(false);

  const load = async () => {

    setLoading(true);
    setError(false);

    try {

      const result = await loader();

      setData(result);

    } catch (err) {

      console.error(
        'API error:',
        err
      );

      setError(true);

    } finally {

      setLoading(false);
    }
  };

  useEffect(() => {

    void load();

  }, deps);

  return {
    data,
    loading,
    error,
    retry: load,
  };
}


/* =========================================================
   PAGE LOADING
========================================================= */

function PageLoading({
  title,
}: {
  title: string;
}) {

  return (
    <div>

      <PageHeader title={title} />

      <Spinner />

    </div>
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

export function DashboardPage({
  onNavigate,
}: {
  onNavigate: (page: PageKey) => void;
}) {

  const {
    data,
    loading,
    error,
    retry,
  } = useAsync(getDashboardStats);

  if (loading) {
    return (
      <PageLoading title="Dashboard" />
    );
  }

  if (error || !data) {

    return (
      <ErrorState
        message="Unable to load dashboard data"
        onRetry={retry}
      />
    );
  }

  return (
    <DashboardContent
      data={data}
      onNavigate={onNavigate}
    />
  );
}


/* =========================================================
   DASHBOARD CONTENT
========================================================= */

function DashboardContent({
  data,
  onNavigate,
}: {
  data: DashboardData;
  onNavigate: (page: PageKey) => void;
}) {

  const {
    stats,
    revenueChart,
    statusChart,
    recentAttempts,
    topFailureReasons,
    recommendations,
  } = data;

  return (
    <div className="animate-fade-in">

      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Monitor payment performance and revenue recovery."
        action={
          <div className="flex gap-2">

            <Button
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4" />
              Export report
            </Button>

            <Button
              size="sm"
              onClick={() =>
                onNavigate('recovery')
              }
            >
              <Sparkles className="h-4 w-4" />
              Recovery center
            </Button>

          </div>
        }
      />


      {/* =====================================================
          STATS
      ===================================================== */}

      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4 mb-6">

        <StatCard
          label="Total transactions"
          value={stats.totalTransactions.toLocaleString(
            'en-IN'
          )}
          icon={
            <Activity className="h-4 w-4" />
          }
          iconClassName="bg-brand-50 text-brand-600"
        />

        <StatCard
          label="Successful payments"
          value={stats.successfulPayments.toLocaleString(
            'en-IN'
          )}
          icon={
            <CheckCircle2 className="h-4 w-4" />
          }
          iconClassName="bg-success-50 text-success-600"
        />

        <StatCard
          label="Failed payments"
          value={stats.failedPayments.toLocaleString(
            'en-IN'
          )}
          icon={
            <ShieldAlert className="h-4 w-4" />
          }
          iconClassName="bg-danger-50 text-danger-600"
        />

        <StatCard
          label="Revenue at risk"
          value={formatINRCompact(
            stats.revenueAtRisk
          )}
          icon={
            <Target className="h-4 w-4" />
          }
          iconClassName="bg-warning-50 text-warning-600"
        />

        <StatCard
          label="Revenue recovered"
          value={formatINRCompact(
            stats.revenueRecovered
          )}
          icon={
            <CircleDollarSign className="h-4 w-4" />
          }
          iconClassName="bg-success-50 text-success-600"
        />

        <StatCard
          label="Recovery rate"
          value={`${stats.recoveryRate}%`}
          icon={
            <TrendingUp className="h-4 w-4" />
          }
          iconClassName="bg-brand-50 text-brand-600"
        />

      </div>


      {/* =====================================================
          CHARTS
      ===================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4 mb-6">

        <Card className="xl:col-span-3">

          <CardHeader
            title="Revenue recovery"
            subtitle="Recovery performance from backend data"
            action={
              <button
                type="button"
                className="text-xs text-slate-500 border border-slate-200 rounded-lg px-2.5 py-1.5 flex items-center gap-1"
              >
                Recovery data
                <ChevronDown className="h-3 w-3" />
              </button>
            }
          />

          <CardBody className="pt-4">

            <RevenueChart
              data={revenueChart}
            />

          </CardBody>

        </Card>


        <Card className="xl:col-span-2">

          <CardHeader
            title="Payment performance"
            subtitle="Successful vs failed payments"
            action={
              <button
                type="button"
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
            }
          />

          <CardBody className="pt-4">

            <PaymentStatusChart
              data={statusChart}
            />

          </CardBody>

        </Card>

      </div>


      {/* =====================================================
          RECENT ATTEMPTS
      ===================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">

        <Card className="xl:col-span-3">

          <CardHeader
            title="Recent recovery attempts"
            action={
              <button
                type="button"
                className="text-xs font-medium text-brand-600 hover:text-brand-700"
                onClick={() =>
                  onNavigate('recovery')
                }
              >
                View all
                <ArrowRight className="h-3 w-3 inline ml-1" />
              </button>
            }
          />

          <div className="overflow-x-auto">

            <table className="w-full text-left">

              <thead>

                <tr className="border-b border-slate-100 text-[10px] uppercase tracking-wider text-slate-400">

                  <th className="px-5 py-3 font-medium">
                    Customer
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Amount
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Action
                  </th>

                  <th className="px-5 py-3 font-medium">
                    Status
                  </th>

                  <th className="px-5 py-3 font-medium">
                    When
                  </th>

                </tr>

              </thead>

              <tbody>

                {recentAttempts.map(
                  (attempt) => (

                    <tr
                      key={attempt.id}
                      className="border-b border-slate-50 last:border-0 hover:bg-slate-50"
                    >

                      <td className="px-5 py-3 text-sm font-medium text-slate-700">
                        {attempt.customerName}
                      </td>

                      <td className="px-5 py-3 text-sm text-slate-700">
                        {formatINR(
                          attempt.amount
                        )}
                      </td>

                      <td className="px-5 py-3 text-xs text-slate-500">
                        {attempt.action}
                      </td>

                      <td className="px-5 py-3">
                        <StatusBadge
                          status={
                            attempt.status
                          }
                        />
                      </td>

                      <td className="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">
                        {attempt.timestamp
                          ? timeAgo(
                              attempt.timestamp
                            )
                          : '—'}
                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>

          </div>

        </Card>


        {/* ===================================================
            FAILURE REASONS
        =================================================== */}

        <Card className="xl:col-span-2">

          <CardHeader
            title="Top failure reasons"
            subtitle="Revenue currently exposed to failed payments"
          />

          <CardBody className="pt-4 space-y-4">

            {topFailureReasons.map(
              (item, index) => {

                const maximum =
                  Math.max(
                    ...topFailureReasons.map(
                      (reason) =>
                        reason.count
                    ),
                    1
                  );

                const width =
                  (item.count /
                    maximum) *
                  100;

                return (
                  <div
                    key={item.reason}
                  >

                    <div className="flex items-center justify-between mb-1.5">

                      <span className="text-xs font-medium text-slate-700 flex items-center gap-2">

                        <span
                          className="h-2 w-2 rounded-full"
                          style={{
                            backgroundColor:
                              getFailureReasonColor(
                                item.reason
                              ),
                          }}
                        />

                        {item.reason}

                      </span>

                      <span className="text-xs text-slate-400">
                        {item.count} cases
                      </span>

                    </div>

                    <div className="h-1.5 bg-slate-100 rounded-full">

                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${width}%`,
                          backgroundColor:
                            getFailureReasonColor(
                              item.reason
                            ),
                        }}
                      />

                    </div>

                    <p className="text-[10px] text-slate-400 mt-1">
                      {formatINR(
                        item.amount
                      )}{' '}
                      at risk
                    </p>

                  </div>
                );
              }
            )}

          </CardBody>

        </Card>

      </div>


      {/* =====================================================
          AI RECOMMENDATIONS
      ===================================================== */}

      <Card className="mt-4">

        <CardHeader
          title="AI recommendations"
          subtitle="Recommendations generated from backend recovery analysis"
          action={
            <Badge className="bg-brand-50 text-brand-700">
              <Sparkles className="h-3 w-3" />
              AI
            </Badge>
          }
        />

        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">

          {recommendations.map(
            (rec) => (

              <div
                key={rec.id}
                className="p-5"
              >

                <div className="flex items-start justify-between gap-3">

                  <div>

                    <p className="text-sm font-semibold text-slate-800">
                      {rec.customerName}
                    </p>

                    <p className="text-xs text-slate-500 mt-0.5">
                      {rec.reason} ·{' '}
                      {formatINR(
                        rec.amount
                      )}
                    </p>

                  </div>

                  <span
                    className={`text-sm font-bold ${getProbabilityColor(
                      rec.probability
                    )}`}
                  >
                    {rec.probability}%
                  </span>

                </div>

                <p className="text-xs text-slate-500 leading-relaxed mt-3">
                  {rec.rationale}
                </p>

                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4 w-full"
                  onClick={() =>
                    onNavigate(
                      'recovery'
                    )
                  }
                >
                  {rec.action}
                  <ArrowRight className="h-3 w-3" />
                </Button>

              </div>
            )
          )}

        </div>

      </Card>

    </div>
  );
}


/* =========================================================
   PAYMENTS PAGE
========================================================= */

export function PaymentsPage({
  onNavigate,
}: {
  onNavigate: (page: PageKey) => void;
}) {

  const {
    data,
    loading,
    error,
    retry,
  } = useAsync(getPayments);

  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('all');
  const [selected, setSelected] = useState<Payment | null>(null);
  const [showAddPayment, setShowAddPayment] = useState(false);

  const filtered = useMemo(
    () => {
      return (data || []).filter((payment) => {
        const statusMatches =
          status === 'all' || payment.status === status;

        const searchable = [
          payment.id,
          payment.customerName,
          payment.customerEmail,
          payment.failureReason,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();

        return (
          statusMatches &&
          searchable.includes(query.toLowerCase())
        );
      });
    },
    [data, query, status]
  );

  if (loading) {
    return <PageLoading title="Payments" />;
  }

  if (error || !data) {
    return (
      <ErrorState
        message="Unable to load payments"
        onRetry={retry}
      />
    );
  }

  return (
    <div className="animate-fade-in">

      <PageHeader
        title="Payments"
        description="Monitor transactions and identify recovery opportunities."
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4" />
              Export payments
            </Button>

            <Button
              size="sm"
              onClick={() => setShowAddPayment(true)}
            >
              <Plus className="h-4 w-4" />
              Add payment
            </Button>
          </div>
        }
      />

      <Card>
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3 justify-between">
          <div className="relative max-w-sm w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search payments or customers..."
              className="w-full h-9 pl-9 pr-3 text-sm border border-slate-200 rounded-lg focus:border-brand-500 focus:outline-none"
            />
          </div>

          <div className="flex gap-2 items-center">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="h-9 text-sm border border-slate-200 rounded-lg px-3 text-slate-600"
            >
              <option value="all">All</option>
              <option value="successful">Successful</option>
              <option value="failed">Failed</option>
              <option value="at_risk">At Risk</option>
              <option value="recovering">Recovering</option>
              <option value="recovered">Recovered</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left min-w-[1040px]">
            <thead>
              <tr className="border-b border-slate-100 text-[10px] uppercase tracking-wider text-slate-400 bg-slate-50/50">
                <th className="px-5 py-3 font-medium">Payment</th>
                <th className="px-5 py-3 font-medium">Customer</th>
                <th className="px-5 py-3 font-medium">Amount</th>
                <th className="px-5 py-3 font-medium">Method</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Failure reason</th>
                <th className="px-5 py-3 font-medium">Recovery probability</th>
                <th className="px-5 py-3 font-medium">Last attempt</th>
                <th className="px-5 py-3 font-medium">Action</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>

            <tbody>
              {filtered.map((payment) => (
                <tr
                  key={payment.id}
                  className="border-b border-slate-50 hover:bg-slate-50/70"
                >
                  <td className="px-5 py-3 text-xs font-medium text-brand-600 whitespace-nowrap">
                    {payment.id}
                  </td>

                  <td className="px-5 py-3">
                    <p className="text-sm font-medium text-slate-700">
                      {payment.customerName}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {payment.customerEmail}
                    </p>
                  </td>

                  <td className="px-5 py-3 text-sm font-semibold text-slate-700">
                    {formatINR(payment.amount)}
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500">
                    {payment.paymentMethod}
                  </td>

                  <td className="px-5 py-3">
                    <StatusBadge status={payment.status} />
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500">
                    {payment.failureReason || '—'}
                  </td>

                  <td className="px-5 py-3 w-40">
                    <ProbabilityBar
                      probability={payment.recoveryProbability}
                      size="sm"
                    />
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">
                    {payment.lastAttempt
                      ? timeAgo(payment.lastAttempt)
                      : '—'}
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500 whitespace-nowrap">
                    {payment.recommendedAction}
                  </td>

                  <td className="px-5 py-3">
                    <button
                      type="button"
                      onClick={() => setSelected(payment)}
                      className="text-xs font-medium text-brand-600 hover:text-brand-700 whitespace-nowrap"
                    >
                      View details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filtered.length === 0 && (
            <EmptyState
              title="No payments found"
              description="Try changing your filters or search term."
            />
          )}
        </div>

        <div className="px-5 py-3 border-t border-slate-100 text-xs text-slate-500">
          Showing {filtered.length} of {data.length} payments
        </div>
      </Card>

      {selected && (
        <PaymentDrawer
          payment={selected}
          onClose={() => setSelected(null)}
          onNavigate={onNavigate}
        />
      )}

      {showAddPayment && (
        <AddPaymentModal
          onClose={() => setShowAddPayment(false)}
          onCreated={async () => {
            setShowAddPayment(false);
            await retry();
          }}
        />
      )}
    </div>
  );
}


/* =========================================================
   ADD PAYMENT MODAL
========================================================= */

function AddPaymentModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => Promise<void> | void;
}) {
  const {
    data: customers,
    loading: customersLoading,
    error: customersError,
    retry: retryCustomers,
  } = useAsync(getCustomers);

  const [customerId, setCustomerId] = useState('');
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('UPI');
  const [paymentStatus, setPaymentStatus] = useState<Payment['status']>('failed');
  const [failureReason, setFailureReason] = useState('Insufficient Funds');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError('');

    const numericAmount = Number(amount);

    if (!customerId) {
      setFormError('Please select a customer.');
      return;
    }

    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setFormError('Enter a valid amount greater than ₹0.');
      return;
    }

    setSaving(true);

    try {
      await createPayment({
        customerId,
        amount: numericAmount,
        currency: 'INR',
        status: paymentStatus,
        paymentMethod,
        failureReason:
          paymentStatus === 'failed' || paymentStatus === 'at_risk'
            ? failureReason
            : null,
      });

      await onCreated();
    } catch (err) {
      setFormError(
        err instanceof Error
          ? err.message
          : 'Unable to create payment.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40"
        onClick={() => !saving && onClose()}
      />

      <div className="relative w-full max-w-lg rounded-xl bg-white shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-slate-200">
          <div>
            <p className="text-xs font-medium text-brand-600">Payments</p>
            <h2 className="text-lg font-bold text-slate-800 mt-1">
              Add payment
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Create a transaction in the current merchant account.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-50"
          >
            <X className="h-5 w-5 text-slate-500" />
          </button>
        </div>

        <form onSubmit={submit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">
              Customer
            </label>
            <select
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              disabled={customersLoading || saving}
              className="w-full h-10 text-sm border border-slate-200 rounded-lg px-3 text-slate-700 focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
            >
              <option value="">
                {customersLoading ? 'Loading customers...' : 'Select customer'}
              </option>
              {(customers || []).map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} — {customer.email}
                </option>
              ))}
            </select>
            {customersError && (
              <button
                type="button"
                onClick={() => void retryCustomers()}
                className="text-xs text-brand-600 mt-1.5 hover:underline"
              >
                Unable to load customers. Retry.
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Amount (INR)
              </label>
              <input
                type="number"
                min="1"
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="1000"
                disabled={saving}
                className="w-full h-10 text-sm border border-slate-200 rounded-lg px-3 text-slate-700 focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Payment method
              </label>
              <select
                value={paymentMethod}
                onChange={(event) => setPaymentMethod(event.target.value)}
                disabled={saving}
                className="w-full h-10 text-sm border border-slate-200 rounded-lg px-3 text-slate-700 focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
              >
                <option value="UPI">UPI</option>
                <option value="CARD">Card</option>
                <option value="NET_BANKING">Net Banking</option>
                <option value="WALLET">Wallet</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">
              Status
            </label>
            <select
              value={paymentStatus}
              onChange={(event) => {
                const nextStatus = event.target.value as Payment['status'];
                setPaymentStatus(nextStatus);
                if (nextStatus === 'successful' || nextStatus === 'recovered') {
                  setFailureReason('');
                } else if (!failureReason) {
                  setFailureReason('Insufficient Funds');
                }
              }}
              disabled={saving}
              className="w-full h-10 text-sm border border-slate-200 rounded-lg px-3 text-slate-700 focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
            >
              <option value="failed">Failed</option>
              <option value="at_risk">At Risk</option>
              <option value="recovering">Recovering</option>
              <option value="successful">Successful</option>
              <option value="recovered">Recovered</option>
            </select>
          </div>

          {(paymentStatus === 'failed' || paymentStatus === 'at_risk') && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                Failure reason
              </label>
              <select
                value={failureReason}
                onChange={(event) => setFailureReason(event.target.value)}
                disabled={saving}
                className="w-full h-10 text-sm border border-slate-200 rounded-lg px-3 text-slate-700 focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
              >
                <option value="Insufficient Funds">Insufficient Funds</option>
                <option value="Timeout">Timeout</option>
                <option value="Network Error">Network Error</option>
                <option value="Expired Card">Expired Card</option>
                <option value="Invalid Card">Invalid Card</option>
                <option value="Bank Declined">Bank Declined</option>
              </select>
            </div>
          )}

          {formError && (
            <div className="rounded-lg border border-red-100 bg-red-50 px-3 py-2.5 text-xs text-red-700">
              {formError}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={saving || customersLoading || !customers?.length}
            >
              {saving ? 'Creating...' : 'Create payment'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}


/* =========================================================
   PAYMENT DRAWER
========================================================= */

function PaymentDrawer({
  payment,
  onClose,
  onNavigate,
}: {
  payment: Payment;
  onClose: () => void;
  onNavigate: (page: PageKey) => void;
}) {

  const [
    details,
    setDetails,
  ] = useState<Payment | null>(
    payment
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  useEffect(() => {

    let mounted = true;

    const loadDetails = async () => {

      setLoading(true);

      const result =
        await getPaymentDetails(
          payment.id
        );

      if (mounted && result) {
        setDetails(result);
      }

      if (mounted) {
        setLoading(false);
      }
    };

    void loadDetails();

    return () => {
      mounted = false;
    };

  }, [payment.id]);

  const current =
    details || payment;

  return (
    <div className="fixed inset-0 z-40">

      <div
        className="absolute inset-0 bg-slate-900/30"
        onClick={onClose}
      />

      <div className="absolute right-0 top-0 bottom-0 w-full max-w-lg bg-white shadow-xl overflow-y-auto">

        <div className="flex items-center justify-between p-5 border-b border-slate-200">

          <div>

            <p className="text-xs text-brand-600 font-medium">
              {current.id}
            </p>

            <h2 className="text-lg font-bold text-slate-800 mt-1">
              Payment details
            </h2>

          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100"
          >
            <X className="h-5 w-5 text-slate-500" />
          </button>

        </div>


        <div className="p-5 space-y-5">

          {loading && (
            <Spinner />
          )}

          <div className="flex items-center justify-between">

            <div>

              <p className="text-xs text-slate-500">
                Transaction amount
              </p>

              <p className="text-2xl font-bold text-slate-800 mt-1">
                {formatINR(
                  current.amount
                )}
              </p>

            </div>

            <StatusBadge
              status={current.status}
            />

          </div>


          <div className="grid grid-cols-2 gap-4">

            <div>

              <p className="text-xs text-slate-400">
                Customer
              </p>

              <p className="text-sm font-medium text-slate-700 mt-1">
                {current.customerName}
              </p>

              <p className="text-xs text-slate-500">
                {current.customerEmail}
              </p>

            </div>

            <div>

              <p className="text-xs text-slate-400">
                Payment method
              </p>

              <p className="text-sm font-medium text-slate-700 mt-1">
                {current.paymentMethod}
              </p>

            </div>

          </div>


          <div className="bg-slate-50 rounded-lg p-4">

            <div className="flex justify-between mb-2">

              <span className="text-xs text-slate-500">
                Recovery probability
              </span>

              <span
                className={`text-sm font-bold ${getProbabilityColor(
                  current.recoveryProbability
                )}`}
              >
                {current.recoveryProbability}%
              </span>

            </div>

            <ProbabilityBar
              probability={
                current.recoveryProbability
              }
              showLabel={false}
            />

          </div>


          {current.failureReason && (

            <div className="flex items-start gap-3 p-3 rounded-lg bg-warning-50 border border-warning-100">

              <Info className="h-4 w-4 text-warning-600 mt-0.5" />

              <div>

                <p className="text-xs font-semibold text-warning-700">
                  Failure reason
                </p>

                <p className="text-xs text-warning-700 mt-0.5">
                  {current.failureReason}
                </p>

              </div>

            </div>

          )}


          <div>

            <h3 className="text-sm font-semibold text-slate-800 mb-3">
              Recovery timeline
            </h3>

            <div className="space-y-0">

              {current.timeline.map(
                (event, index) => (

                  <div
                    key={event.id}
                    className="flex gap-3"
                  >

                    <div className="flex flex-col items-center">

                      <div
                        className={`h-6 w-6 rounded-full flex items-center justify-center ${
                          event.status ===
                          'completed'
                            ? 'bg-success-100 text-success-600'
                            : event.status ===
                              'current'
                            ? 'bg-brand-100 text-brand-600'
                            : 'bg-slate-100 text-slate-400'
                        }`}
                      >

                        {event.status ===
                        'completed' ? (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        ) : event.status ===
                          'current' ? (
                          <Activity className="h-3.5 w-3.5" />
                        ) : (
                          <Clock3 className="h-3.5 w-3.5" />
                        )}

                      </div>

                      {index <
                        current.timeline
                          .length -
                          1 && (
                        <div className="w-px h-8 bg-slate-200" />
                      )}

                    </div>


                    <div className="pb-3">

                      <p
                        className={`text-xs font-medium ${
                          event.status ===
                          'pending'
                            ? 'text-slate-400'
                            : 'text-slate-700'
                        }`}
                      >
                        {event.title}
                      </p>

                      <p className="text-[10px] text-slate-400 mt-0.5">

                        {event.description}

                        {event.timestamp &&
                          ` · ${formatDateTime(
                            event.timestamp
                          )}`}

                      </p>

                    </div>

                  </div>
                )
              )}

            </div>

          </div>


          <div className="flex gap-2">

            <Button
              className="flex-1"
              onClick={() => {

                onClose();

                onNavigate(
                  'recovery'
                );

              }}
            >
              <Sparkles className="h-4 w-4" />
              View recovery case
            </Button>

            <Button
              variant="outline"
              onClick={onClose}
            >
              Close
            </Button>

          </div>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   CUSTOMERS PAGE
========================================================= */

export function CustomersPage() {

  const {
    data,
    loading,
    error,
    retry,
  } = useAsync(getCustomers);

  const [
    query,
    setQuery,
  ] = useState('');

  const [
    showAddCustomer,
    setShowAddCustomer,
  ] = useState(false);

  const [
    name,
    setName,
  ] = useState('');

  const [
    email,
    setEmail,
  ] = useState('');

  const [
    phone,
    setPhone,
  ] = useState('');

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    saveError,
    setSaveError,
  ] = useState('');

  if (loading) {

    return (
      <PageLoading title="Customers" />
    );
  }

  if (error || !data) {

    return (
      <ErrorState
        message="Unable to load customers"
        onRetry={retry}
      />
    );
  }

  const filtered =
    data.filter(
      (customer) =>
        [
          customer.name,
          customer.email,
          customer.id,
        ]
          .join(' ')
          .toLowerCase()
          .includes(
            query.toLowerCase()
          )
    );

  async function handleAddCustomer() {

    if (!name.trim() || !email.trim()) {
      setSaveError(
        'Name and email are required.'
      );
      return;
    }

    try {

      setSaving(true);
      setSaveError('');

      await createCustomer({
        name,
        email,
        phone,
        riskScore: 0.5,
      });

      setName('');
      setEmail('');
      setPhone('');
      setShowAddCustomer(false);

      await retry();

    } catch (error) {

      setSaveError(
        error instanceof Error
          ? error.message
          : 'Unable to create customer.'
      );

    } finally {

      setSaving(false);

    }
  }

  return (
    <div className="animate-fade-in">

      <PageHeader
        title="Customers"
        description="Understand customer payment history and recovery profiles."
        action={
          <div className="flex items-center gap-2">

            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setShowAddCustomer(
                  !showAddCustomer
                )
              }
            >
              {showAddCustomer
                ? 'Cancel'
                : '+ Add Customer'}
            </Button>

            <Button
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4" />
              Export customers
            </Button>

          </div>
        }
      />


      {showAddCustomer && (

        <Card className="mb-4">

          <div className="p-5">

            <div className="mb-4">

              <h3 className="text-sm font-semibold text-slate-700">
                Add customer
              </h3>

              <p className="text-xs text-slate-400 mt-1">
                Add a real customer so RecoverAI can track their payment and recovery history.
              </p>

            </div>


            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">

              <input
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                placeholder="Customer name"
                className="h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand-500"
              />

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="Email address"
                className="h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand-500"
              />

              <input
                value={phone}
                onChange={(event) =>
                  setPhone(event.target.value)
                }
                placeholder="Phone number (optional)"
                className="h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand-500"
              />

            </div>


            {saveError && (

              <p className="mt-3 text-xs text-danger-600">
                {saveError}
              </p>

            )}


            <div className="flex justify-end mt-4">

              <Button
                size="sm"
                disabled={saving}
                onClick={handleAddCustomer}
              >
                {saving
                  ? 'Saving...'
                  : 'Save customer'}
              </Button>

            </div>

          </div>

        </Card>

      )}


      <Card>

        <div className="p-4 border-b border-slate-100">

          <div className="relative max-w-sm">

            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />

            <input
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value
                )
              }
              placeholder="Search customers..."
              className="w-full h-9 pl-9 pr-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-brand-500"
            />

          </div>

        </div>


        <div className="overflow-x-auto">

          <table className="w-full text-left min-w-[900px]">

            <thead>

              <tr className="border-b border-slate-100 text-[10px] uppercase tracking-wider text-slate-400 bg-slate-50/50">

                <th className="px-5 py-3 font-medium">
                  Customer
                </th>

                <th className="px-5 py-3 font-medium">
                  Payments
                </th>

                <th className="px-5 py-3 font-medium">
                  Successful
                </th>

                <th className="px-5 py-3 font-medium">
                  Failed
                </th>

                <th className="px-5 py-3 font-medium">
                  Total amount
                </th>

                <th className="px-5 py-3 font-medium">
                  Recovery probability
                </th>

                <th className="px-5 py-3 font-medium">
                  Profile
                </th>

              </tr>

            </thead>


            <tbody>

              {filtered.map(
                (customer) => (

                  <tr
                    key={customer.id}
                    className="border-b border-slate-50 hover:bg-slate-50"
                  >

                    <td className="px-5 py-4">

                      <div className="flex items-center gap-3">

                        <div
                          className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold text-white"
                          style={{
                            backgroundColor:
                              customer.avatarColor ||
                              '#64748b',
                          }}
                        >
                          {customer.name
                            .split(' ')
                            .map(
                              (name) =>
                                name[0]
                            )
                            .join('')}
                        </div>

                        <div>

                          <p className="text-sm font-medium text-slate-700">
                            {customer.name}
                          </p>

                          <p className="text-[10px] text-slate-400">
                            {customer.id} ·{' '}
                            {customer.email}
                          </p>

                        </div>

                      </div>

                    </td>

                    <td className="px-5 py-4 text-sm text-slate-600">
                      {customer.totalPayments}
                    </td>

                    <td className="px-5 py-4 text-sm text-success-600 font-medium">
                      {customer.successfulPayments}
                    </td>

                    <td className="px-5 py-4 text-sm text-danger-600 font-medium">
                      {customer.failedPayments}
                    </td>

                    <td className="px-5 py-4 text-sm font-semibold text-slate-700">
                      {formatINR(
                        customer.totalAmount
                      )}
                    </td>

                    <td className="px-5 py-4 w-44">

                      <ProbabilityBar
                        probability={
                          customer.recoveryProbability
                        }
                        size="sm"
                      />

                    </td>

                    <td className="px-5 py-4">

                      <StatusBadge
                        status={
                          customer.riskProfile
                        }
                      />

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

          {filtered.length === 0 && (

            <EmptyState
              title="No customers found"
              description="Try another search term."
            />

          )}

        </div>

      </Card>

    </div>
  );
}


/* =========================================================
   RECOVERY PAGE
========================================================= */

export function RecoveryPage() {
  const {
    data,
    loading,
    error,
    retry,
  } = useAsync(
    getRecoveryCases
  );

  const [
    cases,
    setCases,
  ] = useState<RecoveryCase[]>(
    []
  );

  const [
    acting,
    setActing,
  ] = useState('');

  useEffect(() => {
    if (data) {
      setCases(data);
    }
  }, [data]);

  if (loading) {
    return (
      <PageLoading
        title="Recovery Center"
      />
    );
  }

  if (error || !data) {
    return (
      <ErrorState
        message="Unable to load recovery cases"
        onRetry={retry}
      />
    );
  }

  const activeCases =
    cases.filter(
      (item) =>
        item.status !==
          'recovered' &&
        item.status !==
          'failed'
    );

  const recoveredCases =
    cases.filter(
      (item) =>
        item.status ===
        'recovered'
    );

  const activeAmountAtRisk =
    activeCases.reduce(
      (sum, item) =>
        sum + item.amountAtRisk,
      0
    );

  const recoveredAmount =
    recoveredCases.reduce(
      (sum, item) =>
        sum + item.amountAtRisk,
      0
    );

  const totalTrackedAmount =
    cases.reduce(
      (sum, item) =>
        sum + item.amountAtRisk,
      0
    );

  const recoveryRate =
    totalTrackedAmount > 0
      ? Math.round(
          (recoveredAmount /
            totalTrackedAmount) *
            100
        )
      : 0;

  const casesNeedingAttention =
    activeCases.filter(
      (item) =>
        item.recommendedAction !==
        'STOP'
    ).length;

  /* =======================================================
     ACTION
  ======================================================= */

  const action = async (
    item: RecoveryCase
  ) => {
    if (
      !item.paymentId ||
      !item.recommendedAction ||
      item.recommendedAction ===
        'STOP'
    ) {
      return;
    }

    setActing(item.id);

    try {
      const result =
        await sendRecoveryAction(
          item.paymentId,
          item.recommendedAction
        );

      console.log(
        'Recovery action result:',
        result
      );

      /*
       * Backend is the source of truth.
       * Reload MongoDB data after the action.
       */
      await retry();
    } catch (err) {
      console.error(
        'Recovery action failed:',
        err
      );

      alert(
        err instanceof Error
          ? err.message
          : 'Failed to take recovery action.'
      );
    } finally {
      setActing('');
    }
  };

  const getActionLabel = (
    recommendedAction:
      | RecoveryCase['recommendedAction']
      | null
      | undefined
  ) => {
    switch (
      recommendedAction
    ) {
      case 'REMINDER':
        return 'Send payment reminder';

      case 'PAYMENT_METHOD_SUGGESTION':
        return 'Suggest another payment method';

      case 'SMART_RETRY':
        return 'Run smart retry';

      case 'SUPPORT_ESCALATION':
        return 'Escalate to support';

      case 'STOP':
        return 'No automated action';

      default:
        return 'Review recovery action';
    }
  };

  const getStatusLabel = (
    item: RecoveryCase
  ) => {
    if (
      item.recommendedAction ===
      'STOP'
    ) {
      return 'Protected by policy';
    }

    if (
      item.status ===
      'awaiting_customer'
    ) {
      return 'Customer action required';
    }

    if (
      item.status ===
      'recovered'
    ) {
      return 'Recovered';
    }

    if (
      item.status ===
      'failed'
    ) {
      return 'Recovery failed';
    }

    return 'Recovery in progress';
  };

  const getStatusClass = (
    item: RecoveryCase
  ) => {
    if (
      item.recommendedAction ===
      'STOP'
    ) {
      return 'bg-slate-100 text-slate-600 border-slate-200';
    }

    if (
      item.status ===
      'awaiting_customer'
    ) {
      return 'bg-warning-50 text-warning-700 border-warning-100';
    }

    if (
      item.status ===
      'recovered'
    ) {
      return 'bg-success-50 text-success-700 border-success-100';
    }

    if (
      item.status ===
      'failed'
    ) {
      return 'bg-danger-50 text-danger-700 border-danger-100';
    }

    return 'bg-brand-50 text-brand-700 border-brand-100';
  };

  return (
    <div className="animate-fade-in">

      <PageHeader
        eyebrow="Revenue recovery"
        title="Recovery Center"
        description="Recover revenue with AI-guided actions and bounded automation."
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              void retry()
            }
          >
            <RefreshCw className="h-4 w-4" />
            Refresh cases
          </Button>
        }
      />

      {/* =====================================================
          MONEY-FIRST STATS
      ===================================================== */}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">

        <StatCard
          label="Revenue at risk"
          value={formatINRCompact(
            activeAmountAtRisk
          )}
          icon={
            <Target className="h-4 w-4" />
          }
          iconClassName="bg-danger-50 text-danger-600"
        />

        <StatCard
          label="Revenue recovered"
          value={formatINRCompact(
            recoveredAmount
          )}
          icon={
            <CheckCircle2 className="h-4 w-4" />
          }
          iconClassName="bg-success-50 text-success-600"
        />

        <StatCard
          label="Recovery rate"
          value={`${recoveryRate}%`}
          icon={
            <TrendingUp className="h-4 w-4" />
          }
          iconClassName="bg-brand-50 text-brand-600"
        />

        <StatCard
          label="Cases needing attention"
          value={String(
            casesNeedingAttention
          )}
          icon={
            <ShieldAlert className="h-4 w-4" />
          }
          iconClassName="bg-warning-50 text-warning-600"
        />

      </div>

      {/* =====================================================
          CONTEXT BANNER
      ===================================================== */}

      {activeCases.length > 0 && (
        <Card className="mb-6">
          <CardBody>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

              <div className="flex items-start gap-3">
                <div className="h-9 w-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                  <Sparkles className="h-4 w-4" />
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    RecoverAI is prioritizing the highest-value recovery opportunities.
                  </p>

                  <p className="text-xs text-slate-500 mt-1">
                    AI predicts recovery likelihood, selects an intervention, and policy controls how far automation can go.
                  </p>
                </div>
              </div>

              <div className="text-left md:text-right shrink-0">
                <p className="text-xs text-slate-400">
                  Active exposure
                </p>

                <p className="text-lg font-bold text-slate-800">
                  {formatINRCompact(
                    activeAmountAtRisk
                  )}
                </p>
              </div>

            </div>
          </CardBody>
        </Card>
      )}

      {/* =====================================================
          RECOVERY CASES
      ===================================================== */}

      <div className="flex items-center justify-between mb-3">

        <div>
          <h2 className="text-sm font-semibold text-slate-800">
            Recovery cases
          </h2>

          <p className="text-xs text-slate-400 mt-0.5">
            Cases requiring recovery decisions or customer action
          </p>
        </div>

        <span className="text-xs text-slate-400">
          {activeCases.length} active
        </span>

      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

        {cases.map(
          (item) => {

            const isWorking =
              acting === item.id;

            const isCompleted =
              item.status ===
                'recovered' ||
              item.status ===
                'failed';

            const isStop =
              item.recommendedAction ===
              'STOP';

            const isWaiting =
              item.status ===
              'awaiting_customer';

            const canAct =
              !isWorking &&
              !isCompleted &&
              !isStop &&
              Boolean(
                item.paymentId &&
                item.recommendedAction
              );

            return (
              <Card
                key={item.id}
                hover
                className={
                  isStop
                    ? 'border-slate-200'
                    : ''
                }
              >
                <CardBody>

                  {/* CUSTOMER + STATUS */}

                  <div className="flex items-start justify-between gap-3">

                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800 truncate">
                        {item.customerName}
                      </p>

                      <p className="text-xs text-slate-400 mt-0.5">
                        {item.id}
                        {item.lastUpdated &&
                          ` · ${timeAgo(
                            item.lastUpdated
                          )}`}
                      </p>
                    </div>

                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold whitespace-nowrap ${getStatusClass(
                        item
                      )}`}
                    >
                      {getStatusLabel(
                        item
                      )}
                    </span>

                  </div>

                  {/* AMOUNT */}

                  <div className="my-5">

                    <p className="text-xs text-slate-500">
                      Amount at risk
                    </p>

                    <p className="text-2xl font-bold text-slate-800 mt-1">
                      {formatINR(
                        item.amountAtRisk
                      )}
                    </p>

                  </div>

                  {/* AI RECOMMENDATION */}

                  <div
                    className={`rounded-lg p-3 mb-4 border ${
                      isStop
                        ? 'bg-slate-50 border-slate-200'
                        : isWaiting
                        ? 'bg-warning-50 border-warning-100'
                        : 'bg-brand-50 border-brand-100'
                    }`}
                  >

                    <div className="flex items-start gap-2.5">

                      <div
                        className={`mt-0.5 ${
                          isStop
                            ? 'text-slate-500'
                            : isWaiting
                            ? 'text-warning-600'
                            : 'text-brand-600'
                        }`}
                      >
                        {isStop ? (
                          <ShieldAlert className="h-4 w-4" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                      </div>

                      <div className="min-w-0">

                        <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                          {isStop
                            ? 'Policy protection'
                            : 'AI recommendation'}
                        </p>

                        <p className="text-xs font-semibold text-slate-800 mt-1">
                          {getActionLabel(
                            item.recommendedAction
                          )}
                        </p>

                        {isWaiting && (
                          <p className="text-[11px] text-warning-700 mt-1">
                            The next step depends on the customer rather than another automated retry.
                          </p>
                        )}

                        {isStop && (
                          <p className="text-[11px] text-slate-500 mt-1">
                            Automation is stopped to prevent repeated payment attempts.
                          </p>
                        )}

                      </div>

                    </div>

                  </div>

                  {/* CONFIDENCE */}

                  {!isStop && (
                    <div className="bg-slate-50 rounded-lg p-3 mb-4">

                      <div className="flex items-center justify-between mb-2">

                        <span className="text-xs text-slate-500">
                          AI confidence
                        </span>

                        <span
                          className={`text-xs font-semibold ${getProbabilityColor(
                            item.recoveryProbability
                          )}`}
                        >
                          {item.recoveryProbability}%
                        </span>

                      </div>

                      <ProbabilityBar
                        probability={
                          item.recoveryProbability
                        }
                        showLabel={false}
                        size="sm"
                      />

                    </div>
                  )}

                  {/* POLICY STOP */}

                  {isStop && (
                    <div className="flex items-center justify-between rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 mb-4">

                      <div>
                        <p className="text-[10px] uppercase tracking-wide text-slate-400">
                          Automation limit
                        </p>

                        <p className="text-xs font-semibold text-slate-700 mt-0.5">
                          {Math.min(
                            item.attempts,
                            3
                          )} / 3 attempts used
                        </p>
                      </div>

                      <ShieldAlert className="h-4 w-4 text-slate-400" />

                    </div>
                  )}

                  {/* REASONING */}

                  <details className="group mb-4">

                    <summary className="cursor-pointer list-none flex items-center justify-between text-xs font-medium text-slate-500 hover:text-slate-700">

                      <span>
                        View reasoning
                      </span>

                      <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" />

                    </summary>

                    <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-2 gap-3">

                      <div>
                        <p className="text-[10px] uppercase tracking-wide text-slate-400">
                          Failure reason
                        </p>

                        <p className="text-xs font-medium text-slate-700 mt-1">
                          {item.failureReason ||
                            'Not provided'}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wide text-slate-400">
                          Attempts
                        </p>

                        <p className="text-xs font-medium text-slate-700 mt-1">
                          {item.attempts}
                        </p>
                      </div>

                    </div>

                  </details>

                  {/* ACTION */}

                  <Button
                    className="w-full"
                    size="sm"
                    loading={isWorking}
                    disabled={
                      !canAct
                    }
                    onClick={() =>
                      void action(item)
                    }
                  >

                    {isWorking ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        Processing...
                      </>
                    ) : isStop ? (
                      <>
                        <ShieldAlert className="h-3.5 w-3.5" />
                        No automated action
                      </>
                    ) : item.status ===
                      'recovered' ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Recovered
                      </>
                    ) : item.status ===
                      'failed' ? (
                      <>
                        <ShieldAlert className="h-3.5 w-3.5" />
                        Recovery failed
                      </>
                    ) : item.recommendedAction ===
                      'REMINDER' ? (
                      <>
                        Send reminder
                        <ArrowRight className="h-3.5 w-3.5" />
                      </>
                    ) : item.recommendedAction ===
                      'PAYMENT_METHOD_SUGGESTION' ? (
                      <>
                        Suggest payment method
                        <ArrowRight className="h-3.5 w-3.5" />
                      </>
                    ) : (
                      <>
                        Take action
                        <ArrowRight className="h-3.5 w-3.5" />
                      </>
                    )}

                  </Button>

                </CardBody>
              </Card>
            );
          }
        )}

      </div>

      {/* =====================================================
          EMPTY STATE
      ===================================================== */}

      {activeCases.length === 0 && (
        <Card className="mt-4">

          <EmptyState
            title="All caught up"
            description="There are no active recovery cases right now."
            icon={
              <CheckCircle2 className="h-6 w-6" />
            }
          />

        </Card>
      )}

    </div>
  );
}


/* =========================================================
   ANALYTICS PAGE
========================================================= */

export function AnalyticsPage() {
  const {
    data,
    loading,
    error,
    retry,
  } = useAsync(getAnalytics);

  const {
    data: benchmark,
    loading: benchmarkLoading,
    error: benchmarkError,
    retry: retryBenchmark,
  } = useAsync(
    () => getRecoveryBenchmark(250, 2026),
  );

  if (loading) {
    return (
      <PageLoading title="Analytics" />
    );
  }

  if (error || !data) {
    return (
      <ErrorState
        message="Unable to load analytics"
        onRetry={retry}
      />
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Analytics"
        description="Measure recovery performance and identify improvement opportunities."
        action={
          <Button
            variant="outline"
            size="sm"
          >
            <Download className="h-4 w-4" />
            Export report
          </Button>
        }
      />

      {/* =====================================================
          RECOVERY BENCHMARK
      ===================================================== */}

      {benchmarkLoading && (
        <Card className="mb-6">
          <CardBody className="py-8">
            <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin" />

              Loading recovery benchmark...
            </div>
          </CardBody>
        </Card>
      )}

      {!benchmarkLoading &&
        benchmark &&
        !benchmarkError && (
          <RecoveryBenchmarkCard
            benchmark={benchmark}
            onRetry={() =>
              void retryBenchmark()
            }
          />
        )}

      {!benchmarkLoading &&
        benchmarkError && (
          <Card className="mb-6">
            <CardBody>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Recovery benchmark unavailable
                  </p>

                  <p className="text-xs text-slate-500 mt-1">
                    Standard analytics are still available.
                  </p>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    void retryBenchmark()
                  }
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Retry benchmark
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

      {/* =====================================================
          EXISTING ANALYTICS
      ===================================================== */}

      <AnalyticsContent
        data={data}
      />
    </div>
  );
}


/* =========================================================
   ANALYTICS CONTENT
========================================================= */

function AnalyticsContent({
  data,
}: {
  data: AnalyticsData;
}) {

  const methodItems =
    data.recoveryByMethod.map(
      (item, index) => ({
        label: item.method,
        value: item.recovered,
        color: [
          '#3b82f6',
          '#10b981',
          '#f59e0b',
          '#8b5cf6',
          '#ef4444',
          '#0ea5e9',
        ][index % 6],
      })
    );


  return (
    <div className="animate-fade-in">

      <PageHeader
        title="Analytics"
        description="Measure recovery performance and identify improvement opportunities."
        action={
          <Button
            variant="outline"
            size="sm"
          >
            <Download className="h-4 w-4" />
            Export report
          </Button>
        }
      />


      {/* =====================================================
          STATS
      ===================================================== */}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">

        <StatCard
          label="Revenue at risk"
          value={formatINRCompact(
            data.revenueAtRisk
          )}
          icon={
            <Target className="h-4 w-4" />
          }
          iconClassName="bg-warning-50 text-warning-600"
        />

        <StatCard
          label="Revenue recovered"
          value={formatINRCompact(
            data.revenueRecovered
          )}
          icon={
            <CircleDollarSign className="h-4 w-4" />
          }
          iconClassName="bg-success-50 text-success-600"
        />

        <StatCard
          label="Recovery rate"
          value={`${data.recoveryRate}%`}
          icon={
            <TrendingUp className="h-4 w-4" />
          }
          iconClassName="bg-brand-50 text-brand-600"
        />

        <StatCard
          label="Successful recoveries"
          value={data.successfulRecoveries.toLocaleString(
            'en-IN'
          )}
          icon={
            <CheckCircle2 className="h-4 w-4" />
          }
          iconClassName="bg-success-50 text-success-600"
        />

      </div>


      {/* =====================================================
          CHARTS
      ===================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">

        <Card className="xl:col-span-2">

          <CardHeader
            title="Recovery performance over time"
            subtitle="Revenue recovered vs revenue at risk"
          />

          <CardBody>

            <RevenueChart
              data={
                data.performanceOverTime
              }
              height={260}
            />

          </CardBody>

        </Card>


        <Card>

          <CardHeader
            title="Recovery by payment method"
            subtitle="Recovered revenue distribution"
          />

          <CardBody>

            <div className="flex items-center justify-center">

              <DonutChart
                items={methodItems}
                size={170}
                centerValue={formatINRCompact(
                  data.revenueRecovered
                )}
                centerLabel="recovered"
              />

            </div>


            <div className="space-y-2 mt-4">

              {data.recoveryByMethod.map(
                (item) => (

                  <div
                    key={item.method}
                    className="flex items-center justify-between text-xs"
                  >

                    <span className="text-slate-600">
                      {item.method}
                    </span>

                    <span className="font-medium text-slate-700">
                      {formatINR(
                        item.recovered
                      )}
                    </span>

                  </div>

                )
              )}

            </div>

          </CardBody>

        </Card>

      </div>


      {/* =====================================================
          RECOVERY BY FAILURE REASON
      ===================================================== */}

      <Card>

        <CardHeader
          title="Recovery by failure reason"
          subtitle="Which issues are most recoverable"
        />

        <div className="overflow-x-auto">

          <table className="w-full text-left">

            <thead>

              <tr className="border-b border-slate-100 text-[10px] uppercase tracking-wider text-slate-400">

                <th className="px-5 py-3 font-medium">
                  Failure reason
                </th>

                <th className="px-5 py-3 font-medium">
                  Attempted
                </th>

                <th className="px-5 py-3 font-medium">
                  Recovered
                </th>

                <th className="px-5 py-3 font-medium">
                  Recovery rate
                </th>

                <th className="px-5 py-3 font-medium">
                  Progress
                </th>

              </tr>

            </thead>


            <tbody>

              {data.recoveryByReason.map(
                (item) => {

                  const rate =
                    item.attempted > 0
                      ? Math.round(
                          (item.recovered /
                            item.attempted) *
                            100
                        )
                      : 0;

                  return (

                    <tr
                      key={item.reason}
                      className="border-b border-slate-50"
                    >

                      <td className="px-5 py-3 text-sm font-medium text-slate-700">

                        <div className="flex items-center gap-2">

                          <span
                            className="h-2 w-2 rounded-full"
                            style={{
                              backgroundColor:
                                getFailureReasonColor(
                                  item.reason
                                ),
                            }}
                          />

                          {item.reason}

                        </div>

                      </td>

                      <td className="px-5 py-3 text-sm text-slate-600">
                        {formatINR(
                          item.attempted
                        )}
                      </td>

                      <td className="px-5 py-3 text-sm font-semibold text-success-600">
                        {formatINR(
                          item.recovered
                        )}
                      </td>

                      <td className="px-5 py-3 text-sm font-medium text-slate-700">
                        {rate}%
                      </td>

                      <td className="px-5 py-3 w-52">

                        <ProbabilityBar
                          probability={rate}
                          showLabel={false}
                          size="sm"
                        />

                      </td>

                    </tr>

                  );
                }
              )}

            </tbody>

          </table>

        </div>

      </Card>

    </div>
  );
}