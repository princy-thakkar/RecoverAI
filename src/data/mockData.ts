import type {
  Payment,
  Customer,
  RecoveryCase,
  DashboardData,
  AnalyticsData,
  MerchantSettings,
  PaymentStatus,
  FailureReason,
  PaymentMethod,
  RecommendedAction,
  TimelineEvent,
} from '@/types';

const isoDaysAgo = (days: number, hours = 0) => {
  const d = new Date();
  d.setDate(d.getDate() - days);
  d.setHours(d.getHours() - hours);
  return d.toISOString();
};

const customers: Customer[] = [
  {
    id: 'CUST-1001',
    name: 'Arjun Mehta',
    email: 'arjun.mehta@gmail.com',
    phone: '+91 98200 11223',
    totalPayments: 14,
    successfulPayments: 11,
    failedPayments: 3,
    totalAmount: 184500,
    recoveryProbability: 78,
    riskProfile: 'Recovering',
    avatarColor: '#0ea5e9',
    joinedAt: '2024-03-12',
  },
  {
    id: 'CUST-1002',
    name: 'Priya Sharma',
    email: 'priya.sharma@outlook.com',
    phone: '+91 99100 44556',
    totalPayments: 8,
    successfulPayments: 8,
    failedPayments: 0,
    totalAmount: 92000,
    recoveryProbability: 95,
    riskProfile: 'Low Risk',
    avatarColor: '#10b981',
    joinedAt: '2024-06-01',
  },
  {
    id: 'CUST-1003',
    name: 'Rohan Kapoor',
    email: 'rohan.kapoor@yahoo.in',
    phone: '+91 90040 77889',
    totalPayments: 21,
    successfulPayments: 14,
    failedPayments: 7,
    totalAmount: 312000,
    recoveryProbability: 42,
    riskProfile: 'High Risk',
    avatarColor: '#f59e0b',
    joinedAt: '2023-11-22',
  },
  {
    id: 'CUST-1004',
    name: 'Sneha Reddy',
    email: 'sneha.reddy@gmail.com',
    phone: '+91 88610 23344',
    totalPayments: 6,
    successfulPayments: 4,
    failedPayments: 2,
    totalAmount: 67500,
    recoveryProbability: 64,
    riskProfile: 'Medium Risk',
    avatarColor: '#8b5cf6',
    joinedAt: '2025-01-15',
  },
  {
    id: 'CUST-1005',
    name: 'Vikram Singh',
    email: 'vikram.singh@gmail.com',
    phone: '+91 98700 55667',
    totalPayments: 19,
    successfulPayments: 16,
    failedPayments: 3,
    totalAmount: 248000,
    recoveryProbability: 71,
    riskProfile: 'Recovering',
    avatarColor: '#ef4444',
    joinedAt: '2024-02-08',
  },
  {
    id: 'CUST-1006',
    name: 'Ananya Iyer',
    email: 'ananya.iyer@gmail.com',
    phone: '+91 70200 88990',
    totalPayments: 11,
    successfulPayments: 9,
    failedPayments: 2,
    totalAmount: 134000,
    recoveryProbability: 83,
    riskProfile: 'Low Risk',
    avatarColor: '#0ea5e9',
    joinedAt: '2024-09-30',
  },
  {
    id: 'CUST-1007',
    name: 'Karan Malhotra',
    email: 'karan.malhotra@yahoo.in',
    phone: '+91 91200 33445',
    totalPayments: 5,
    successfulPayments: 2,
    failedPayments: 3,
    totalAmount: 48000,
    recoveryProbability: 35,
    riskProfile: 'High Risk',
    avatarColor: '#f59e0b',
    joinedAt: '2025-04-18',
  },
  {
    id: 'CUST-1008',
    name: 'Divya Nair',
    email: 'divya.nair@outlook.com',
    phone: '+91 99800 12233',
    totalPayments: 13,
    successfulPayments: 12,
    failedPayments: 1,
    totalAmount: 156000,
    recoveryProbability: 88,
    riskProfile: 'Low Risk',
    avatarColor: '#10b981',
    joinedAt: '2024-07-14',
  },
];

