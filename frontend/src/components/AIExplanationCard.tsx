import React from 'react';
import { Sparkles, CheckCircle, AlertTriangle, ShieldCheck, Info, RefreshCw } from 'lucide-react';
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
  if (loading && !explanation) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20"></div>
            <div className="space-y-1.5">
              <div className="h-4 w-40 bg-slate-800 rounded"></div>
              <div className="h-3 w-28 bg-slate-800/60 rounded"></div>
            </div>
          </div>
        </div>
        <div className="p-4 bg-slate-950/60 rounded-xl space-y-2">
          <div className="h-3 w-full bg-slate-800 rounded"></div>
          <div className="h-3 w-5/6 bg-slate-800 rounded"></div>
          <div className="h-3 w-4/6 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-slate-400">
            <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Risk Explanation</h3>
              <p className="text-xs text-slate-400">Natural language synthesis from structured graph evidence</p>
            </div>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Generate Summary</span>
            </button>
          )}
        </div>
        <p className="mt-3 text-xs text-slate-400 leading-relaxed">
          Click above to synthesize observable hardware, network, and campaign signals into an evidence-grounded merchant risk summary.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-6 shadow-xl shadow-indigo-950/10 relative overflow-hidden space-y-5">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-xl text-white shadow-md shadow-indigo-950/50">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-tight">AI Risk Summary</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                Evidence Synthesizer
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Evidence-grounded natural language synthesis</p>
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-xl transition-all border ${
              loading 
                ? 'bg-slate-800/60 text-indigo-400 border-indigo-500/30 cursor-wait' 
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 hover:border-slate-600'
            }`}
            title="Regenerate explanation"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            <span>{loading ? 'Regenerating...' : 'Refresh'}</span>
          </button>
        )}
      </div>

      {/* Headline Callout */}
      <div className="p-3.5 bg-indigo-950/30 border border-indigo-500/20 rounded-xl">
        <h4 className="text-xs font-bold text-indigo-200">{explanation.headline}</h4>
      </div>

      {/* Detailed Narrative Summary */}
      <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs leading-relaxed text-slate-300">
        {explanation.summary}
      </div>

      {/* Structured Evidence Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Key Signals Observed */}
        <div className="p-4 bg-slate-950/40 border border-slate-800/80 rounded-xl space-y-2.5">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Key Signals Observed
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {explanation.key_signals.map((sig, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-indigo-400 mt-0.5 font-bold">•</span>
                <span>{sig}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Observable Evidence Details */}
        <div className="p-4 bg-slate-950/40 border border-slate-800/80 rounded-xl space-y-2.5">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <CheckCircle className="w-3.5 h-3.5 text-sky-400" />
            Observable Evidence Details
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {explanation.observed_evidence.map((ev, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-sky-400 mt-0.5 font-bold">•</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended Action */}
      <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl flex items-start gap-3 text-xs">
        <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-500/20 flex-shrink-0 mt-0.5">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <strong className="text-white block mb-0.5 font-semibold">Recommended Operational Action:</strong>
          <span className="text-slate-300 leading-relaxed">{explanation.recommended_action}</span>
        </div>
      </div>

      {/* Transparency & AI Responsibility Notice */}
      <div className="pt-2 border-t border-slate-800/80 flex items-start gap-2 text-[11px] text-slate-400 leading-normal">
        <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="text-slate-300 font-medium">AI Responsibility Notice: </span>
          AI-generated explanation based strictly on structured graph evidence. Risk scores and review thresholds are computed deterministically by the GraphSAGE model. {explanation.uncertainty}
        </div>
      </div>

    </div>
  );
};
