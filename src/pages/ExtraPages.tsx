import { PageHeader } from '@/components/ui/PageHeader';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type MouseEvent,
} from 'react';

import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';

import {
  ArrowLeft,
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  LockKeyhole,
  Mail,
  Moon,
  Sun,
  MessageSquare,
  Mic,
  MicOff,
  Send,
  Sparkles,
  UserRound,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';

import {
  Card,
  CardBody,
  CardHeader,
} from '@/components/ui/Card';

import {
  Input,
  Toggle,
} from '@/components/ui/Input';

import {
  Badge,
  StatusBadge,
} from '@/components/ui/Badge';

import {
  ErrorState,
  Spinner,
} from '@/components/ui/States';

import { ProbabilityBar } from '@/components/ui/ProbabilityBar';

import {
  getPaymentDetails,
  getSettings,
  requestPasswordReset,
  resetPassword,
  sendRecoveryAction,
  sendAIMessage,
  updateSettings,
} from '@/services/api';

import type {
  AIResponse,
  ChatMessage,
  MerchantSettings,
  Payment,
} from '@/types';

import {
  formatDateTime,
  formatINR,
  getProbabilityColor,
} from '@/utils/format';


/* =========================================================
   LOGIN PAGE
========================================================= */

export function LoginPage() {
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [forgotMode, setForgotMode] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  const [showDemoModal, setShowDemoModal] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();

    setError('');

    const cleanEmail = email.trim();

    if (!cleanEmail || !password) {
      setError(
        'Enter your email and password to continue.',
      );

      return;
    }

    setLoading(true);

    try {
      await login(cleanEmail, password);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to sign in. Please check your credentials.',
      );
    } finally {
      setLoading(false);
    }
  };

  const requestReset = async (e: FormEvent) => {
    e.preventDefault();

    setError('');

    const cleanEmail = email.trim();

    if (!cleanEmail) {
      setError('Enter your work email to reset your password.');
      return;
    }

    setResetLoading(true);

    try {
      await requestPasswordReset(cleanEmail);
      setResetSent(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to start the password reset. Please try again.',
      );
    } finally {
      setResetLoading(false);
    }
  };

  const openForgotPassword = () => {
    setError('');
    setResetSent(false);
    setForgotMode(true);
  };

  const backToLogin = () => {
    setError('');
    setResetSent(false);
    setForgotMode(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* =====================================================
          LEFT BRAND PANEL
      ===================================================== */}

      <div className="hidden lg:flex lg:w-1/2 bg-brand-950 relative overflow-hidden p-12 flex-col justify-between">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              'radial-gradient(#93c5fd 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />

        <div className="relative flex items-center gap-2 text-white">
          <div className="h-9 w-9 rounded-lg bg-brand-500 flex items-center justify-center">
            <Sparkles className="h-5 w-5" />
          </div>

          <span className="font-bold text-xl">
            Recover
            <span className="text-brand-300">
              AI
            </span>
          </span>
        </div>

        <div className="relative max-w-md">
          <p className="text-brand-200 text-sm font-medium mb-4">
            REVENUE RECOVERY, REIMAGINED
          </p>

          <h1 className="text-4xl xl:text-5xl font-bold text-white tracking-tight leading-tight">
            Turn failed payments into recovered revenue.
          </h1>

          <p className="text-brand-200 mt-6 leading-relaxed">
            A clearer view of payment risk, a smarter path to recovery,
            and more revenue for your business.
          </p>

          <div className="mt-10 flex items-center gap-6">
            <div>
              <p className="text-2xl font-bold text-white">
                72.4%
              </p>

              <p className="text-xs text-brand-300 mt-1">
                Average recovery rate
              </p>
            </div>

            <div className="h-8 w-px bg-brand-800" />

            <div>
              <p className="text-2xl font-bold text-white">
                ₹6.12L
              </p>

              <p className="text-xs text-brand-300 mt-1">
                Revenue recovered
              </p>
            </div>
          </div>
        </div>

        <p className="relative text-xs text-brand-400">
          © 2026 RecoverAI · Built for modern merchants
        </p>
      </div>

      {/* =====================================================
          AUTH FORM
      ===================================================== */}

      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-sm">

          <div className="lg:hidden flex items-center gap-2 mb-12">
            <div className="h-9 w-9 rounded-lg bg-brand-600 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-white" />
            </div>

            <span className="font-bold text-xl text-slate-800">
              Recover
              <span className="text-brand-600">
                AI
              </span>
            </span>
          </div>

          <div className="mb-8">
            <div className="h-10 w-10 bg-brand-50 rounded-lg flex items-center justify-center text-brand-600 mb-5">
              <LockKeyhole className="h-5 w-5" />
            </div>

            <h2 className="text-2xl font-bold text-slate-900">
              {forgotMode ? 'Reset your password' : 'Welcome back'}
            </h2>

            <p className="text-sm text-slate-500 mt-2">
              {forgotMode
                ? 'Enter your work email and we will send you a secure reset link.'
                : 'Sign in to your RecoverAI workspace.'}
            </p>
          </div>

          {forgotMode ? (
            <form
              onSubmit={requestReset}
              className="space-y-5"
            >
              <Input
                label="Work email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError('');
                  setResetSent(false);
                }}
                placeholder="you@company.com"
                icon={
                  <Mail className="h-4 w-4" />
                }
                disabled={resetLoading || resetSent}
              />

              {resetSent && (
                <div
                  role="status"
                  className="rounded-lg border border-success-100 bg-success-50 px-3 py-3 text-sm text-success-700"
                >
                  If an account exists for this email, a password reset link has been sent. Check your inbox and spam folder.
                </div>
              )}

              {error && (
                <div
                  role="alert"
                  className="rounded-lg border border-danger-100 bg-danger-50 px-3 py-2.5 text-sm text-danger-700"
                >
                  {error}
                </div>
              )}

              {!resetSent && (
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  loading={resetLoading}
                  disabled={resetLoading}
                >
                  {resetLoading
                    ? 'Sending reset link...'
                    : 'Send reset link'}
                </Button>
              )}

              <button
                type="button"
                onClick={backToLogin}
                className="w-full text-sm text-brand-600 hover:text-brand-700 font-medium"
              >
                ← Back to sign in
              </button>
            </form>
          ) : (
            <form
              onSubmit={submit}
              className="space-y-5"
            >
              <Input
                label="Work email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError('');
                }}
                placeholder="you@company.com"
                icon={
                  <Mail className="h-4 w-4" />
                }
                disabled={loading}
              />

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium text-slate-700">
                    Password
                  </label>

                  <button
                    type="button"
                    disabled={loading}
                    onClick={openForgotPassword}
                    className="text-xs text-brand-600 hover:text-brand-700 disabled:opacity-50"
                  >
                    Forgot password?
                  </button>
                </div>

                <Input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError('');
                  }}
                  placeholder="Enter your password"
                  disabled={loading}
                />
              </div>

              {error && (
                <div
                  role="alert"
                  className="rounded-lg border border-danger-100 bg-danger-50 px-3 py-2.5 text-sm text-danger-700"
                >
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                size="lg"
                loading={loading}
                disabled={loading}
              >
                {loading
                  ? 'Signing in...'
                  : 'Sign in'}

                {!loading && (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            </form>
          )}

          {!forgotMode && (
            <>
              <p className="text-center text-xs text-slate-400 mt-8">
                New to RecoverAI?{' '}
                <button
                  type="button"
                  onClick={() =>
                    setShowDemoModal(true)
                  }
                  className="text-brand-600 font-medium hover:text-brand-700 hover:underline"
                >
                  Request a demo
                </button>
              </p>

              <p className="text-center text-[10px] text-slate-400 mt-12">
                Secure access powered by RecoverAI
              </p>
            </>
          )}
        </div>
      </div>

      {showDemoModal && (
        <RequestDemoModal
          onClose={() =>
            setShowDemoModal(false)
          }
        />
      )}
    </div>
  );
}