const buildTimeline = (
  status: PaymentStatus,
  failureReason: FailureReason | null,
  action: RecommendedAction,
): TimelineEvent[] => {
  const events: TimelineEvent[] = [
    {
      id: 'tl-1',
      type: 'Payment Created',
      title: 'Payment Created',
      description: 'Transaction initiated by customer.',
      timestamp: isoDaysAgo(3, 4),
      status: 'completed',
    },
  ];

  if (status === 'Successful') {
    events.push({
      id: 'tl-2',
      type: 'Result',
      title: 'Payment Successful',
      description: 'Payment captured successfully on first attempt.',
      timestamp: isoDaysAgo(3, 3),
      status: 'completed',
    });
    return events;
  }

  events.push({
    id: 'tl-2',
    type: 'Payment Failed',
    title: 'Payment Failed',
    description: `Declined: ${failureReason}.`,
    timestamp: isoDaysAgo(3, 3),
    status: 'completed',
  });

  events.push({
    id: 'tl-3',
    type: 'AI Analyzed',
    title: 'AI Analyzed',
    description: 'Recovery probability assessed and action recommended.',
    timestamp: isoDaysAgo(2, 10),
    status: 'completed',
  });

  if (status === 'At Risk') {
    events.push({
      id: 'tl-4',
      type: 'Recovery Action Selected',
      title: 'Recovery Action Selected',
      description: `Recommended: ${action}.`,
      timestamp: isoDaysAgo(2, 8),
      status: 'current',
    });
    events.push({
      id: 'tl-5',
      type: 'Recovery Attempt',
      title: 'Recovery Attempt',
      description: 'Awaiting execution.',
      timestamp: '',
      status: 'pending',
    });
    events.push({
      id: 'tl-6',
      type: 'Result',
      title: 'Result',
      description: 'Outcome pending.',
      timestamp: '',
      status: 'pending',
    });
    return events;
  }

  if (status === 'Recovering') {
    events.push({
      id: 'tl-4',
      type: 'Recovery Action Selected',
      title: 'Recovery Action Selected',
      description: `Action: ${action}.`,
      timestamp: isoDaysAgo(2, 8),
      status: 'completed',
    });
    events.push({
      id: 'tl-5',
      type: 'Recovery Attempt',
      title: 'Recovery Attempt In Progress',
      description: 'Retry attempt 1 of 3 in progress.',
      timestamp: isoDaysAgo(1, 2),
      status: 'current',
    });
    events.push({
      id: 'tl-6',
      type: 'Result',
      title: 'Result',
      description: 'Outcome pending.',
      timestamp: '',
      status: 'pending',
    });
    return events;
  }

  if (status === 'Recovered') {
    events.push({
      id: 'tl-4',
      type: 'Recovery Action Selected',
      title: 'Recovery Action Selected',
      description: `Action: ${action}.`,
      timestamp: isoDaysAgo(2, 8),
      status: 'completed',
    });
    events.push({
      id: 'tl-5',
      type: 'Recovery Attempt',
      title: 'Recovery Attempt',
      description: 'Retry attempt 1 of 3 executed.',
      timestamp: isoDaysAgo(1, 2),
      status: 'completed',
    });
    events.push({
      id: 'tl-6',
      type: 'Result',
      title: 'Payment Recovered',
      description: 'Payment successfully recovered.',
      timestamp: isoDaysAgo(0, 6),
      status: 'completed',
    });
    return events;
  }

  // Failed (no recovery)
  events.push({
    id: 'tl-4',
    type: 'Recovery Action Selected',
    title: 'Recovery Action Selected',
    description: `Recommended: ${action}.`,
    timestamp: isoDaysAgo(2, 8),
    status: 'completed',
  });
  events.push({
    id: 'tl-5',
    type: 'Recovery Attempt',
    title: 'Recovery Attempt',
    description: 'Retry attempt 1 of 3 failed.',
    timestamp: isoDaysAgo(1, 2),
    status: 'completed',
  });
  events.push({
    id: 'tl-6',
    type: 'Result',
    title: 'Recovery Failed',
    description: 'Maximum retries exhausted. Payment marked as failed.',
    timestamp: isoDaysAgo(0, 6),
    status: 'completed',
  });
  return events;
};

