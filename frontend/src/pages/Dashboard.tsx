import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  AlertOctagon, 
  ShieldAlert, 
  CreditCard, 
  ArrowRight, 
  Sparkles,
  Search,
  CheckCircle,
  ChevronRight,
  TrendingUp,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';

import { fetchDashboardSummary, fetchRiskQueue } from '../services/api';
import { MetricCard } from '../components/MetricCard';
import { RiskBadge } from '../components/RiskBadge';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = React.useState('');

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
  });

  const { data: queueData, isLoading: queueLoading } = useQuery({
    queryKey: ['risk-queue-preview'],
    queryFn: () => fetchRiskQueue({ limit: 6, sort: 'desc', review_required: true }),
  });

  const chartData = summary ? [
    { name: 'Low Risk', count: summary.risk_distribution.LOW, color: '#10b981', desc: '< 30% Score' },
    { name: 'Medium Risk', count: summary.risk_distribution.MEDIUM, color: '#f59e0b', desc: '30–70% Score' },
    { name: 'High Risk', count: summary.risk_distribution.HIGH, color: '#f43f5e', desc: '≥ 70% Score' },
  ] : [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/customers/${searchQuery.trim().toUpperCase()}`);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      
      {/* 1. Hero Search & Surveillance Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight">Merchant Risk Operations</h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-semibold">
              Surveillance Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time graph surveillance detecting coordinated merchant abuse, shared hardware, and promotional rings.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Quick Investigate ID (e.g. C_46046)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono shadow-inner"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-colors shadow-md shadow-indigo-950/40"
          >
            Investigate
          </button>
        </form>
      </div>

      {/* 2. Key Operational Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Customers"
          value={summaryLoading ? '...' : (summary?.total_customers.toLocaleString() || '50,000')}
          subtitle="Heterogeneous graph surveillance"
          icon={<Users className="w-5 h-5 text-indigo-400" />}
        />
        <MetricCard
          title="Reviews Required"
          value={summaryLoading ? '...' : (summary?.customers_requiring_review.toLocaleString() || '0')}
          subtitle="Operational Threshold: Probability ≥ 60%"
          icon={<AlertOctagon className="w-5 h-5 text-rose-400" />}
          trend="Immediate Action"
          trendType="danger"
        />
        <MetricCard
          title="High-Risk Customers"
          value={summaryLoading ? '...' : (summary?.high_risk_customers.toLocaleString() || '0')}
          subtitle={`${summary?.high_risk_percentage || 0}% of active merchant accounts`}
          icon={<ShieldAlert className="w-5 h-5 text-amber-400" />}
          trend="Score ≥ 70%"
          trendType="warning"
        />
        <MetricCard
          title="Transactions Monitored"
          value={summaryLoading ? '...' : (summary?.total_transactions.toLocaleString() || '303,161')}
          subtitle="Multi-signal relationship tracking"
          icon={<CreditCard className="w-5 h-5 text-sky-400" />}
        />
      </div>

      {/* 3. Judge Demo Launcher & Quick Seeds */}
      <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-5 shadow-lg shadow-indigo-950/20">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white tracking-tight">Quick Evaluation Profiles</h3>
          </div>
          <span className="text-[11px] text-slate-400">One-click live demo seeds</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          
          {/* Seed 1: C_00003 */}
          <div
            onClick={() => navigate('/customers/C_00003')}
            className="p-3.5 bg-slate-950/80 border border-slate-800 hover:border-emerald-500/50 rounded-xl cursor-pointer transition-all hover:bg-slate-950 group"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono font-bold text-emerald-400 text-xs">C_00003 (Low-Risk Control)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-semibold font-mono">
                0.02% Score
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              Organic consumer with dedicated hardware and no multi-account clusters. Demonstrates low false-positive baseline.
            </p>
          </div>

          {/* Seed 2: C_46046 */}
          <div
            onClick={() => navigate('/customers/C_46046')}
            className="p-3.5 bg-slate-950/80 border border-slate-800 hover:border-rose-500/50 rounded-xl cursor-pointer transition-all hover:bg-slate-950 group"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono font-bold text-rose-400 text-xs">C_46046 (High-Risk Device Ring)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold font-mono">
                99.06% Score
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              Shares physical hardware D32830 with 9 accounts and 3 synchronized transaction burst clusters (&lt; 60s).
            </p>
          </div>

          {/* Seed 3: C_46021 */}
          <div
            onClick={() => navigate('/customers/C_46021')}
            className="p-3.5 bg-slate-950/80 border border-slate-800 hover:border-rose-500/50 rounded-xl cursor-pointer transition-all hover:bg-slate-950 group"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono font-bold text-rose-400 text-xs">C_46021 (Multi-Signal Ring)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold font-mono">
                99.30% Score
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              High-degree multi-signal coordination across shared device D32888, network gateway, and coupon promotion.
            </p>
          </div>

        </div>
      </div>

      {/* 4. Charts & Priority Review Queue Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Distribution Chart */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Portfolio Risk Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Triage segmentation across 50,000 active customer accounts</p>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#020617', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }}
                  formatter={(value: any) => [Number(value).toLocaleString() + ' accounts', 'Count']}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center">
            {chartData.map((item, idx) => (
              <div key={idx} className="p-2 bg-slate-950/60 rounded-xl">
                <div className="text-[10px] text-slate-400 font-medium">{item.name}</div>
                <div className="text-xs font-bold text-white font-mono mt-0.5">{item.count?.toLocaleString() || 0}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Review Queue Preview */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight">Priority Review Queue Preview</h3>
                <p className="text-xs text-slate-400 mt-0.5">Highest priority accounts requiring immediate risk officer review</p>
              </div>
              <button
                onClick={() => navigate('/risk-queue')}
                className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
              >
                <span>View Full Queue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider font-semibold">
                    <th className="pb-2.5">Customer ID</th>
                    <th className="pb-2.5">Risk Score</th>
                    <th className="pb-2.5">Primary Signals</th>
                    <th className="pb-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {queueLoading ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-slate-500 font-mono">
                        Loading priority queue...
                      </td>
                    </tr>
                  ) : (
                    queueData?.items.map((item) => (
                      <tr 
                        key={item.customer_id}
                        onClick={() => navigate(`/customers/${item.customer_id}`)}
                        className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                      >
                        <td className="py-3 font-mono font-bold text-white">
                          {item.customer_id}
                        </td>
                        <td className="py-3">
                          <span className="font-mono font-bold text-rose-400">
                            {(item.risk_probability * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3 text-slate-300">
                          <div className="flex flex-wrap gap-1">
                            {item.primary_signals.slice(0, 2).map((sig, i) => (
                              <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                                {sig}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 text-right">
                          <span className="text-xs text-indigo-400 font-semibold hover:text-indigo-300">
                            Investigate →
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Filter threshold: GraphSAGE Probability ≥ 60.0%</span>
            <button
              onClick={() => navigate('/risk-queue')}
              className="text-xs font-semibold text-slate-200 hover:text-white"
            >
              Explore all {summary?.customers_requiring_review.toLocaleString() || '...'} accounts in queue →
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