/* =========================================================
   RESET PASSWORD PAGE
========================================================= */

export function ResetPasswordPage() {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setToken(params.get('reset_token') || '');
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('This password reset link is missing or invalid.');
      return;
    }

    if (password.length < 8) {
      setError('Your new password must be at least 8 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to reset your password. Please request a new link.',
      );
    } finally {
      setLoading(false);
    }
  };

  const goToLogin = () => {
    window.history.replaceState({}, '', '/');
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-10">
          <div className="h-9 w-9 rounded-lg bg-brand-600 flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-xl text-slate-800">
            Recover<span className="text-brand-600">AI</span>
          </span>
        </div>

        <Card>
          <CardHeader
            title={success ? 'Password updated' : 'Create a new password'}
          />
          <CardBody>
            {success ? (
              <div className="space-y-5">
                <div className="rounded-lg border border-success-100 bg-success-50 px-3 py-3 text-sm text-success-700">
                  Your password has been updated successfully. You can now sign in with your new password.
                </div>

                <Button
                  className="w-full"
                  size="lg"
                  onClick={goToLogin}
                >
                  Back to sign in
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <form
                onSubmit={submit}
                className="space-y-5"
              >
                <p className="text-sm text-slate-500 leading-relaxed">
                  Choose a new password for your RecoverAI account.
                </p>

                <Input
                  label="New password"
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError('');
                  }}
                  placeholder="At least 8 characters"
                  disabled={loading}
                />

                <Input
                  label="Confirm new password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setError('');
                  }}
                  placeholder="Re-enter your password"
                  disabled={loading}
                />

                {error && (
                  <div
                    role="alert"
                    className="rounded-lg border border-danger-100 bg-danger-50 px-3 py-2.5 text-sm text-danger-700"
                  >
                    {error}
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  loading={loading}
                  disabled={loading || !token}
                >
                  {loading ? 'Updating password...' : 'Update password'}
                </Button>

                <button
                  type="button"
                  onClick={goToLogin}
                  className="w-full text-sm text-brand-600 hover:text-brand-700 font-medium"
                >
                  ← Back to sign in
                </button>
              </form>
            )}
          </CardBody>
        </Card>

        <p className="text-center text-[10px] text-slate-400 mt-8">
          Secure password recovery powered by RecoverAI
        </p>
      </div>
    </div>
  );
}


/* =========================================================
   REQUEST DEMO MODAL
========================================================= */

function RequestDemoModal({
  onClose,
}: {
  onClose: () => void;
}) {
  const { requestDemo } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');

  /*
   * Password belongs to the merchant account.
   * It must NOT be stored inside DemoRequest.
   */
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const submitDemoRequest = async (
    e: FormEvent,
  ) => {
    e.preventDefault();

    setError('');

    const cleanName = name.trim();
    const cleanEmail = email.trim();
    const cleanCompany = company.trim();

    if (!cleanName) {
      setError('Please enter your name.');
      return;
    }

    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }

    if (!cleanCompany) {
      setError('Please enter your company name.');
      return;
    }

    if (!password) {
      setError('Please create a password.');
      return;
    }

    if (password.length < 8) {
      setError(
        'Password must be at least 8 characters long.',
      );
      return;
    }

    if (!confirmPassword) {
      setError('Please confirm your password.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await requestDemo(
        cleanName,
        cleanEmail,
        cleanCompany,
        password,
        confirmPassword,
      );

      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to create your RecoverAI account.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >

      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl max-h-[90vh] overflow-y-auto">

        {/* HEADER */}

        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">

          <div>

            <h2 className="text-lg font-bold text-slate-900">
              Create your RecoverAI account
            </h2>

            <p className="text-xs text-slate-500 mt-1">
              Start your demo workspace and set your password.
            </p>

          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>

        </div>


        {/* SUCCESS */}

        {success ? (

          <div className="px-6 py-10 text-center">

            <div className="mx-auto h-14 w-14 rounded-full bg-success-100 text-success-600 flex items-center justify-center">

              <CheckCircle2 className="h-7 w-7" />

            </div>


            <h3 className="text-lg font-bold text-slate-900 mt-5">
              Account created successfully
            </h3>


            <p className="text-sm text-slate-500 mt-2 leading-relaxed">

              Your RecoverAI account is ready.
              You have been signed in automatically.

            </p>


            <p className="text-xs text-slate-400 mt-3">

              Account:
              <span className="font-medium text-slate-600 ml-1">
                {email}
              </span>

            </p>


            <Button
              className="mt-6"
              onClick={onClose}
            >
              Continue to RecoverAI
            </Button>

          </div>

        ) : (

          <form
            onSubmit={submitDemoRequest}
            className="p-6 space-y-4"
          >

            {/* NAME */}

            <Input
              label="Your name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              placeholder="Rajesh Kumar"
              icon={
                <UserRound className="h-4 w-4" />
              }
              disabled={loading}
            />


            {/* EMAIL */}

            <Input
              label="Work email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError('');
              }}
              placeholder="you@company.com"
              icon={
                <Mail className="h-4 w-4" />
              }
              disabled={loading}
            />


            {/* COMPANY */}

            <Input
              label="Company name"
              value={company}
              onChange={(e) => {
                setCompany(e.target.value);
                setError('');
              }}
              placeholder="ShopKart"
              disabled={loading}
            />


            {/* PASSWORD */}

            <Input
              label="Create password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError('');
              }}
              placeholder="At least 8 characters"
              disabled={loading}
            />

            <p className="text-[10px] text-slate-400 -mt-2">
              Use at least 8 characters. Your password is stored securely as a hash.
            </p>


            {/* CONFIRM PASSWORD */}

            <Input
              label="Confirm password"
              type="password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setError('');
              }}
              placeholder="Re-enter your password"
              disabled={loading}
            />


            {/* ERROR */}

            {error && (
              <div
                role="alert"
                className="rounded-lg border border-danger-100 bg-danger-50 px-3 py-2.5 text-sm text-danger-700"
              >
                {error}
              </div>
            )}


            {/* SUBMIT */}

            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
              disabled={loading}
            >

              {loading
                ? 'Creating account...'
                : 'Create account'}

              {!loading && (
                <ChevronRight className="h-4 w-4" />
              )}

            </Button>


            <p className="text-[10px] text-center text-slate-400">
              Your password is never emailed or stored in the demo request record.
            </p>

          </form>

        )}

      </div>

    </div>
  );
}


/* =========================================================
   PAYMENT DETAILS PAGE
========================================================= */