const payments: Payment[] = [
  {
    id: 'PAY-20250824-001',
    customerId: 'CUST-1001',
    customerName: 'Arjun Mehta',
    customerEmail: 'arjun.mehta@gmail.com',
    amount: 12500,
    paymentMethod: 'UPI',
    status: 'Recovering',
    failureReason: 'Insufficient Funds',
    recoveryProbability: 78,
    lastAttempt: isoDaysAgo(1, 2),
    recommendedAction: 'Smart Retry',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'UPI', amount: 12500, status: 'Failed', reason: 'Insufficient Funds', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'UPI', amount: 12500, status: 'Pending', reason: null, timestamp: isoDaysAgo(1, 2) },
    ],
    timeline: buildTimeline('Recovering', 'Insufficient Funds', 'Smart Retry'),
  },
  {
    id: 'PAY-20250824-002',
    customerId: 'CUST-1003',
    customerName: 'Rohan Kapoor',
    customerEmail: 'rohan.kapoor@yahoo.in',
    amount: 48000,
    paymentMethod: 'Credit Card',
    status: 'At Risk',
    failureReason: 'Card Expired',
    recoveryProbability: 42,
    lastAttempt: isoDaysAgo(2, 8),
    recommendedAction: 'Send Payment Link',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Credit Card', amount: 48000, status: 'Failed', reason: 'Card Expired', timestamp: isoDaysAgo(3, 3) },
    ],
    timeline: buildTimeline('At Risk', 'Card Expired', 'Send Payment Link'),
  },
  {
    id: 'PAY-20250824-003',
    customerId: 'CUST-1002',
    customerName: 'Priya Sharma',
    customerEmail: 'priya.sharma@outlook.com',
    amount: 5000,
    paymentMethod: 'UPI',
    status: 'Successful',
    failureReason: null,
    recoveryProbability: 100,
    lastAttempt: isoDaysAgo(3, 3),
    recommendedAction: 'No Action Needed',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'UPI', amount: 5000, status: 'Success', reason: null, timestamp: isoDaysAgo(3, 3) },
    ],
    timeline: buildTimeline('Successful', null, 'No Action Needed'),
  },
  {
    id: 'PAY-20250823-004',
    customerId: 'CUST-1005',
    customerName: 'Vikram Singh',
    customerEmail: 'vikram.singh@gmail.com',
    amount: 25000,
    paymentMethod: 'Debit Card',
    status: 'Recovered',
    failureReason: 'Network Error',
    recoveryProbability: 71,
    lastAttempt: isoDaysAgo(0, 6),
    recommendedAction: 'Retry with UPI',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Debit Card', amount: 25000, status: 'Failed', reason: 'Network Error', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'UPI', amount: 25000, status: 'Success', reason: null, timestamp: isoDaysAgo(0, 6) },
    ],
    timeline: buildTimeline('Recovered', 'Network Error', 'Retry with UPI'),
  },
  {
    id: 'PAY-20250823-005',
    customerId: 'CUST-1004',
    customerName: 'Sneha Reddy',
    customerEmail: 'sneha.reddy@gmail.com',
    amount: 1200,
    paymentMethod: 'Wallet',
    status: 'Failed',
    failureReason: 'Authentication Failed',
    recoveryProbability: 64,
    lastAttempt: isoDaysAgo(0, 6),
    recommendedAction: 'Customer Outreach',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Wallet', amount: 1200, status: 'Failed', reason: 'Authentication Failed', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'Wallet', amount: 1200, status: 'Failed', reason: 'Authentication Failed', timestamp: isoDaysAgo(1, 2) },
      { id: 'att-3', attemptNumber: 3, method: 'Wallet', amount: 1200, status: 'Failed', reason: 'Authentication Failed', timestamp: isoDaysAgo(0, 6) },
    ],
    timeline: buildTimeline('Failed', 'Authentication Failed', 'Customer Outreach'),
  },
  {
    id: 'PAY-20250822-006',
    customerId: 'CUST-1006',
    customerName: 'Ananya Iyer',
    customerEmail: 'ananya.iyer@gmail.com',
    amount: 12500,
    paymentMethod: 'UPI',
    status: 'Recovering',
    failureReason: 'Bank Declined',
    recoveryProbability: 83,
    lastAttempt: isoDaysAgo(1, 2),
    recommendedAction: 'Schedule Retry',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'UPI', amount: 12500, status: 'Failed', reason: 'Bank Declined', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'UPI', amount: 12500, status: 'Pending', reason: null, timestamp: isoDaysAgo(1, 2) },
    ],
    timeline: buildTimeline('Recovering', 'Bank Declined', 'Schedule Retry'),
  },
  {
    id: 'PAY-20250822-007',
    customerId: 'CUST-1007',
    customerName: 'Karan Malhotra',
    customerEmail: 'karan.malhotra@yahoo.in',
    amount: 48000,
    paymentMethod: 'Credit Card',
    status: 'At Risk',
    failureReason: 'Fraud Suspected',
    recoveryProbability: 35,
    lastAttempt: isoDaysAgo(2, 8),
    recommendedAction: 'Card Update Request',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Credit Card', amount: 48000, status: 'Failed', reason: 'Fraud Suspected', timestamp: isoDaysAgo(3, 3) },
    ],
    timeline: buildTimeline('At Risk', 'Fraud Suspected', 'Card Update Request'),
  },
  {
    id: 'PAY-20250821-008',
    customerId: 'CUST-1008',
    customerName: 'Divya Nair',
    customerEmail: 'divya.nair@outlook.com',
    amount: 5000,
    paymentMethod: 'Net Banking',
    status: 'Successful',
    failureReason: null,
    recoveryProbability: 100,
    lastAttempt: isoDaysAgo(3, 3),
    recommendedAction: 'No Action Needed',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Net Banking', amount: 5000, status: 'Success', reason: null, timestamp: isoDaysAgo(3, 3) },
    ],
    timeline: buildTimeline('Successful', null, 'No Action Needed'),
  },
  {
    id: 'PAY-20250821-009',
    customerId: 'CUST-1001',
    customerName: 'Arjun Mehta',
    customerEmail: 'arjun.mehta@gmail.com',
    amount: 25000,
    paymentMethod: 'UPI',
    status: 'Recovered',
    failureReason: 'Insufficient Funds',
    recoveryProbability: 78,
    lastAttempt: isoDaysAgo(0, 12),
    recommendedAction: 'Smart Retry',
    createdAt: isoDaysAgo(4, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'UPI', amount: 25000, status: 'Failed', reason: 'Insufficient Funds', timestamp: isoDaysAgo(4, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'UPI', amount: 25000, status: 'Success', reason: null, timestamp: isoDaysAgo(0, 12) },
    ],
    timeline: buildTimeline('Recovered', 'Insufficient Funds', 'Smart Retry'),
  },
  {
    id: 'PAY-20250820-010',
    customerId: 'CUST-1003',
    customerName: 'Rohan Kapoor',
    customerEmail: 'rohan.kapoor@yahoo.in',
    amount: 1200,
    paymentMethod: 'Debit Card',
    status: 'Failed',
    failureReason: 'Invalid Card',
    recoveryProbability: 42,
    lastAttempt: isoDaysAgo(0, 6),
    recommendedAction: 'Customer Outreach',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Debit Card', amount: 1200, status: 'Failed', reason: 'Invalid Card', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'Debit Card', amount: 1200, status: 'Failed', reason: 'Invalid Card', timestamp: isoDaysAgo(1, 2) },
      { id: 'att-3', attemptNumber: 3, method: 'Debit Card', amount: 1200, status: 'Failed', reason: 'Invalid Card', timestamp: isoDaysAgo(0, 6) },
    ],
    timeline: buildTimeline('Failed', 'Invalid Card', 'Customer Outreach'),
  },
  {
    id: 'PAY-20250820-011',
    customerId: 'CUST-1005',
    customerName: 'Vikram Singh',
    customerEmail: 'vikram.singh@gmail.com',
    amount: 12500,
    paymentMethod: 'UPI',
    status: 'Successful',
    failureReason: null,
    recoveryProbability: 100,
    lastAttempt: isoDaysAgo(3, 3),
    recommendedAction: 'No Action Needed',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'UPI', amount: 12500, status: 'Success', reason: null, timestamp: isoDaysAgo(3, 3) },
    ],
    timeline: buildTimeline('Successful', null, 'No Action Needed'),
  },
  {
    id: 'PAY-20250819-012',
    customerId: 'CUST-1004',
    customerName: 'Sneha Reddy',
    customerEmail: 'sneha.reddy@gmail.com',
    amount: 5000,
    paymentMethod: 'Credit Card',
    status: 'Recovering',
    failureReason: 'Limit Exceeded',
    recoveryProbability: 64,
    lastAttempt: isoDaysAgo(1, 2),
    recommendedAction: 'Schedule Retry',
    createdAt: isoDaysAgo(3, 4),
    attempts: [
      { id: 'att-1', attemptNumber: 1, method: 'Credit Card', amount: 5000, status: 'Failed', reason: 'Limit Exceeded', timestamp: isoDaysAgo(3, 3) },
      { id: 'att-2', attemptNumber: 2, method: 'Credit Card', amount: 5000, status: 'Pending', reason: null, timestamp: isoDaysAgo(1, 2) },
    ],
    timeline: buildTimeline('Recovering', 'Limit Exceeded', 'Schedule Retry'),
  },
];

