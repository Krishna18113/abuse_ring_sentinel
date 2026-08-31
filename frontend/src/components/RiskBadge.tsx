import React from 'react';
import { RiskLevel } from '../types';

interface RiskBadgeProps {
  level: RiskLevel;
  reviewRequired?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  reviewRequired,
  size = 'md'
}) => {
  const getBadgeStyle = () => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'LOW':
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-0.5 text-xs';
      case 'lg':
        return 'px-3 py-1.5 text-sm font-semibold';
      case 'md':
      default:
        return 'px-2.5 py-1 text-xs font-medium';
    }
  };

  return (
    <div className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center rounded-full border ${getBadgeStyle()} ${getSizeStyle()}`}>
        <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${level === 'HIGH' ? 'bg-rose-400' : level === 'MEDIUM' ? 'bg-amber-400' : 'bg-emerald-400'}`} />
        {level} RISK
      </span>
      {reviewRequired && (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
          REVIEW
        </span>
      )}
    </div>
  );
};