export function PaymentDetailsPage({
  id,
  onBack,
}: {
  id: string;
  onBack: () => void;
}) {

  const {
    data,
    loading,
    error,
    retry,
  } = usePayment(id);

  const [acting, setActing] =
    useState(false);

  const [actionError, setActionError] =
    useState('');


  const takeRecommendedAction = async () => {

    if (
      !data ||
      data.recommendedAction === 'STOP'
    ) {
      return;
    }


    setActing(true);
    setActionError('');


    try {

      const result =
        await sendRecoveryAction(
          data.id,
          data.recommendedAction,
        );


      if (!result.success) {

        throw new Error(
          result.result?.message ||
            result.result?.aiExplanation?.nextStep ||
            'The recovery action could not be completed.',
        );

      }


      await retry();

    } catch (err) {

      setActionError(
        err instanceof Error
          ? err.message
          : 'The recovery action could not be completed.',
      );

    } finally {

      setActing(false);

    }
  };


  if (loading) {
    return <Spinner />;
  }


  if (error || !data) {

    return (
      <ErrorState
        message="Payment not found"
        onRetry={onBack}
      />
    );

  }


  return (
    <div className="animate-fade-in">

      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-5"
      >

        <ArrowLeft className="h-4 w-4" />

        Back to payments

      </button>


      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">

        <div>

          <p className="text-xs text-brand-600 font-medium">
            {data.id}
          </p>

          <h1 className="text-2xl font-bold text-slate-900 mt-1">
            Payment details
          </h1>

          <p className="text-sm text-slate-500 mt-1">
            Created {formatDateTime(data.createdAt)}
          </p>

        </div>

        <StatusBadge status={data.status} />

      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* LEFT */}

        <div className="lg:col-span-2 space-y-4">

          {/* TRANSACTION OVERVIEW */}

          <Card>

            <CardHeader title="Transaction overview" />

            <CardBody>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">

                <div>

                  <p className="text-xs text-slate-400">
                    Amount
                  </p>

                  <p className="text-lg font-bold text-slate-800 mt-1">
                    {formatINR(data.amount)}
                  </p>

                </div>


                <div>

                  <p className="text-xs text-slate-400">
                    Customer
                  </p>

                  <p className="text-sm font-semibold text-slate-700 mt-1">
                    {data.customerName}
                  </p>

                  <p className="text-xs text-slate-400 mt-0.5">
                    {data.customerEmail}
                  </p>

                </div>


                <div>

                  <p className="text-xs text-slate-400">
                    Payment method
                  </p>

                  <p className="text-sm font-semibold text-slate-700 mt-1">
                    {data.paymentMethod}
                  </p>

                </div>


                <div>

                  <p className="text-xs text-slate-400">
                    Failure reason
                  </p>

                  <p className="text-sm font-semibold text-slate-700 mt-1">
                    {data.failureReason || 'None'}
                  </p>

                </div>

              </div>

            </CardBody>

          </Card>


          {/* RECOVERY TIMELINE */}

          <Card>

            <CardHeader
              title="Recovery timeline"
              subtitle="Every step in this payment's lifecycle"
            />

            <CardBody>

              <div className="space-y-0 max-w-xl">

                {data.timeline.map(
                  (event, i) => (

                    <div
                      key={event.id}
                      className="flex gap-4"
                    >

                      <div className="flex flex-col items-center">

                        <div
                          className={`h-8 w-8 rounded-full flex items-center justify-center ${
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

                            <CheckCircle2 className="h-4 w-4" />

                          ) : event.status ===
                            'current' ? (

                            <Clock3 className="h-4 w-4" />

                          ) : (

                            <div className="h-2 w-2 rounded-full bg-current" />

                          )}

                        </div>


                        {i <
                          data.timeline.length -
                            1 && (

                          <div className="w-px h-10 bg-slate-200" />

                        )}

                      </div>


                      <div className="pb-6">

                        <p
                          className={`text-sm font-semibold ${
                            event.status ===
                            'pending'
                              ? 'text-slate-400'
                              : 'text-slate-800'
                          }`}
                        >
                          {event.title}
                        </p>

                        <p className="text-xs text-slate-500 mt-1">
                          {event.description}
                        </p>

                        {event.timestamp && (

                          <p className="text-[10px] text-slate-400 mt-1">
                            {formatDateTime(
                              event.timestamp,
                            )}
                          </p>

                        )}

                      </div>

                    </div>

                  ),
                )}

              </div>

            </CardBody>

          </Card>


          {/* PREVIOUS ATTEMPTS */}

          <Card>

            <CardHeader title="Previous attempts" />

            <div className="overflow-x-auto">

              <table className="w-full text-left">

                <thead>

                  <tr className="border-b border-slate-100 text-[10px] uppercase text-slate-400">

                    <th className="px-5 py-3">
                      Attempt
                    </th>

                    <th className="px-5 py-3">
                      Method
                    </th>

                    <th className="px-5 py-3">
                      Amount
                    </th>

                    <th className="px-5 py-3">
                      Status
                    </th>

                    <th className="px-5 py-3">
                      Time
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {data.attempts.map(
                    (attempt) => (

                      <tr
                        key={attempt.id}
                        className="border-b border-slate-50"
                      >

                        <td className="px-5 py-3 text-sm text-slate-700">
                          #{attempt.attemptNumber}
                        </td>

                        <td className="px-5 py-3 text-xs text-slate-500">
                          {attempt.method}
                        </td>

                        <td className="px-5 py-3 text-sm text-slate-700">
                          {formatINR(
                            attempt.amount,
                          )}
                        </td>

                        <td className="px-5 py-3">

                          <StatusBadge
                            status={
                              attempt.status ===
                              'Success'
                                ? 'Successful'
                                : attempt.status ===
                                  'Failed'
                                  ? 'Failed'
                                  : 'Recovering'
                            }
                          />

                        </td>

                        <td className="px-5 py-3 text-xs text-slate-400">
                          {formatDateTime(
                            attempt.timestamp,
                          )}
                        </td>

                      </tr>

                    ),
                  )}

                </tbody>

              </table>

            </div>

          </Card>

        </div>


        {/* RIGHT */}

        <div className="space-y-4">

          {/* AI RECOMMENDATION */}

          <Card className="border-brand-100">

            <CardBody>

              <div className="flex items-center gap-2 text-brand-700 mb-4">

                <Sparkles className="h-4 w-4" />

                <h3 className="text-sm font-semibold">
                  AI recommendation
                </h3>

              </div>


              <p className="text-sm font-semibold text-slate-800">
                {data.recommendedAction}
              </p>


              <p className="text-xs text-slate-500 leading-relaxed mt-2">
                Based on this customer's payment history and
                the current failure reason, this is the
                recommended next best action.
              </p>


              <div className="mt-4 bg-brand-50 rounded-lg p-3">

                <div className="flex justify-between mb-2">

                  <span className="text-xs text-brand-700">
                    Recovery probability
                  </span>

                  <span
                    className={`text-xs font-bold ${getProbabilityColor(
                      data.recoveryProbability,
                    )}`}
                  >
                    {data.recoveryProbability}%
                  </span>

                </div>


                <ProbabilityBar
                  probability={
                    data.recoveryProbability
                  }
                  showLabel={false}
                  size="sm"
                />

              </div>


              {actionError && (

                <div className="mt-3 rounded-lg border border-danger-100 bg-danger-50 px-3 py-2 text-xs text-danger-700">
                  {actionError}
                </div>

              )}


              <Button
                className="w-full mt-4"
                loading={acting}
                disabled={
                  acting ||
                  data.status === 'recovered' ||
                  data.status === 'successful' ||
                  data.status === 'failed' ||
                  data.recommendedAction === 'STOP'
                }
                onClick={() =>
                  void takeRecommendedAction()
                }
              >

                {acting
                  ? 'Processing...'
                  : data.recommendedAction ===
                    'STOP'
                    ? 'No action required'
                    : data.status ===
                      'recovered'
                      ? 'Recovered'
                      : 'Take recommended action'}

              </Button>

            </CardBody>

          </Card>


          {/* CUSTOMER */}

          <Card>

            <CardHeader title="Customer information" />

            <CardBody>

              <div className="flex items-center gap-3 mb-4">

                <div className="h-10 w-10 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center">

                  <UserRound className="h-5 w-5" />

                </div>


                <div>

                  <p className="text-sm font-semibold text-slate-800">
                    {data.customerName}
                  </p>

                  <p className="text-xs text-slate-500">
                    {data.customerEmail}
                  </p>

                </div>

              </div>


              <div className="space-y-3 text-xs">

                <div className="flex justify-between">

                  <span className="text-slate-400">
                    Customer ID
                  </span>

                  <span className="text-slate-700 font-medium">
                    {data.customerId}
                  </span>

                </div>


                <div className="flex justify-between">

                  <span className="text-slate-400">
                    Total attempts
                  </span>

                  <span className="text-slate-700 font-medium">
                    {data.attempts.length}
                  </span>

                </div>

              </div>

            </CardBody>

          </Card>

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   PAYMENT HOOK
========================================================= */

function usePayment(id: string) {

  const [data, setData] =
    useState<Payment | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(false);


  const load = useCallback(
    async () => {

      setLoading(true);
      setError(false);

      try {

        const result =
          await getPaymentDetails(id);

        if (!result) {

          setError(true);

          return;
        }

        setData(result);

      } catch {

        setError(true);

      } finally {

        setLoading(false);

      }

    },
    [id],
  );


  useEffect(() => {
    void load();
  }, [load]);


  return {
    data,
    loading,
    error,
    retry: load,
  };
}


/* =========================================================
   AI ASSISTANT
========================================================= */

type StoredChatMessage = ChatMessage & {
  aiResponse?: AIResponse;
};

type Conversation = {
  id: string;
  title: string;
  messages: StoredChatMessage[];
  createdAt: string;
  updatedAt: string;
};


const starters = [
  'How much revenue did we recover?',
  'Why are payments failing?',
  'Which payments should we prioritize?',
  'What is our recovery rate?',
  'Show me high-value payments at risk.',
];


const WELCOME_MESSAGE: StoredChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hi. I'm ready to help you understand your payment recovery performance. Ask me about recovered revenue, failure patterns, or which payments to prioritize.",
  timestamp: new Date().toISOString(),
};


function getConversationalGreeting(text: string): string | null {

  const normalized = text
    .trim()
    .toLowerCase()
    .replace(/[!?.,]+$/g, '');

  if (/^(hi|hello|hey|hiya|good morning|good afternoon|good evening)$/.test(normalized)) {
    return "Hello! 👋 I'm your RecoverAI assistant. I can help you analyze recovered revenue, failed payments, revenue at risk, and recovery priorities. What would you like to check?";
  }

  if (/^(thanks|thank you|thx)$/.test(normalized)) {
    return "You're welcome! I’m here whenever you want to review your payment recovery performance.";
  }

  return null;
}


/* =========================================================
   CREATE CONVERSATION
========================================================= */

function createConversation(): Conversation {

  const now =
    new Date().toISOString();


  return {

    id:
      `conversation-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 8)}`,

    title:
      'New conversation',

    messages: [

      {
        ...WELCOME_MESSAGE,

        id:
          `welcome-${Date.now()}`,

        timestamp:
          now,
      },

    ],

    createdAt:
      now,

    updatedAt:
      now,

  };
}


/* =========================================================
   STRUCTURED AI DECISION CARD
========================================================= */

function AIInsightCard({
  response,
}: {
  response: AIResponse;
}) {

  const analysis =
    response.analysis;

  const priorityPayments =
    Array.isArray(response.payments)
      ? response.payments.slice(0, 4)
      : [];

  const failureReasons =
    Array.isArray(response.failureReasons)
      ? response.failureReasons
      : [];

  const probability =
    typeof analysis?.probability === 'number'
      ? analysis.probability
      : null;

  const recommendedAction =
    typeof analysis?.recommended_action === 'string'
      ? analysis.recommended_action
      : null;

  const previousAttempts =
    typeof analysis?.previous_attempts === 'number'
      ? analysis.previous_attempts
      : null;

  const failedAttempts =
    typeof analysis?.failed_attempts === 'number'
      ? analysis.failed_attempts
      : null;

  const reasoning =
    typeof analysis?.reasoning === 'string'
      ? analysis.reasoning
      : null;

  if (
    !analysis &&
    priorityPayments.length === 0 &&
    failureReasons.length === 0
  ) {
    return null;
  }

  return (
    <div className="mt-3 rounded-xl border border-brand-100 bg-white overflow-hidden">

      <div className="px-4 py-3 border-b border-slate-100 bg-brand-50/60 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-brand-600" />
        <span className="text-xs font-semibold text-slate-800">
          RecoverAI decision context
        </span>
      </div>

      <div className="p-4 space-y-4">

        {/* PRIORITY PAYMENTS */}

        {priorityPayments.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-2">
              Priority payments
            </p>

            <div className="space-y-2">
              {priorityPayments.map(
                (payment, index) => {
                  const paymentId =
                    typeof payment.payment_id === 'string'
                      ? payment.payment_id
                      : typeof payment.id === 'string'
                        ? payment.id
                        : `priority-${index}`;

                  const amount =
                    typeof payment.amount === 'number'
                      ? payment.amount
                      : null;

                  const paymentProbability =
                    typeof payment.probability === 'number'
                      ? payment.probability
                      : null;

                  const paymentAction =
                    typeof payment.recommended_action === 'string'
                      ? payment.recommended_action
                      : null;

                  return (
                    <div
                      key={`${paymentId}-${index}`}
                      className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2"
                    >
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-700 truncate">
                          {paymentId}
                        </p>

                        {paymentAction && (
                          <p className="text-[10px] text-slate-400 mt-0.5">
                            {paymentAction.replace(/_/g, ' ')}
                          </p>
                        )}
                      </div>

                      <div className="text-right shrink-0">
                        {amount !== null && (
                          <p className="text-xs font-semibold text-slate-800">
                            {formatINR(amount)}
                          </p>
                        )}

                        {paymentProbability !== null && (
                          <p className="text-[10px] text-brand-600">
                            {(paymentProbability * 100).toFixed(0)}% confidence
                          </p>
                        )}
                      </div>
                    </div>
                  );
                },
              )}
            </div>
          </div>
        )}

        {/* AI DECISION DETAILS */}

        {(probability !== null ||
          recommendedAction ||
          previousAttempts !== null ||
          failedAttempts !== null) && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">

            {probability !== null && (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-400">
                  Recovery confidence
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-800">
                  {(probability * 100).toFixed(0)}%
                </p>
              </div>
            )}

            {recommendedAction && (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-400">
                  Recommended action
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-800">
                  {recommendedAction.replace(/_/g, ' ')}
                </p>
              </div>
            )}

            {previousAttempts !== null && (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-400">
                  Previous attempts
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-800">
                  {previousAttempts}
                </p>
              </div>
            )}

            {failedAttempts !== null && (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-400">
                  Failed attempts
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-800">
                  {failedAttempts}
                </p>
              </div>
            )}

          </div>
        )}

        {/* REASONING */}

        {reasoning && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">
              Why
            </p>
            <p className="text-xs leading-relaxed text-slate-600">
              {reasoning}
            </p>
          </div>
        )}

        {/* FAILURE PATTERNS */}

        {failureReasons.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-2">
              Failure patterns
            </p>

            <div className="space-y-1.5">
              {failureReasons
                .slice(0, 5)
                .map((item, index) => {
                  const reason =
                    typeof item.reason === 'string'
                      ? item.reason
                      : typeof item.failure_reason === 'string'
                        ? item.failure_reason
                        : 'Unknown failure';

                  const count =
                    typeof item.count === 'number'
                      ? item.count
                      : '—';

                  return (
                    <div
                      key={index}
                      className="flex items-center justify-between text-xs text-slate-600"
                    >
                      <span>{reason}</span>

                      <span className="font-medium text-slate-800">
                        {count}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}


/* =========================================================
   AI ASSISTANT PAGE
========================================================= */

export function AssistantPage() {

  const { user } =
    useAuth();


  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [activeConversationId, setActiveConversationId] =
    useState('');

  const [input, setInput] =
    useState('');

  const [sending, setSending] =
    useState(false);

  const [isListening, setIsListening] =
    useState(false);

  const [isSpeaking, setIsSpeaking] =
    useState(false);

  const [speakingMessageId, setSpeakingMessageId] =
    useState<string | null>(null);

  const [voiceSupported, setVoiceSupported] =
    useState(false);

  const recognitionRef =
    useRef<any>(null);

  const speechUtteranceRef =
    useRef<SpeechSynthesisUtterance | null>(null);

  /*
   * Store the complete AI response separately from ChatMessage.
   * ChatMessage keeps the normal visible reply, while this state
   * keeps the structured decision context returned by RecoverAI.
   */
  const [aiInsights, setAiInsights] =
    useState<Record<string, AIResponse>>({});

  /*
   * Prevent the save effect from overwriting a merchant's history
   * before that merchant's history has finished loading.
   */
  const [historyLoadedFor, setHistoryLoadedFor] =
    useState<string | null>(null);

  /*
   * Every merchant gets an independent browser history.
   * The authenticated merchant ID is preferred over email.
   */
  const merchantKey =
    user?.id ||
    user?.email?.trim().toLowerCase() ||
    null;

  const chatStorageKey =
    merchantKey
      ? `recoverai-chat-history:${merchantKey}`
      : null;


  /* =========================================================
     VOICE SETUP
  ========================================================= */

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    const supported =
      Boolean(SpeechRecognition) &&
      'speechSynthesis' in window;

    setVoiceSupported(supported);

    if (!SpeechRecognition) {
      return;
    }

    const recognition =
      new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let transcript = '';

      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        transcript += event.results[index][0].transcript;
      }

      if (transcript.trim()) {
        setInput(transcript.trim());
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
      window.speechSynthesis.cancel();
    };
  }, []);

  const toggleListening = () => {
    if (!voiceSupported || !recognitionRef.current) {
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    try {
      recognitionRef.current.start();
    } catch {
      setIsListening(false);
    }
  };

  const stopSpeaking = () => {
    if (!('speechSynthesis' in window)) {
      return;
    }

    window.speechSynthesis.cancel();
    speechUtteranceRef.current = null;
    setIsSpeaking(false);
    setSpeakingMessageId(null);
  };

  const readAloud = (text: string, messageId: string) => {
    if (!('speechSynthesis' in window) || !text.trim()) {
      return;
    }

    stopSpeaking();

    const utterance =
      new SpeechSynthesisUtterance(text);

    utterance.lang = 'en-IN';
    utterance.rate = 0.95;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setSpeakingMessageId(messageId);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setSpeakingMessageId(null);
      speechUtteranceRef.current = null;
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setSpeakingMessageId(null);
      speechUtteranceRef.current = null;
    };

    speechUtteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };


  /* =========================================================
     LOAD HISTORY FOR CURRENT MERCHANT
  ========================================================= */

  useEffect(() => {

    if (
      !merchantKey ||
      !chatStorageKey
    ) {
      setConversations([]);
      setActiveConversationId('');
      setInput('');
      setHistoryLoadedFor(null);
      setAiInsights({});
      return;
    }

    /*
     * Clear the previous merchant's in-memory state immediately.
     * This prevents one merchant's chat from being visible while
     * another merchant's history is loading.
     */
    setConversations([]);
    setActiveConversationId('');
    setInput('');
    setAiInsights({});
    setHistoryLoadedFor(null);

    const stored =
      localStorage.getItem(chatStorageKey);

    if (stored) {
      try {
        const parsed:
          Conversation[] =
          JSON.parse(stored);

        if (
          Array.isArray(parsed) &&
          parsed.length > 0
        ) {
          setConversations(parsed);
          setActiveConversationId(parsed[0].id);
          setHistoryLoadedFor(merchantKey);
          return;
        }
      } catch (error) {
        console.error(
          'Unable to load chat history:',
          error,
        );
      }
    }

    const initialConversation =
      createConversation();

    setConversations([
      initialConversation,
    ]);

    setActiveConversationId(
      initialConversation.id,
    );

    setHistoryLoadedFor(
      merchantKey,
    );
  }, [
    merchantKey,
    chatStorageKey,
  ]);


  /* =========================================================
     PERSIST HISTORY
  ========================================================= */

  useEffect(() => {

    if (
      !merchantKey ||
      !chatStorageKey ||
      historyLoadedFor !== merchantKey ||
      conversations.length === 0
    ) {
      return;
    }

    localStorage.setItem(
      chatStorageKey,
      JSON.stringify(conversations),
    );
  }, [
    conversations,
    merchantKey,
    chatStorageKey,
    historyLoadedFor,
  ]);


  /* =========================================================
     ACTIVE CONVERSATION
  ========================================================= */

  const activeConversation =
    conversations.find(
      (conversation) =>
        conversation.id ===
        activeConversationId,
    ) ?? null;


  /* =========================================================
     NEW CONVERSATION
  ========================================================= */

  const handleNewConversation =
    () => {

      if (!merchantKey) {
        return;
      }

      const newConversation =
        createConversation();

      setConversations((prev) => [
        newConversation,
        ...prev,
      ]);

      setActiveConversationId(
        newConversation.id,
      );

      setInput('');
    };


  /* =========================================================
     SELECT CONVERSATION
  ========================================================= */

  const handleSelectConversation =
    (id: string) => {
      setActiveConversationId(id);
      setInput('');
    };


  /* =========================================================
     SEND MESSAGE
  ========================================================= */

  const send = async (
    text = input,
  ) => {

    if (
      !merchantKey ||
      !text.trim() ||
      sending ||
      !activeConversation
    ) {
      return;
    }

    const cleanText =
      text.trim();

    const conversationId =
      activeConversation.id;

    const now =
      new Date().toISOString();

    const userMessage:
      ChatMessage = {
      id:
        `user-${Date.now()}`,
      role:
        'user',
      content:
        cleanText,
      timestamp:
        now,
    };

    const updatedMessages = [
      ...activeConversation.messages,
      userMessage,
    ];

    const newTitle =
      activeConversation.title ===
      'New conversation'
        ? cleanText.slice(0, 45) +
          (
            cleanText.length > 45
              ? '...'
              : ''
          )
        : activeConversation.title;

    setConversations((prev) =>
      prev.map(
        (conversation) =>
          conversation.id ===
          conversationId
            ? {
                ...conversation,
                title:
                  newTitle,
                messages:
                  updatedMessages,
                updatedAt:
                  now,
              }
            : conversation,
      ),
    );

    setInput('');
    setSending(true);

    try {

      const conversationalReply =
        getConversationalGreeting(cleanText);

      let aiResponse: AIResponse;

      if (conversationalReply) {
        aiResponse = {
          reply: conversationalReply,
        } as AIResponse;
      } else {
        /*
         * Keep the authenticated RecoverAI API call unchanged.
         * The backend gets the merchant from the JWT.
         */
        aiResponse =
          await sendAIMessage(
            cleanText,
            updatedMessages,
          );
      }

      const assistantMessage: StoredChatMessage = {
        id:
          `assistant-${Date.now()}`,
        role:
          'assistant',
        content:
          aiResponse.reply,
        timestamp:
          new Date().toISOString(),
        aiResponse,
      };

      /*
       * Keep the complete response both in state and on the
       * assistant message. This makes structured cards survive
       * conversation switching and page reloads.
       */
      setAiInsights((prev) => ({
        ...prev,
        [assistantMessage.id]:
          aiResponse,
      }));

      setConversations((prev) =>
        prev.map(
          (conversation) =>
            conversation.id ===
            conversationId
              ? {
                  ...conversation,
                  messages: [
                    ...conversation.messages,
                    assistantMessage,
                  ],
                  updatedAt:
                    new Date().toISOString(),
                }
              : conversation,
        ),
      );

    } catch (error) {

      console.error(
        'AI message failed:',
        error,
      );

      const errorMessage:
        StoredChatMessage = {
        id:
          `error-${Date.now()}`,
        role:
          'assistant',
        content:
          'Sorry, I was unable to process your request. Please try again.',
        timestamp:
          new Date().toISOString(),
      };

      setConversations((prev) =>
        prev.map(
          (conversation) =>
            conversation.id ===
            conversationId
              ? {
                  ...conversation,
                  messages: [
                    ...conversation.messages,
                    errorMessage,
                  ],
                  updatedAt:
                    new Date().toISOString(),
                }
              : conversation,
        ),
      );

    } finally {
      setSending(false);
    }
  };


  /* =========================================================
     DELETE CONVERSATION
  ========================================================= */

  const handleDeleteConversation =
    (
      event: MouseEvent,
      id: string,
    ) => {

      event.stopPropagation();

      setConversations((prev) => {

        const remaining =
          prev.filter(
            (conversation) =>
              conversation.id !== id,
          );

        if (
          remaining.length === 0
        ) {
          const newConversation =
            createConversation();

          setActiveConversationId(
            newConversation.id,
          );

          return [
            newConversation,
          ];
        }

        if (
          id ===
          activeConversationId
        ) {
          setActiveConversationId(
            remaining[0].id,
          );
        }

        return remaining;
      });

      setAiInsights((prev) => {
        const next = { ...prev };
        const deletedConversation = conversations.find(
          (conversation) => conversation.id === id,
        );

        deletedConversation?.messages.forEach((message) => {
          delete next[message.id];
        });

        return next;
      });
    };


  /* =========================================================
     CONVERSATION GROUPS
  ========================================================= */

  const today =
    new Date().toDateString();

  const todayConversations =
    conversations.filter(
      (conversation) =>
        new Date(
          conversation.updatedAt,
        ).toDateString() === today,
    );

  const olderConversations =
    conversations.filter(
      (conversation) =>
        new Date(
          conversation.updatedAt,
        ).toDateString() !== today,
    );


  /* =========================================================
     CONVERSATION SIDEBAR ITEM
  ========================================================= */

  const renderConversation = (
    conversation: Conversation,
  ) => {

    const isActive =
      conversation.id ===
      activeConversationId;

    const messageCount =
      Math.max(
        conversation.messages.length -
          1,
        0,
      );

    return (
      <button
        key={conversation.id}
        onClick={() =>
          handleSelectConversation(
            conversation.id,
          )
        }
        className={`group w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
          isActive
            ? 'bg-brand-50 text-brand-700'
            : 'text-slate-600 hover:bg-slate-50'
        }`}
      >
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 shrink-0 text-slate-400" />

          <span className="flex-1 min-w-0">
            <span className="block text-xs font-medium truncate">
              {conversation.title}
            </span>

            <span className="block text-[10px] text-slate-400 mt-0.5">
              {messageCount}{' '}
              {messageCount === 1
                ? 'message'
                : 'messages'}
            </span>
          </span>

          <span
            role="button"
            aria-label="Delete conversation"
            onClick={(event) =>
              handleDeleteConversation(
                event,
                conversation.id,
              )
            }
            className="hidden group-hover:flex h-6 w-6 items-center justify-center rounded-md hover:bg-red-50 hover:text-red-600 text-slate-400"
          >
            ×
          </span>
        </div>
      </button>
    );
  };


  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="animate-fade-in max-w-6xl mx-auto">

      <PageHeader
        eyebrow="RecoverAI intelligence"
        title="AI Assistant"
        description="Ask questions about your revenue recovery performance."
        action={
          <Badge className="bg-blue-50 text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            RecoverAI Engine Online
          </Badge>
        }
      />

      <Card className="overflow-hidden">
        <div className="flex h-[600px]">

          {/* =================================================
              SIDEBAR
          ================================================= */}

          <aside className="hidden md:flex w-64 shrink-0 border-r border-slate-200 bg-white flex-col">

            <div className="p-3 border-b border-slate-100">
              <button
                onClick={
                  handleNewConversation
                }
                className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition-colors"
              >
                <span className="text-lg leading-none">
                  +
                </span>
                New conversation
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3">

              {todayConversations.length >
                0 && (
                <>
                  <p className="px-2 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Today
                  </p>

                  <div className="space-y-1">
                    {todayConversations.map(
                      renderConversation,
                    )}
                  </div>
                </>
              )}

              {olderConversations.length >
                0 && (
                <div className="mt-6">
                  <p className="px-2 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Previous
                  </p>

                  <div className="space-y-1">
                    {olderConversations.map(
                      renderConversation,
                    )}
                  </div>
                </div>
              )}

            </div>
          </aside>


          {/* =================================================
              CHAT AREA
          ================================================= */}

          <div className="flex-1 flex flex-col min-w-0 bg-slate-50">

            {/* MESSAGES */}

            <div className="flex-1 overflow-y-auto p-4 sm:p-6">
              <div className="max-w-3xl mx-auto space-y-5">

                {activeConversation?.messages.map(
                  (message) => {

                    const response =
                      message.role ===
                      'assistant'
                        ? message.aiResponse ||
                          aiInsights[message.id]
                        : undefined;

                    const isStructuredAssistantMessage =
                      message.role === 'assistant' &&
                      message.id !== 'welcome' &&
                      Boolean(response);

                    return (
                      <div
                        key={message.id}
                        className={`flex gap-3 animate-slide-in ${
                          message.role ===
                          'user'
                            ? 'justify-end'
                            : ''
                        }`}
                      >

                        {/* ASSISTANT ICON */}

                        {message.role ===
                          'assistant' && (
                          <div className="h-7 w-7 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center shrink-0">
                            <Sparkles className="h-3.5 w-3.5" />
                          </div>
                        )}


                        {/* MESSAGE + STRUCTURED RESULT */}

                        <div className="max-w-[80%] min-w-0">

                          <div
                            className={`rounded-xl px-4 py-3 text-sm whitespace-pre-line leading-relaxed ${
                              message.role ===
                              'user'
                                ? 'bg-brand-600 text-white'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {message.content}
                          </div>

                          {message.role === 'assistant' &&
                            message.id !== 'welcome' && (
                            <div className="mt-1.5 flex items-center gap-2">
                              {isSpeaking && speakingMessageId === message.id ? (
                                <button
                                  type="button"
                                  onClick={stopSpeaking}
                                  className="inline-flex items-center gap-1 text-[10px] text-brand-600 hover:text-brand-700"
                                >
                                  <VolumeX className="h-3 w-3" />
                                  Stop voice
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => readAloud(message.content, message.id)}
                                  className="inline-flex items-center gap-1 text-[10px] text-slate-400 hover:text-brand-600"
                                >
                                  <Volume2 className="h-3 w-3" />
                                  Read aloud
                                </button>
                              )}
                            </div>
                          )}

                          {isStructuredAssistantMessage &&
                            response && (
                              <AIInsightCard
                                response={response}
                              />
                            )}

                        </div>


                        {/* USER ICON */}

                        {message.role ===
                          'user' && (
                          <div className="h-7 w-7 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-[10px] font-semibold shrink-0">
                            U
                          </div>
                        )}

                      </div>
                    );
                  },
                )}


                {/* =================================================
                    STARTERS
                ================================================= */}

                {activeConversation &&
                  activeConversation.messages.length ===
                    1 && (
                    <div className="pt-4">
                      <p className="text-xs font-medium text-slate-500 mb-3">
                        Try asking
                      </p>

                      <div className="grid gap-2 sm:grid-cols-2">
                        {starters.map(
                          (starter) => (
                            <button
                              key={starter}
                              onClick={() =>
                                void send(
                                  starter,
                                )
                              }
                              disabled={
                                sending
                              }
                              className="text-left rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700 transition-colors disabled:opacity-50"
                            >
                              {starter}
                            </button>
                          ),
                        )}
                      </div>
                    </div>
                  )}


                {/* =================================================
                    SENDING INDICATOR
                ================================================= */}

                {sending && (
                  <div className="flex gap-3">
                    <div className="h-7 w-7 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center shrink-0">
                      <Sparkles className="h-3.5 w-3.5" />
                    </div>

                    <div className="rounded-xl bg-slate-100 px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-pulse" />
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-pulse [animation-delay:150ms]" />
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-pulse [animation-delay:300ms]" />
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </div>


            {/* =================================================
                INPUT
            ================================================= */}

            <div className="border-t border-slate-200 bg-white p-3 sm:p-4">
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  void send();
                }}
                className="max-w-3xl mx-auto"
              >
                <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-slate-50 p-2 focus-within:border-brand-300 focus-within:ring-2 focus-within:ring-brand-100">
                  <textarea
                    value={input}
                    onChange={(event) =>
                      setInput(
                        event.target.value,
                      )
                    }
                    onKeyDown={(event) => {
                      if (
                        event.key ===
                          'Enter' &&
                        !event.shiftKey
                      ) {
                        event.preventDefault();

                        if (
                          input.trim() &&
                          !sending
                        ) {
                          void send();
                        }
                      }
                    }}
                    placeholder="Ask about your recovery performance..."
                    rows={1}
                    disabled={sending}
                    className="flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-0 disabled:opacity-50"
                  />

                  <button
                  type="button"
                  onClick={toggleListening}
                  disabled={!voiceSupported || sending}
                  title={
                    voiceSupported
                      ? isListening
                        ? 'Stop listening'
                        : 'Speak your message'
                      : 'Voice input is not supported in this browser'
                  }
                  className={`h-10 w-10 shrink-0 rounded-lg border flex items-center justify-center transition-colors ${
                    isListening
                      ? 'border-red-200 bg-red-50 text-red-600'
                      : 'border-slate-200 bg-white text-slate-500 hover:border-brand-200 hover:text-brand-600'
                  } disabled:opacity-40 disabled:cursor-not-allowed`}
                >
                  {isListening ? (
                    <MicOff className="h-4 w-4" />
                  ) : (
                    <Mic className="h-4 w-4" />
                  )}
                </button>

                <button
                    type="submit"
                    disabled={
                      !input.trim() ||
                      sending
                    }
                    className="h-9 w-9 shrink-0 rounded-lg bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Send message"
                  >
                    {sending ? (
                      <span className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </button>
                </div>

                <p className="mt-2 text-center text-[10px] text-slate-400">
                  {isListening
                    ? 'Listening… speak your question, then tap send.'
                    : voiceSupported
                      ? 'Use the microphone for voice input, or Read aloud for voice responses.'
                      : 'Voice features are not supported in this browser.'}
                </p>

                <p className="mt-1 text-center text-[10px] text-slate-400">
                  RecoverAI analyzes your merchant payment data.
                  Recommendations do not automatically execute payments.
                </p>
              </form>
            </div>

          </div>
        </div>
      </Card>
    </div>
  );
}