const recoveryCases: RecoveryCase[] = payments
  .filter((p) => p.status === 'At Risk' || p.status === 'Recovering')
  .map((p, i) => ({
    id: `RC-${100 + i}`,
    paymentId: p.id,
    customerId: p.customerId,
    customerName: p.customerName,
    amountAtRisk: p.amount,
    failureReason: p.failureReason!,
    recoveryProbability: p.recoveryProbability,
    recommendedAction: p.recommendedAction,
    status: p.status === 'At Risk' ? 'Pending' : 'In Progress',
    attempts: p.attempts.length,
    createdAt: p.createdAt,
    lastUpdated: p.lastAttempt,
  }));

const dashboardData: DashboardData = {
  stats: {
    totalTransactions: 1284,
    successfulPayments: 1047,
    failedPayments: 237,
    revenueAtRisk: 845000,
    revenueRecovered: 612000,
    recoveryRate: 72.4,
  },
  revenueChart: [
    { label: 'Mon', recovered: 78000, atRisk: 32000 },
    { label: 'Tue', recovered: 95000, atRisk: 28000 },
    { label: 'Wed', recovered: 64000, atRisk: 45000 },
    { label: 'Thu', recovered: 112000, atRisk: 38000 },
    { label: 'Fri', recovered: 88000, atRisk: 52000 },
    { label: 'Sat', recovered: 103000, atRisk: 41000 },
    { label: 'Sun', recovered: 72000, atRisk: 35000 },
  ],
  statusChart: [
    { label: 'Mon', successful: 142, failed: 28 },
    { label: 'Tue', successful: 168, failed: 22 },
    { label: 'Wed', successful: 121, failed: 35 },
    { label: 'Thu', successful: 189, failed: 31 },
    { label: 'Fri', successful: 156, failed: 42 },
    { label: 'Sat', successful: 174, failed: 26 },
    { label: 'Sun', successful: 97, failed: 53 },
  ],
  recentAttempts: [
    { id: 'ra-1', customerName: 'Vikram Singh', amount: 25000, action: 'Retry with UPI', status: 'Recovered', timestamp: isoDaysAgo(0, 6) },
    { id: 'ra-2', customerName: 'Arjun Mehta', amount: 12500, action: 'Smart Retry', status: 'In Progress', timestamp: isoDaysAgo(1, 2) },
    { id: 'ra-3', customerName: 'Ananya Iyer', amount: 12500, action: 'Schedule Retry', status: 'Retry Scheduled', timestamp: isoDaysAgo(1, 2) },
    { id: 'ra-4', customerName: 'Sneha Reddy', amount: 5000, action: 'Schedule Retry', status: 'In Progress', timestamp: isoDaysAgo(1, 2) },
    { id: 'ra-5', customerName: 'Rohan Kapoor', amount: 48000, action: 'Send Payment Link', status: 'Awaiting Customer', timestamp: isoDaysAgo(2, 8) },
  ],
  topFailureReasons: [
    { reason: 'Insufficient Funds', count: 68, amount: 285000 },
    { reason: 'Card Expired', count: 42, amount: 198000 },
    { reason: 'Network Error', count: 35, amount: 142000 },
    { reason: 'Authentication Failed', count: 28, amount: 86000 },
    { reason: 'Bank Declined', count: 22, amount: 74000 },
  ],
  recommendations: [
    {
      id: 'rec-1',
      paymentId: 'PAY-20250824-002',
      customerName: 'Rohan Kapoor',
      amount: 48000,
      reason: 'Card Expired',
      probability: 42,
      action: 'Send Payment Link',
      rationale: 'Customer has a high lifetime value. Sending a payment link to update card details has a 42% recovery probability.',
    },
    {
      id: 'rec-2',
      paymentId: 'PAY-20250822-007',
      customerName: 'Karan Malhotra',
      amount: 48000,
      reason: 'Fraud Suspected',
      probability: 35,
      action: 'Card Update Request',
      rationale: 'Fraud flag requires customer verification. Requesting a card update is the safest recovery path.',
    },
    {
      id: 'rec-3',
      paymentId: 'PAY-20250824-001',
      customerName: 'Arjun Mehta',
      amount: 12500,
      reason: 'Insufficient Funds',
      probability: 78,
      action: 'Smart Retry',
      rationale: 'Customer has a strong payment history. Smart retry during peak funding hours has high recovery probability.',
    },
  ],
};

