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
  CheckCircle, 
  AlertOctagon, 
  Calendar,
  Share2,
  Clock,
  Sparkles,
  ShieldCheck,
  Ban,
  Check
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
    refetch: refetchExplanation 
  } = useQuery({
    queryKey: ['explanation', cId],
    queryFn: () => fetchCustomerExplanation(cId),
  });

  if (investigationLoading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-xs text-slate-400 font-mono">Assembling graph evidence dossier for {cId}...</p>
      </div>
    );
  }

  if (investigationError || !investigation) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center max-w-lg mx-auto mt-12 space-y-4">
        <AlertOctagon className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-base font-bold text-white">Investigation Dossier Unavailable</h2>
        <p className="text-xs text-slate-400">
          Could not locate customer profile <span className="font-mono text-slate-200">{cId}</span> in graph database.
        </p>
        <button
          onClick={() => navigate('/risk-queue')}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold"
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

  return (
    <div className="space-y-6 pb-16">
      
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Queue
        </button>

        <div className="text-xs text-slate-500 font-mono">
          Last Indexed: {investigation.summary?.investigation_timestamp || 'Live'}
        </div>
      </div>

      {/* Hero Header */}
      <div className={`p-6 rounded-2xl border ${
        isHighRisk 
          ? 'bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border-rose-500/40 shadow-lg shadow-rose-950/20' 
          : 'bg-slate-900/90 border-slate-800'
      }`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          {/* Profile Identity & Risk Score */}
          <div className="flex flex-wrap items-center gap-5">
            <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center border font-mono font-bold shadow-md ${
              isHighRisk 
                ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' 
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
            }`}>
              <span className="text-lg leading-none">{((risk.risk_probability || 0) * 100).toFixed(0)}%</span>
              <span className="text-[9px] uppercase tracking-wider text-slate-400 mt-0.5">Risk</span>
            </div>

            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-extrabold text-white tracking-tight font-mono">{cId}</h1>
                <RiskBadge level={risk.risk_level || 'LOW'} reviewRequired={risk.review_required} size="lg" />
              </div>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5" />
                Account Created: <span className="text-slate-300">{investigation.customer?.account_created_at || 'Active'}</span> 
                {investigation.customer?.account_age_days != null && ` (${investigation.customer.account_age_days.toFixed(0)} days active)`}
              </p>
            </div>
          </div>

          {/* Decision Support Review Actions */}
          <div className="flex flex-wrap items-center gap-2.5">
            {simulatedStatus ? (
              <div className="px-4 py-2 bg-indigo-950/60 border border-indigo-500/40 rounded-xl text-xs text-indigo-300 flex items-center gap-2 font-medium">
                <Check className="w-4 h-4 text-indigo-400" />
                <span>Action Applied: <strong>{simulatedStatus}</strong></span>
              </div>
            ) : (
              <>
                <button
                  onClick={() => setSimulatedStatus('Flagged for Manual Investigation')}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-950/40 transition-colors"
                >
                  <Ban className="w-3.5 h-3.5" />
                  Flag for Manual Review
                </button>
                <button
                  onClick={() => setSimulatedStatus('Approved / Exception Granted')}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Approve Account
                </button>
              </>
            )}
          </div>

        </div>
      </div>

      {/* Core Layout: Left Grid (2/3) & Right Intelligence (1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Observable Evidence, Graph, Timeline */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Observable Signal Cards */}
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Observable Graph Evidence
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Shared Device Card */}
              <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                    <Smartphone className="w-4 h-4 text-sky-400" />
                    <span>Shared Hardware</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    strengths.shared_device?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {strengths.shared_device?.detected ? `${strengths.shared_device.strength} STRENGTH` : 'NONE'}
                  </span>
                </div>
                {signals.shared_devices && signals.shared_devices.length > 0 ? (
                  <div className="space-y-1 text-xs">
                    {signals.shared_devices.map((d, i) => (
                      <div key={i} className="text-slate-300">
                        Device <span className="font-mono text-white font-bold">{d.device_id}</span> shared with{' '}
                        <strong className="text-rose-400">{d.customer_count}</strong> other accounts ({d.transaction_count} total txs).
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Dedicated hardware footprint. No shared device nodes.</p>
                )}
              </div>

              {/* Shared IP Card */}
              <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                    <Globe className="w-4 h-4 text-indigo-400" />
                    <span>Network IP Address</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    strengths.shared_ip?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {strengths.shared_ip?.detected ? `${strengths.shared_ip.strength} STRENGTH` : 'NONE'}
                  </span>
                </div>
                {signals.shared_ips && signals.shared_ips.length > 0 ? (
                  <div className="space-y-1 text-xs">
                    {signals.shared_ips.map((ip, i) => (
                      <div key={i} className="text-slate-300">
                        IP <span className="font-mono text-white font-bold">{ip.ip_address}</span> shared with{' '}
                        <strong className="text-amber-400">{ip.customer_count}</strong> other accounts.
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Isolated IP address. No multi-account clustering.</p>
                )}
              </div>

              {/* Coupon Coordination Card */}
              <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                    <Tag className="w-4 h-4 text-amber-400" />
                    <span>Promotional Campaigns</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    strengths.coupon_coordination?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {strengths.coupon_coordination?.detected ? `${strengths.coupon_coordination.strength} STRENGTH` : 'NORMAL'}
                  </span>
                </div>
                {signals.coupon_coordination && signals.coupon_coordination.length > 0 ? (
                  <div className="space-y-1 text-xs">
                    {signals.coupon_coordination.slice(0, 2).map((c, i) => (
                      <div key={i} className="text-slate-300">
                        <span className="font-mono text-white font-bold">{c.coupon_id}</span> ({c.customer_count} users). 
                        {c.shared_device_count > 0 && (
                          <span className="text-rose-400 font-semibold"> {c.shared_device_count} device overlaps.</span>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No promotional coupons redeemed.</p>
                )}
              </div>

              {/* Referral Network Card */}
              <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                    <Share2 className="w-4 h-4 text-rose-400" />
                    <span>Referral Network</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    strengths.referral_coordination?.detected ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {strengths.referral_coordination?.detected ? `${strengths.referral_coordination.strength} STRENGTH` : 'NORMAL'}
                  </span>
                </div>
                <div className="text-xs space-y-1 text-slate-300">
                  <div>Referrer: <span className="font-mono font-bold text-white">{signals.referral_connections?.referrer_id || 'None (Organic)'}</span></div>
                  <div>Referred Accounts: <strong className="text-slate-200">{signals.referral_connections?.referral_out_degree ?? 0}</strong></div>
                  <div>Local Component Tree: <strong className="text-indigo-400">{signals.referral_connections?.referral_component_size ?? 0}</strong> nodes</div>
                </div>
              </div>

            </div>
          </div>

          {/* Interactive React Flow Graph */}
          {graphLoading || !graphData ? (
            <div className="h-[460px] bg-slate-900/80 border border-slate-800 rounded-xl flex items-center justify-center text-slate-500 text-xs font-mono">
              Loading interactive network graph...
            </div>
          ) : (
            <NetworkGraph graphData={graphData} />
          )}

          {/* Temporal Evidence Timeline */}
          <EvidenceTimeline clusters={signals.temporal_clusters || []} />

        </div>

        {/* Right 1 Col: AI Explanation & Ranked Connections */}
        <div className="space-y-6">
          
          {/* Gemini AI Explanation Panel */}
          <AIExplanationCard
            explanation={explanation || null}
            loading={explanationLoading}
            onRefresh={() => refetchExplanation()}
          />

          {/* Multi-Signal Connections Ranked List */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Multi-Signal Connections
              </h3>
              <span className="text-xs font-mono text-indigo-400">
                {multi_signal_connections.length} Accounts
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mb-3">
              Accounts sharing multiple independent connection types with this target
            </p>

            {multi_signal_connections.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No multi-signal customer overlap detected.</p>
            ) : (
              <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                {multi_signal_connections.map((conn, idx) => (
                  <div
                    key={idx}
                    onClick={() => navigate(`/customers/${conn.connected_customer}`)}
                    className="p-3 bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 rounded-lg cursor-pointer transition-all"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono font-bold text-white text-xs">{conn.connected_customer}</span>
                      <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 text-[10px] font-bold border border-rose-500/20">
                        {conn.signal_count} Coordinated Signals
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {conn.signals.map((sig, sIdx) => (
                        <span key={sIdx} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400">
                          {sig.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Behavioral Stats Panel */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3 text-xs">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Account Transaction Metrics
            </h3>
            <div className="grid grid-cols-2 gap-2 text-slate-300">
              <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/60">
                <div className="text-[10px] text-slate-500 uppercase">Transactions</div>
                <div className="font-mono text-sm font-bold text-white mt-0.5">{behavior.transaction_count ?? 0}</div>
              </div>
              <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/60">
                <div className="text-[10px] text-slate-500 uppercase">Total Spend</div>
                <div className="font-mono text-sm font-bold text-white mt-0.5">INR {(behavior.total_transaction_amount || 0).toFixed(2)}</div>
              </div>
              <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/60">
                <div className="text-[10px] text-slate-500 uppercase">Avg Amount</div>
                <div className="font-mono text-sm font-bold text-white mt-0.5">INR {(behavior.average_transaction_amount || 0).toFixed(2)}</div>
              </div>
              <div className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800/60">
                <div className="text-[10px] text-slate-500 uppercase">Night Activity</div>
                <div className="font-mono text-sm font-bold text-white mt-0.5">{((behavior.night_transaction_ratio || 0) * 100).toFixed(0)}%</div>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