/* =========================================================
   SETTINGS PAGE
========================================================= */

export function SettingsPage() {
  const { theme, setTheme } = useTheme();

  const [settings, setSettings] =
    useState<MerchantSettings | null>(null);

  const [saved, setSaved] =
    useState(false);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState('');

  const loadSettings = useCallback(async () => {
    setError('');

    try {
      const result = await getSettings();

      setSettings(result);
    } catch (err) {
      console.error(
        'Unable to load settings:',
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load settings.',
      );
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);


  if (error) {
    return (
      <ErrorState
        message={error}
        onRetry={() => {
          void loadSettings();
        }}
      />
    );
  }


  if (!settings) {
    return <Spinner />;
  }


  const update = <
    K extends keyof MerchantSettings
  >(
    key: K,
    value: MerchantSettings[K],
  ) => {
    setSettings((prev) =>
      prev
        ? {
            ...prev,
            [key]: value,
          }
        : prev,
    );

    setSaved(false);
  };


  const save = async () => {
    setSaving(true);
    setSaved(false);
    setError('');

    try {
      /*
       * Only send settings that the merchant is
       * actually allowed to change.
       *
       * merchantName and merchantEmail come from
       * the authenticated account and are intentionally
       * not sent as editable settings.
       */
      const editableSettings: Partial<MerchantSettings> = {
        businessName:
          settings.businessName,

        gstin:
          settings.gstin,

        merchantPhone:
          settings.merchantPhone,

        maxRetryAttempts:
          settings.maxRetryAttempts,

        retryIntervalHours:
          settings.retryIntervalHours,

        minRecoveryProbability:
          settings.minRecoveryProbability,

        emailNotifications:
          settings.emailNotifications,

        smsNotifications:
          settings.smsNotifications,

        weeklyReport:
          settings.weeklyReport,

        recoveryAlerts:
          settings.recoveryAlerts,
      };


      const result =
        await updateSettings(
          editableSettings,
        );


      /*
       * If the backend returns the updated settings,
       * use them as the source of truth.
       */
      if (result.settings) {
        setSettings(result.settings);
      } else {
        /*
         * Otherwise keep the current local state.
         */
        setSettings((current) =>
          current
            ? {
                ...current,
                ...editableSettings,
              }
            : current,
        );
      }


      setSaved(true);


      window.setTimeout(() => {
        setSaved(false);
      }, 2500);

    } catch (err) {
      console.error(
        'Unable to save settings:',
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to save settings.',
      );

    } finally {
      setSaving(false);
    }
  };


  return (
    <div className="animate-fade-in max-w-4xl">

      <PageHeader
        title="Settings"
        description="Manage your merchant profile and recovery preferences."
        action={
          <Button
            onClick={() => {
              void save();
            }}
            loading={saving}
            disabled={saving}
          >
            {saved ? (
              <>
                <Check className="h-4 w-4" />
                Saved
              </>
            ) : (
              'Save changes'
            )}
          </Button>
        }
      />


      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-danger-100 bg-danger-50 px-3 py-2.5 text-sm text-danger-700"
        >
          {error}
        </div>
      )}


      <div className="space-y-4">

        {/* =====================================================
            APPEARANCE
        ===================================================== */}

        <Card>

          <CardHeader
            title="Appearance"
            subtitle="Choose how your RecoverAI workspace looks"
          />

          <CardBody>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

              <button
                type="button"
                onClick={() => setTheme('light')}
                aria-pressed={theme === 'light'}
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                  theme === 'light'
                    ? 'border-brand-500 bg-brand-50 text-brand-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white border border-slate-200">
                  <Sun className="h-4 w-4" />
                </span>

                <span>
                  <span className="block text-sm font-semibold">
                    Light
                  </span>
                  <span className="block text-xs text-slate-400 mt-0.5">
                    Bright workspace with the default RecoverAI look.
                  </span>
                </span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('dark')}
                aria-pressed={theme === 'dark'}
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                  theme === 'dark'
                    ? 'border-brand-500 bg-brand-50 text-brand-700'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white border border-slate-700">
                  <Moon className="h-4 w-4" />
                </span>

                <span>
                  <span className="block text-sm font-semibold">
                    Dark
                  </span>
                  <span className="block text-xs text-slate-400 mt-0.5">
                    A darker workspace for low-light use.
                  </span>
                </span>
              </button>

            </div>

            <p className="mt-3 text-[10px] text-slate-400">
              Theme preference is saved on this device and does not change your merchant recovery rules.
            </p>

          </CardBody>

        </Card>


        {/* =====================================================
            MERCHANT PROFILE
        ===================================================== */}

        <Card>

          <CardHeader
            title="Merchant profile"
            subtitle="Information used across your RecoverAI workspace"
          />

          <CardBody>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

              {/* BUSINESS NAME */}

              <Input
                label="Business name"
                value={
                  settings.businessName ?? ''
                }
                onChange={(e) =>
                  update(
                    'businessName',
                    e.target.value,
                  )
                }
              />


              {/* GSTIN */}

              <Input
                label="GSTIN"
                value={
                  settings.gstin ?? ''
                }
                onChange={(e) =>
                  update(
                    'gstin',
                    e.target.value,
                  )
                }
              />


              {/* MERCHANT NAME - READ ONLY */}

              <div>
                <Input
                  label="Your name"
                  value={
                    settings.merchantName ?? ''
                  }
                  disabled
                  icon={
                    <UserRound className="h-4 w-4" />
                  }
                />

                <p className="text-[10px] text-slate-400 mt-1.5">
                  This comes from your RecoverAI account.
                </p>
              </div>


              {/* MERCHANT EMAIL - READ ONLY */}

              <div>
                <Input
                  label="Work email"
                  type="email"
                  value={
                    settings.merchantEmail ?? ''
                  }
                  disabled
                  icon={
                    <Mail className="h-4 w-4" />
                  }
                />

                <p className="text-[10px] text-slate-400 mt-1.5">
                  This comes from your authenticated account.
                </p>
              </div>


              {/* PHONE */}

              <Input
                label="Phone number"
                value={
                  settings.merchantPhone ?? ''
                }
                onChange={(e) =>
                  update(
                    'merchantPhone',
                    e.target.value,
                  )
                }
              />

            </div>

          </CardBody>

        </Card>


        {/* =====================================================
            RECOVERY RULES
        ===================================================== */}

        <Card>

          <CardHeader
            title="Recovery rules"
            subtitle="Control when and how RecoverAI should attempt recovery"
          />

          <CardBody>

            <div className="space-y-6">

              {/* MAX RETRIES */}

              <div>

                <label className="text-sm font-medium text-slate-700">
                  Maximum retry attempts
                </label>

                <p className="text-xs text-slate-500 mt-1 mb-2">
                  Maximum number of times to retry a failed
                  payment.
                </p>

                <div className="flex items-center gap-3">

                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={
                      settings.maxRetryAttempts
                    }
                    onChange={(e) =>
                      update(
                        'maxRetryAttempts',
                        Number(
                          e.target.value,
                        ),
                      )
                    }
                    className="accent-brand-600 w-48"
                  />

                  <span className="text-sm font-semibold text-slate-700">
                    {settings.maxRetryAttempts}{' '}
                    attempts
                  </span>

                </div>

              </div>


              {/* RETRY INTERVAL */}

              <div>

                <label className="text-sm font-medium text-slate-700">
                  Retry interval
                </label>

                <p className="text-xs text-slate-500 mt-1 mb-2">
                  Time to wait between automated recovery
                  attempts.
                </p>

                <select
                  value={
                    settings.retryIntervalHours
                  }
                  onChange={(e) =>
                    update(
                      'retryIntervalHours',
                      Number(
                        e.target.value,
                      ),
                    )
                  }
                  className="h-9 px-3 border border-slate-300 rounded-lg text-sm"
                >

                  <option value="6">
                    Every 6 hours
                  </option>

                  <option value="12">
                    Every 12 hours
                  </option>

                  <option value="24">
                    Every 24 hours
                  </option>

                  <option value="48">
                    Every 48 hours
                  </option>

                </select>

              </div>


              {/* MINIMUM PROBABILITY */}

              <div>

                <label className="text-sm font-medium text-slate-700">
                  Minimum recovery probability
                </label>

                <p className="text-xs text-slate-500 mt-1 mb-2">
                  Only surface recommendations above this
                  confidence threshold.
                </p>

                <div className="flex items-center gap-3">

                  <input
                    type="range"
                    min="10"
                    max="90"
                    step="5"
                    value={
                      settings.minRecoveryProbability
                    }
                    onChange={(e) =>
                      update(
                        'minRecoveryProbability',
                        Number(
                          e.target.value,
                        ),
                      )
                    }
                    className="accent-brand-600 w-48"
                  />

                  <span className="text-sm font-semibold text-slate-700">
                    {settings.minRecoveryProbability}%
                  </span>

                </div>

              </div>

            </div>

          </CardBody>

        </Card>


        {/* =====================================================
            NOTIFICATIONS
        ===================================================== */}

        <Card>

          <CardHeader
            title="Notifications"
            subtitle="Choose what updates you want to receive"
          />

          <CardBody>

            <div className="space-y-5">

              <Toggle
                label="Recovery alerts"
                description="Get notified when a recovery action succeeds or needs attention."
                checked={
                  settings.recoveryAlerts
                }
                onChange={(value) =>
                  update(
                    'recoveryAlerts',
                    value,
                  )
                }
              />


              <Toggle
                label="Email notifications"
                description="Receive important payment and recovery updates by email."
                checked={
                  settings.emailNotifications
                }
                onChange={(value) =>
                  update(
                    'emailNotifications',
                    value,
                  )
                }
              />


              <Toggle
                label="SMS notifications"
                description="Receive high-priority alerts on your registered phone."
                checked={
                  settings.smsNotifications
                }
                onChange={(value) =>
                  update(
                    'smsNotifications',
                    value,
                  )
                }
              />


              <Toggle
                label="Weekly report"
                description="Get a weekly summary of revenue recovery performance."
                checked={
                  settings.weeklyReport
                }
                onChange={(value) =>
                  update(
                    'weeklyReport',
                    value,
                  )
                }
              />

            </div>

          </CardBody>

        </Card>

      </div>

    </div>
  );
}