const analyticsData: AnalyticsData = {
  revenueAtRisk: 845000,
  revenueRecovered: 612000,
  recoveryRate: 72.4,
  recoveryAttempts: 312,
  successfulRecoveries: 226,
  recoveryByMethod: [
    { method: 'UPI', recovered: 248000, attempted: 310000 },
    { method: 'Credit Card', recovered: 156000, attempted: 245000 },
    { method: 'Debit Card', recovered: 98000, attempted: 160000 },
    { method: 'Net Banking', recovered: 72000, attempted: 90000 },
    { method: 'Wallet', recovered: 38000, attempted: 70000 },
  ],
  recoveryByReason: [
    { reason: 'Insufficient Funds', recovered: 198000, attempted: 285000 },
    { reason: 'Network Error', recovered: 112000, attempted: 142000 },
    { reason: 'Card Expired', recovered: 68000, attempted: 198000 },
    { reason: 'Authentication Failed', recovered: 42000, attempted: 86000 },
    { reason: 'Bank Declined', recovered: 51000, attempted: 74000 },
    { reason: 'Invalid Card', recovered: 28000, attempted: 60000 },
    { reason: 'Fraud Suspected', recovered: 12000, attempted: 45000 },
    { reason: 'Limit Exceeded', recovered: 95000, attempted: 120000 },
  ],
  performanceOverTime: [
    { label: 'Wk 1', recovered: 320000, atRisk: 120000 },
    { label: 'Wk 2', recovered: 410000, atRisk: 180000 },
    { label: 'Wk 3', recovered: 380000, atRisk: 210000 },
    { label: 'Wk 4', recovered: 612000, atRisk: 845000 },
  ],
};

const defaultSettings: MerchantSettings = {
  merchantName: 'Rajesh Kumar',
  merchantEmail: 'rajesh@shopkart.in',
  merchantPhone: '+91 98765 43210',
  businessName: 'ShopKart India Pvt Ltd',
  gstin: '27ABCDE1234F1Z5',
  maxRetryAttempts: 3,
  retryIntervalHours: 24,
  minRecoveryProbability: 40,
  emailNotifications: true,
  smsNotifications: true,
  weeklyReport: true,
  recoveryAlerts: true,
};

export const mockData = {
  customers,
  payments,
  recoveryCases,
  dashboardData,
  analyticsData,
  settings: defaultSettings,
};

export { buildTimeline };
