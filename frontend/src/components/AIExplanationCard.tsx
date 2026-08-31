import React from 'react';
import { Sparkles, CheckCircle, AlertTriangle, ShieldCheck, Info } from 'lucide-react';
import { RiskExplanation } from '../types';

interface AIExplanationCardProps {
  explanation: RiskExplanation | null;
  loading?: boolean;
  onRefresh?: () => void;
}

export const AIExplanationCard: React.FC<AIExplanationCardProps> = ({
  explanation,
  loading = false,
  onRefresh
}) => {
  if (loading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm animate-pulse">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-6 h-6 rounded-lg bg-indigo-500/20"></div>
          <div className="h-4 w-48 bg-slate-800 rounded"></div>
        </div>
        <div className="space-y-3">
          <div className="h-3 w-full bg-slate-800 rounded"></div>
          <div className="h-3 w-5/6 bg-slate-800 rounded"></div>
          <div className="h-3 w-4/6 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">AI Risk Explanation</h3>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-3 py-1 text-xs rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
            >
              Generate AI Summary
            </button>
          )}
        </div>
        <p className="mt-3 text-xs text-slate-400">Click to translate the structured graph evidence into a merchant-friendly risk summary.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-indigo-950/20 border border-indigo-500/30 rounded-xl p-6 shadow-lg shadow-indigo-950/20 relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-lg text-white shadow-md shadow-indigo-950/50">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">{explanation.headline}</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-medium">
                Gemini 2.5 Flash
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Evidence-grounded natural language synthesis</p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-lg text-xs leading-relaxed text-slate-300 mb-4">
        {explanation.summary}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Key Signals */}
        <div className="p-3.5 bg-slate-950/40 border border-slate-800/60 rounded-lg">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Key Signals Observed
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {explanation.key_signals.map((sig, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-indigo-400 mt-0.5">•</span>
                <span>{sig}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Observed Evidence */}
        <div className="p-3.5 bg-slate-950/40 border border-slate-800/60 rounded-lg">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-sky-400" />
            Observable Evidence Details
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {explanation.observed_evidence.map((ev, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-sky-400 mt-0.5">•</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended Action & Uncertainty */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 bg-indigo-950/30 border border-indigo-500/20 rounded-lg text-xs">
        <div className="flex items-center gap-2 text-indigo-200">
          <ShieldCheck className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <span><strong>Action:</strong> {explanation.recommended_action}</span>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500">
        <Info className="w-3.5 h-3.5 flex-shrink-0" />
        <span>{explanation.uncertainty}</span>
      </div>
    </div>
  );
};
