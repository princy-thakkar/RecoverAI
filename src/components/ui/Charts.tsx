import { useMemo } from 'react';
import type { PaymentStatusPoint, RevenuePoint } from '@/types';
import { formatINRCompact } from '@/utils/format';

interface RevenueChartProps {
  data: RevenuePoint[];
  height?: number;
}

export function RevenueChart({ data, height = 240 }: RevenueChartProps) {
  const maxValue = useMemo(
    () => Math.max(...data.flatMap((item) => [item.recovered, item.atRisk]), 1),
    [data],
  );
  const chartWidth = 640;
  const padding = { top: 16, right: 16, bottom: 34, left: 54 };
  const innerW = chartWidth - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const points = data.map((item, index) => ({
    x: padding.left + (index / Math.max(data.length - 1, 1)) * innerW,
    recoveredY: padding.top + innerH - (item.recovered / maxValue) * innerH,
    riskY: padding.top + innerH - (item.atRisk / maxValue) * innerH,
  }));
  const recoveredPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.recoveredY}`).join(' ');
  const riskPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.riskY}`).join(' ');
  const gridValues = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="w-full overflow-hidden">
      <div className="flex items-center gap-4 mb-3 px-1">
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-brand-500" /> Recovered
        </span>
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-warning-500" /> At risk
        </span>
      </div>
      <svg viewBox={`0 0 ${chartWidth} ${height}`} className="w-full" preserveAspectRatio="none" role="img" aria-label="Revenue recovery chart">
        <defs>
          <linearGradient id="recoveredFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.16" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
        {gridValues.map((fraction) => {
          const y = padding.top + innerH - fraction * innerH;
          return (
            <g key={fraction}>
              <line x1={padding.left} x2={chartWidth - padding.right} y1={y} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />
              <text x={padding.left - 8} y={y + 3} textAnchor="end" fontSize="10" fill="#94a3b8">
                {formatINRCompact(maxValue * fraction)}
              </text>
            </g>
          );
        })}
        <path d={`${recoveredPath} L ${points[points.length - 1].x} ${padding.top + innerH} L ${points[0].x} ${padding.top + innerH} Z`} fill="url(#recoveredFill)" />
        <path d={riskPath} fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d={recoveredPath} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {points.map((point, index) => (
          <g key={data[index].label}>
            <circle cx={point.x} cy={point.recoveredY} r="4" fill="white" stroke="#3b82f6" strokeWidth="2" />
            <text x={point.x} y={height - 10} textAnchor="middle" fontSize="10" fill="#94a3b8">{data[index].label}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

interface PaymentStatusChartProps {
  data: PaymentStatusPoint[];
  height?: number;
}

export function PaymentStatusChart({ data, height = 240 }: PaymentStatusChartProps) {
  const maxValue = Math.max(...data.flatMap((item) => [item.successful, item.failed]), 1);
  const chartWidth = 640;
  const padding = { top: 18, right: 16, bottom: 34, left: 34 };
  const innerW = chartWidth - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const groupWidth = innerW / data.length;
  const barWidth = Math.min(18, groupWidth * 0.22);

  return (
    <div className="w-full overflow-hidden">
      <div className="flex items-center gap-4 mb-3 px-1">
        <span className="flex items-center gap-1.5 text-xs text-slate-500"><span className="w-2 h-2 rounded-full bg-success-500" /> Successful</span>
        <span className="flex items-center gap-1.5 text-xs text-slate-500"><span className="w-2 h-2 rounded-full bg-danger-500" /> Failed</span>
      </div>
      <svg viewBox={`0 0 ${chartWidth} ${height}`} className="w-full" preserveAspectRatio="none" role="img" aria-label="Payment success and failure chart">
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
          const y = padding.top + innerH - fraction * innerH;
          return <line key={fraction} x1={padding.left} x2={chartWidth - padding.right} y1={y} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />;
        })}
        {data.map((item, index) => {
          const xCenter = padding.left + groupWidth * index + groupWidth / 2;
          const successHeight = (item.successful / maxValue) * innerH;
          const failHeight = (item.failed / maxValue) * innerH;
          return (
            <g key={item.label}>
              <rect x={xCenter - barWidth - 2} y={padding.top + innerH - successHeight} width={barWidth} height={successHeight} rx="3" fill="#10b981" />
              <rect x={xCenter + 2} y={padding.top + innerH - failHeight} width={barWidth} height={failHeight} rx="3" fill="#ef4444" />
              <text x={xCenter} y={height - 10} textAnchor="middle" fontSize="10" fill="#94a3b8">{item.label}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

interface DonutChartProps {
  items: { label: string; value: number; color: string }[];
  size?: number;
  centerLabel?: string;
  centerValue?: string;
}

export function DonutChart({ items, size = 180, centerLabel, centerValue }: DonutChartProps) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const radius = 66;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 160 160" className="-rotate-90">
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="18" />
        {items.map((item) => {
          const length = total ? (item.value / total) * circumference : 0;
          const circle = (
            <circle key={item.label} cx="80" cy="80" r={radius} fill="none" stroke={item.color} strokeWidth="18" strokeDasharray={`${length} ${circumference - length}`} strokeDashoffset={-offset} strokeLinecap="butt" />
          );
          offset += length;
          return circle;
        })}
      </svg>
      {(centerLabel || centerValue) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          {centerValue && <span className="text-xl font-bold text-slate-800">{centerValue}</span>}
          {centerLabel && <span className="text-[10px] text-slate-500">{centerLabel}</span>}
        </div>
      )}
    </div>
  );
}
