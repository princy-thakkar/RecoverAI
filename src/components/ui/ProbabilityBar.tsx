import { getProbabilityBgColor, getProbabilityColor, getProbabilityLabel } from '@/utils/format';

interface ProbabilityBarProps {
  probability: number;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export function ProbabilityBar({ probability, showLabel = true, size = 'md' }: ProbabilityBarProps) {
  const barHeight = size === 'sm' ? 'h-1.5' : 'h-2';
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className={`flex-1 bg-slate-100 rounded-full overflow-hidden ${barHeight}`}>
        <div
          className={`${barHeight} rounded-full transition-all duration-500 ${getProbabilityBgColor(probability)}`}
          style={{ width: `${probability}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex items-center gap-1 whitespace-nowrap">
          <span className={`text-xs font-semibold ${getProbabilityColor(probability)}`}>
            {probability}%
          </span>
          <span className="text-xs text-slate-400 hidden sm:inline">
            {getProbabilityLabel(probability)}
          </span>
        </div>
      )}
    </div>
  );
}
