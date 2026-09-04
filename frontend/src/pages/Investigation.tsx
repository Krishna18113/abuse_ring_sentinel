import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  Smartphone, 
  Globe, 
  Tag, 
  Users, 
  Activity, 
  AlertOctagon, 
  Calendar,
  Share2,
  Clock,
  Sparkles,
  ShieldCheck,
  Ban,
  Check,
  ChevronRight,
  AlertTriangle,
  CreditCard,
  Moon,
  Info
} from 'lucide-react';

import { 
  fetchCustomerInvestigation, 
  fetchCustomerGraph, 
  fetchCustomerExplanation 
} from '../services/api';
import { RiskBadge } from '../components/RiskBadge';
import { NetworkGraph } from '../components/NetworkGraph';
import { EvidenceTimeline } from '../components/EvidenceTimeline';
import { AIExplanationCard } from '../components/AIExplanationCard';

export const Investigation: React.FC = () => {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const cId = customerId || 'C_46046';

  const [simulatedStatus, setSimulatedStatus] = useState<string | null>(null);

  // Queries
  const { 
    data: investigation, 
    isLoading: investigationLoading, 
    error: investigationError 
  } = useQuery({
    queryKey: ['investigation', cId],
    queryFn: () => fetchCustomerInvestigation(cId),
  });

  const { 
    data: graphData, 
    isLoading: graphLoading 
  } = useQuery({
    queryKey: ['graph', cId],
    queryFn: () => fetchCustomerGraph(cId),
  });

  const { 
    data: explanation, 
    isLoading: explanationLoading, 
    isFetching: explanationFetching,
    refetch: refetchExplanation 
  } = useQuery({
    queryKey: ['explanation', cId],
    queryFn: () => fetchCustomerExplanation(cId),
  });

  // Loading State
  if (investigationLoading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-9 h-9 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <h3 className="text-sm font-bold text-white">Retrieving Graph Dossier for {cId}...</h3>
        <p className="text-xs text-slate-400 font-mono">Traversing multi-hop infrastructure connections and pre-computed risk metrics</p>
      </div>
    );
  }

  // Error State
  if (investigationError || !investigation) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 text-center max-w-lg mx-auto mt-12 space-y-4 shadow-xl">
        <div className="w-12 h-12 bg-rose-500/10 rounded-2xl flex items-center justify-center mx-auto text-rose-400 border border-rose-500/20">
          <AlertOctagon className="w-6 h-6" />
        </div>
        <h2 className="text-base font-bold text-white">Investigation Dossier Unavailable</h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Could not locate customer profile <span className="font-mono text-slate-200 font-semibold">{cId}</span> in the active graph database. Please verify the customer ID or return to the triage queue.
        </p>
        <button
          onClick={() => navigate('/risk-queue')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md transition-colors"
        >
          Return to Risk Queue
        </button>
      </div>
    );
  }

  const risk = investigation.risk || { risk_probability: 0, review_required: false, risk_level: 'LOW' };
  const behavior = investigation.behavior || {
    transaction_count: 0,
    total_transaction_amount: 0,
    average_transaction_amount: 0,
    median_transaction_amount: 0,
    coupon_usage_count: 0,
    unique_coupons_used: 0,
    referrals_made: 0,
    was_referred: false,
    active_days: 0,
    night_transaction_ratio: 0
  };
  const signals = investigation.signals || {
    shared_devices: [],
    shared_ips: [],
    coupon_coordination: [],
    referral_connections: { referrer_id: null, referral_out_degree: 0, referral_component_size: 0 },
    temporal_clusters: []
  };
  const strengths = investigation.strengths || {
    shared_device: { detected: false, strength: 'LOW' },
    shared_ip: { detected: false, strength: 'LOW' },
    coupon_coordination: { detected: false, strength: 'LOW' },
    referral_coordination: { detected: false, strength: 'LOW' },
    temporal_coordination: { detected: false, strength: 'LOW' }
  };
  const multi_signal_connections = investigation.multi_signal_connections || [];
  const isHighRisk = (risk.risk_probability || 0) >= 0.70;
  const isReviewRequired = risk.review_required;

  // Build deterministic plain-English primary reason
  let primaryReason = "Routine Organic Profile";
  let reasonDetails = "Standard consumer transaction cadence with dedicated infrastructure and no multi-account overlaps.";

  if (isReviewRequired) {
    const parts: string[] = [];
    if (strengths.shared_device?.detected) parts.push("shared physical hardware");
    if (strengths.shared_ip?.detected) parts.push("network IP clustering");
    if (strengths.coupon_coordination?.detected) parts.push("promotional campaign coordination");
    if (strengths.temporal_coordination?.detected) parts.push("synchronized transaction bursts");
    if (strengths.referral_coordination?.detected) parts.push("referral tree concentration");

    primaryReason = isHighRisk ? "High Risk — Review Recommended" : "Moderate Risk — Review Suggested";
    reasonDetails = parts.length > 0 
      ? `Shares ${parts.join(', ')} with ${investigation.summary?.connected_customer_count || 'multiple'} connected accounts.`
      : "Multi-signal structural overlap observed across graph neighborhood.";
  }

  return (
    <div className="space-y-6 pb-16">
      
      {/* 1. Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/risk-queue')}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Risk Queue</span>
        </button>

        <div className="text-xs text-slate-400 font-mono">
          Last Indexed: {investigation.summary?.investigation_timestamp || 'Live Active State'}
        </div>
      </div>

      {/* 2. Strong Investigation Header (Answers 1: WHO, 2: HOW RISKY, 3: SHOULD REVIEW, 4: WHY FLAGGED, 8: ACTION) */}
      <div className={`p-6 rounded-2xl border ${
        isHighRisk 
          ? 'bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border-rose-500/40 shadow-xl shadow-rose-950/20' 
          : isReviewRequired
          ? 'bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border-amber-500/40 shadow-xl shadow-amber-950/20'
          : 'bg-slate-900/90 border-slate-800'
      }`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          {/* Left: Score Box & Customer Identity */}
          <div className="flex flex-wrap items-start sm:items-center gap-5">
            
            {/* Risk Probability Callout */}
            <div className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center border font-mono font-bold shadow-lg flex-shrink-0 ${
              isHighRisk 
                ? 'bg-rose-500/20 text-rose-400 border-rose-500/50 ring-2 ring-rose-500/20' 
                : isReviewRequired
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/50 ring-2 ring-amber-500/20'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
            }`}>
              <span className="text-2xl leading-none">{((risk.risk_probability || 0) * 100).toFixed(1)}%</span>
              <span className="text-[9px] uppercase tracking-wider text-slate-400 mt-1 font-sans font-semibold">GNN Score</span>
            </div>

            {/* Identity & Status */}
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-extrabold text-white tracking-tight font-mono">{cId}</h1>
                <RiskBadge level={risk.risk_level || 'LOW'} reviewRequired={risk.review_required} size="lg" />
                
                {isReviewRequired ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold font-sans">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Review Required
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-bold font-sans">
                    <Check className="w-3.5 h-3.5" />
                    Routine Account
                  </span>
                )}
              </div>

              {/* Primary Reason for Investigation */}
              <div className="space-y-0.5">
                <div className="text-xs font-bold text-white">{primaryReason}</div>
                <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">{reasonDetails}</p>
              </div>

              <div className="text-[11px] text-slate-400 flex items-center gap-2 pt-0.5 font-sans">
                <Calendar className="w-3 h-3 text-slate-500" />
                <span>Account Created: <strong className="text-slate-300 font-mono">{investigation.customer?.account_created_at || 'Active'}</strong></span>
                {investigation.customer?.account_age_days != null && (
                  <span className="text-slate-500">({investigation.customer.account_age_days.toFixed(0)} days active)</span>
                )}
              </div>
            </div>

          </div>

          {/* Right: Decision Support Review Actions (Step 8: Actions) */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 flex-shrink-0">
            {simulatedStatus ? (
              <div className="px-4 py-2.5 bg-indigo-950/60 border border-indigo-500/40 rounded-xl text-xs text-indigo-300 flex items-center gap-2 font-semibold">
                <Check className="w-4 h-4 text-indigo-400" />
                <span>Action Applied: <strong>{simulatedStatus}</strong></span>
              </div>
            ) : (
              <>
                <button
                  onClick={() => setSimulatedStatus('Flagged for Manual Review')}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-md shadow-rose-950/40 transition-colors"
                >
                  <Ban className="w-4 h-4" />
                  <span>Flag for Manual Review</span>
                </button>
                <button
                  onClick={() => setSimulatedStatus('Approved / Exception Granted')}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Approve Account</span>
                </button>
              </>
            )}
          </div>

        </div>
      </div>

      {/* 3. Section: Evidence Map & Evidence Summary (Answers 5: WHAT EVIDENCE, 6: CONNECTED ACCOUNTS) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Graph Evidence & Network Architecture
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            {investigation.summary?.signal_count || 0} Evidence Signals Detected
          </span>
        </div>

        {graphLoading || !graphData ? (
          <div className="h-[490px] bg-slate-900/90 border border-slate-800 rounded-2xl flex items-center justify-center text-slate-400 text-xs font-mono">
            <div className="text-center space-y-2">
              <div className="w-7 h-7 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p>Constructing hierarchical evidence map...</p>
            </div>
          </div>
        ) : (
          <NetworkGraph 
            graphData={graphData} 
            multiSignalConnections={multi_signal_connections}
            signals={signals}
            strengths={strengths}
          />
        )}
      </section>

      {/* 4. Section: AI Risk Explanation (Answers 7: WHAT DOES AI SUMMARIZE) */}
      <section className="space-y-3">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          AI Risk Explanation & Synthesis
        </h2>
        
        <AIExplanationCard
          explanation={explanation || null}
          loading={explanationLoading || explanationFetching}
          onRefresh={() => refetchExplanation()}
          risk={risk}
          signals={signals}
          strengths={strengths}
          summary={investigation.summary}
          multiSignalConnections={multi_signal_connections}
        />
      </section>

      {/* 5. Section: Two-Column Secondary Details (Temporal Coordination & Customer Behavioral Footprint) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Temporal Burst Timeline */}
        <div className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Temporal Coordination Timeline
          </h2>
          <EvidenceTimeline clusters={signals.temporal_clusters || []} />
        </div>

        {/* Customer Behavioral Profile Footprint */}
        <div className="space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Customer Profile & Spending Behavior
          </h2>
          
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <CreditCard className="w-3.5 h-3.5 text-sky-400" />
                  <span>Transactions</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  {behavior.transaction_count}
                </div>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Total Volume</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  ₹{behavior.total_transaction_amount.toLocaleString()}
                </div>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <Tag className="w-3.5 h-3.5 text-amber-400" />
                  <span>Coupons Used</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  {behavior.coupon_usage_count}
                </div>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <Moon className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Night Ratio</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  {((behavior.night_transaction_ratio || 0) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <Share2 className="w-3.5 h-3.5 text-rose-400" />
                  <span>Referrals Made</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  {behavior.referrals_made}
                </div>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>Active Days</span>
                </div>
                <div className="text-lg font-bold text-white font-mono">
                  {behavior.active_days}
                </div>
              </div>
            </div>

            {/* Multi-Signal Overlaps Quick List */}
            {multi_signal_connections.length > 0 && (
              <div className="pt-4 border-t border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-rose-400" />
                    High-Priority Multi-Signal Overlaps ({multi_signal_connections.length})
                  </span>
                  <span className="text-slate-400 font-mono text-[11px]">Ranked by Strength</span>
                </div>

                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {multi_signal_connections.slice(0, 5).map((mc, idx) => (
                    <div
                      key={idx}
                      onClick={() => navigate(`/customers/${mc.connected_customer}`)}
                      className="p-2.5 bg-slate-950/80 border border-slate-800 hover:border-rose-500/50 rounded-xl text-xs cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-rose-300">{mc.connected_customer}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold font-mono">
                          {mc.signal_count}x Signals
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>

      </div>

    </div>
  );
};
