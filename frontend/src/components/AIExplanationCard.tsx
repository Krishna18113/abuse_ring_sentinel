import React, { useState } from 'react';
import { 
  Sparkles, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Smartphone, 
  Globe, 
  Tag, 
  Clock, 
  Users, 
  CheckCircle2, 
  ChevronDown, 
  ChevronRight, 
  Info, 
  RefreshCw, 
  Search,
  Check
} from 'lucide-react';
import { 
  RiskExplanation, 
  RiskLevel, 
  CustomerInvestigation, 
  MultiSignalConnection 
} from '../types';

export interface AIExplanationCardProps {
  explanation: RiskExplanation | null;
  loading?: boolean;
  onRefresh?: () => void;
  risk?: {
    risk_probability: number;
    review_required: boolean;
    risk_level: RiskLevel;
  };
  signals?: CustomerInvestigation['signals'];
  strengths?: CustomerInvestigation['strengths'];
  summary?: CustomerInvestigation['summary'];
  multiSignalConnections?: MultiSignalConnection[];
}

export const AIExplanationCard: React.FC<AIExplanationCardProps> = ({
  explanation,
  loading = false,
  onRefresh,
  risk,
  signals,
  strengths,
  summary,
  multiSignalConnections = []
}) => {
  const [showDetailedExplanation, setShowDetailedExplanation] = useState(false);

  // Loading State
  if (loading && !explanation) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20"></div>
            <div className="space-y-1.5">
              <div className="h-4 w-44 bg-slate-800 rounded"></div>
              <div className="h-3 w-32 bg-slate-800/60 rounded"></div>
            </div>
          </div>
        </div>
        <div className="p-4 bg-slate-950/60 rounded-xl space-y-2">
          <div className="h-3 w-full bg-slate-800 rounded"></div>
          <div className="h-3 w-5/6 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  // Fallback if explanation is not yet generated
  if (!explanation) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-slate-400">
            <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Risk Decision Summary</h3>
              <p className="text-xs text-slate-400">Synthesizing observable signals into decision support</p>
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
          Click above to generate an evidence-grounded risk decision summary.
        </p>
      </div>
    );
  }

  // Derive risk parameters
  const riskProb = risk ? risk.risk_probability : 0;
  const isReviewRequired = risk ? risk.review_required : riskProb >= 0.60;
  const riskLevel: RiskLevel = risk ? risk.risk_level : (riskProb >= 0.70 ? 'HIGH' : riskProb >= 0.35 ? 'MEDIUM' : 'LOW');
  const isHighRisk = riskLevel === 'HIGH';

  // Count active signals
  const activeSignalsCount = summary?.signal_count ?? [
    strengths?.shared_device?.detected,
    strengths?.shared_ip?.detected,
    strengths?.coupon_coordination?.detected,
    strengths?.temporal_coordination?.detected,
    strengths?.referral_coordination?.detected,
  ].filter(Boolean).length;

  // Connected accounts count
  const connectedAccountsCount = summary?.connected_customer_count ?? (
    signals?.shared_devices?.[0]?.customer_count 
      ? signals.shared_devices[0].customer_count - 1 
      : multiSignalConnections.length
  );

  // Overlap classification
  let overlapText = "Zero multi-account overlap (Isolated profile)";
  if (multiSignalConnections.length >= 2) {
    overlapText = "Strong multi-account overlap";
  } else if (multiSignalConnections.length === 1 || activeSignalsCount >= 2) {
    overlapText = "Moderate infrastructure overlap";
  } else if (activeSignalsCount === 1) {
    overlapText = "Single infrastructure overlap";
  }

  // Build evidence signal cards from actual backend data
  const evidenceCards: Array<{
    icon: React.ReactNode;
    title: string;
    value: string;
    metric: string;
    meaning: string;
    variant: 'danger' | 'warning' | 'info' | 'neutral';
  }> = [];

  // 1. Shared Device
  if (signals?.shared_devices && signals.shared_devices.length > 0) {
    const dev = signals.shared_devices[0];
    const otherCount = dev.customer_count > 1 ? dev.customer_count - 1 : 1;
    evidenceCards.push({
      icon: <Smartphone className="w-4 h-4 text-rose-400" />,
      title: "SHARED HARDWARE",
      value: dev.device_id,
      metric: `${otherCount} connected account${otherCount > 1 ? 's' : ''}`,
      meaning: "Multiple accounts operating from identical physical hardware",
      variant: 'danger',
    });
  }

  // 2. Shared IP
  if (signals?.shared_ips && signals.shared_ips.length > 0) {
    const ip = signals.shared_ips[0];
    const otherCount = ip.customer_count > 1 ? ip.customer_count - 1 : 1;
    evidenceCards.push({
      icon: <Globe className="w-4 h-4 text-amber-400" />,
      title: "SHARED NETWORK IP",
      value: ip.ip_address,
      metric: `${otherCount} connected account${otherCount > 1 ? 's' : ''}`,
      meaning: "Coordinated access through shared network gateway",
      variant: 'warning',
    });
  }

  // 3. Shared Coupon
  if (signals?.coupon_coordination && signals.coupon_coordination.length > 0) {
    const coupon = signals.coupon_coordination[0];
    evidenceCards.push({
      icon: <Tag className="w-4 h-4 text-purple-400" />,
      title: "COORDINATED COUPON",
      value: coupon.coupon_id,
      metric: `${coupon.customer_count} accounts used coupon`,
      meaning: "Promotional discount redeemed across coordinated ring accounts",
      variant: 'warning',
    });
  }

  // 4. Temporal Cluster
  if (signals?.temporal_clusters && signals.temporal_clusters.length > 0) {
    const cluster = signals.temporal_clusters[0];
    evidenceCards.push({
      icon: <Clock className="w-4 h-4 text-indigo-400" />,
      title: "TEMPORAL CLUSTER",
      value: `<${cluster.time_window_seconds || 60}s Window`,
      metric: `${cluster.transaction_count} rapid transactions`,
      meaning: "Synchronized multi-account transaction burst",
      variant: 'info',
    });
  }

  // If low-risk control account with no abusive signals, display clean organic evidence
  if (evidenceCards.length === 0) {
    evidenceCards.push({
      icon: <Smartphone className="w-4 h-4 text-emerald-400" />,
      title: "DEDICATED HARDWARE",
      value: "Clean Fingerprint",
      metric: "0 shared accounts",
      meaning: "Device used exclusively by this customer account",
      variant: 'neutral',
    });
    evidenceCards.push({
      icon: <Globe className="w-4 h-4 text-emerald-400" />,
      title: "RESIDENTIAL IP",
      value: "Private Gateway",
      metric: "0 shared accounts",
      meaning: "Standard consumer network connection without pooling",
      variant: 'neutral',
    });
    evidenceCards.push({
      icon: <Tag className="w-4 h-4 text-emerald-400" />,
      title: "ORGANIC PROMOTIONS",
      value: "Standard Usage",
      metric: "No campaign pooling",
      meaning: "Natural promotional redemption cadence",
      variant: 'neutral',
    });
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      
      {/* 1. TOP-LEVEL DECISION HEADER (3-Second Scannability) */}
      <div className="pb-5 border-b border-slate-800/80 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          
          {/* Section Title */}
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
              AI Risk Summary
            </span>
          </div>

          {/* Refresh Action */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-lg transition-all border ${
                loading 
                  ? 'bg-slate-800/60 text-indigo-400 border-indigo-500/30 cursor-wait' 
                  : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 border-slate-700 hover:text-white'
              }`}
              title="Regenerate explanation"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
              <span>{loading ? 'Regenerating...' : 'Refresh'}</span>
            </button>
          )}
        </div>

        {/* Primary Decision Banner */}
        <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
          isHighRisk 
            ? 'bg-rose-950/30 border-rose-500/40 text-rose-200' 
            : isReviewRequired
            ? 'bg-amber-950/30 border-amber-500/40 text-amber-200'
            : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
        }`}>
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold font-mono tracking-wide ${
                isHighRisk 
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
                  : isReviewRequired
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}>
                {riskLevel} RISK
              </span>
              
              <span className="font-mono font-bold text-white text-sm">
                {(riskProb * 100).toFixed(2)}% risk probability
              </span>
            </div>

            <div className="text-xs text-slate-300 pt-0.5 font-medium">
              <strong className="text-white">Why flagged: </strong>
              <span>{explanation.headline}</span>
            </div>
          </div>

          <div className="flex-shrink-0">
            {isReviewRequired ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-bold shadow-md shadow-rose-950/50">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>REVIEW REQUIRED</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/90 text-white text-xs font-bold shadow-md shadow-emerald-950/50">
                <Check className="w-3.5 h-3.5" />
                <span>ROUTINE ACCOUNT</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. "WHY WAS THIS FLAGGED?" SECTION (Concise Evidence Cards) */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
          Why was this flagged?
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {evidenceCards.map((card, idx) => (
            <div 
              key={idx}
              className={`p-3.5 rounded-xl border flex flex-col justify-between space-y-2 transition-all ${
                card.variant === 'danger'
                  ? 'bg-rose-950/20 border-rose-500/30 hover:border-rose-500/50'
                  : card.variant === 'warning'
                  ? 'bg-amber-950/20 border-amber-500/30 hover:border-amber-500/50'
                  : card.variant === 'info'
                  ? 'bg-indigo-950/20 border-indigo-500/30 hover:border-indigo-500/50'
                  : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">
                    {card.title}
                  </span>
                  {card.icon}
                </div>
                
                <div className="font-mono font-bold text-white text-xs truncate" title={card.value}>
                  {card.value}
                </div>
              </div>

              <div className="pt-1.5 border-t border-slate-800/60 space-y-0.5">
                <div className="text-[11px] font-semibold text-slate-200 font-mono">
                  {card.metric}
                </div>
                <div className="text-[10px] text-slate-400 leading-tight">
                  {card.meaning}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3 & 4. TWO-COLUMN: EVIDENCE STRENGTH & RECOMMENDED ACTION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* 3. Evidence Strength */}
        <div className="p-4 bg-slate-950/50 border border-slate-800 rounded-xl space-y-2.5">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span>Evidence Strength</span>
          </div>

          <ul className="space-y-1.5 text-xs text-slate-300 font-medium">
            <li className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${activeSignalsCount > 0 ? 'bg-rose-400' : 'bg-emerald-400'}`}></span>
              <span><strong>{activeSignalsCount}</strong> independent signal{activeSignalsCount !== 1 ? 's' : ''} detected</span>
            </li>
            <li className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${connectedAccountsCount > 0 ? 'bg-amber-400' : 'bg-emerald-400'}`}></span>
              <span><strong>{connectedAccountsCount}</strong> connected account{connectedAccountsCount !== 1 ? 's' : ''}</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
              <span>{overlapText}</span>
            </li>
          </ul>
        </div>

        {/* 4. Recommended Action */}
        <div className={`p-4 rounded-xl border flex items-start gap-3 ${
          isReviewRequired 
            ? 'bg-rose-950/20 border-rose-500/30' 
            : 'bg-emerald-950/20 border-emerald-500/30'
        }`}>
          <div className={`p-2 rounded-lg flex-shrink-0 mt-0.5 ${
            isReviewRequired ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
          }`}>
            {isReviewRequired ? <Search className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
          </div>
          
          <div className="space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-wider font-mono text-slate-400">
              Recommended Action
            </div>
            <div className="text-xs font-bold text-white uppercase tracking-wide">
              {isReviewRequired ? '🔍 MANUAL REVIEW' : '✅ APPROVE / ROUTINE CLEARANCE'}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {explanation.recommended_action}
            </p>
          </div>
        </div>

      </div>

      {/* 5. "VIEW AI EXPLANATION" COLLAPSIBLE SECTION */}
      <div className="border-t border-slate-800 pt-3">
        <button
          onClick={() => setShowDetailedExplanation(!showDetailedExplanation)}
          className="flex items-center justify-between w-full py-2 px-3 rounded-xl bg-slate-950/60 hover:bg-slate-950 text-slate-300 hover:text-white text-xs font-semibold border border-slate-800 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{showDetailedExplanation ? 'Hide Detailed AI Explanation' : 'View AI Explanation Details'}</span>
          </div>
          {showDetailedExplanation ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {showDetailedExplanation && (
          <div className="mt-3 p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4 animate-in fade-in-50 duration-200">
            
            {/* Risk Synthesis Narrative */}
            <div className="space-y-1.5">
              <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                Risk Synthesis
              </h5>
              <p className="text-xs text-slate-300 leading-relaxed">
                {explanation.summary}
              </p>
            </div>

            {/* Key Signals & Observed Facts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-900">
              {/* Key Signals */}
              <div className="space-y-1.5">
                <h6 className="text-[11px] font-bold text-amber-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <AlertTriangle className="w-3 h-3" />
                  Key Signals
                </h6>
                <ul className="space-y-1 text-xs text-slate-300">
                  {explanation.key_signals.map((sig, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{sig}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Observed Facts */}
              <div className="space-y-1.5">
                <h6 className="text-[11px] font-bold text-sky-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <CheckCircle2 className="w-3 h-3" />
                  Observed Facts
                </h6>
                <ul className="space-y-1 text-xs text-slate-300">
                  {explanation.observed_evidence.map((ev, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-sky-400 font-bold">•</span>
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Uncertainty / Limitations */}
            {explanation.uncertainty && (
              <div className="pt-2 border-t border-slate-900 text-[11px] text-slate-400">
                <strong className="text-slate-300">Limitations: </strong>
                <span>{explanation.uncertainty}</span>
              </div>
            )}

          </div>
        )}
      </div>

      {/* 6. AI RESPONSIBILITY NOTICE (Visually Secondary) */}
      <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 leading-relaxed flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
        <p>
          <span className="font-semibold text-slate-300">AI Responsibility Notice: </span>
          AI-generated explanation based on structured graph evidence. Risk scores and review thresholds are computed by the deterministic GraphSAGE risk engine. Shared infrastructure alone does not prove fraud.
        </p>
      </div>

    </div>
  );
};
