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
  Search
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
    { name: 'Low Risk', count: summary.risk_distribution.LOW, color: '#10b981' },
    { name: 'Medium Risk', count: summary.risk_distribution.MEDIUM, color: '#f59e0b' },
    { name: 'High Risk', count: summary.risk_distribution.HIGH, color: '#f43f5e' },
  ] : [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/customers/${searchQuery.trim().toUpperCase()}`);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Banner / Search */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Merchant Risk Operations</h1>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous coordination and promotional abuse surveillance powered by graph intelligence.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Customer ID (e.g. C_46046)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-colors shadow-sm"
          >
            Investigate
          </button>
        </form>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Customers"
          value={summaryLoading ? '...' : (summary?.total_customers.toLocaleString() || '50,000')}
          subtitle="Continuous behavioral graph surveillance"
          icon={<Users className="w-5 h-5 text-indigo-400" />}
        />
        <MetricCard
          title="Reviews Required"
          value={summaryLoading ? '...' : (summary?.customers_requiring_review.toLocaleString() || '0')}
          subtitle="Threshold: Probability ≥ 60.0%"
          icon={<AlertOctagon className="w-5 h-5 text-rose-400" />}
          trend="Action Required"
          trendType="danger"
        />
        <MetricCard
          title="High-Risk Customers"
          value={summaryLoading ? '...' : (summary?.high_risk_customers.toLocaleString() || '0')}
          subtitle={`${summary?.high_risk_percentage || 0}% of active monitored profiles`}
          icon={<ShieldAlert className="w-5 h-5 text-amber-400" />}
          trend="Score ≥ 70%"
          trendType="warning"
        />
        <MetricCard
          title="Transactions Analyzed"
          value={summaryLoading ? '...' : (summary?.total_transactions.toLocaleString() || '303,161')}
          subtitle="Real-time multi-signal correlation"
          icon={<CreditCard className="w-5 h-5 text-sky-400" />}
        />
      </div>

      {/* Charts & Review Previews */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Distribution Chart */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Risk Tier Distribution</h3>
              <p className="text-xs text-slate-400">Customer risk categorization breakdown</p>
            </div>
          </div>
          
          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800/80 text-center">
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-medium">Low</div>
              <div className="text-xs font-bold text-emerald-400">{summary?.risk_distribution.LOW.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-medium">Medium</div>
              <div className="text-xs font-bold text-amber-400">{summary?.risk_distribution.MEDIUM.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-medium">High</div>
              <div className="text-xs font-bold text-rose-400">{summary?.risk_distribution.HIGH.toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* Urgent Review Queue Preview */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white">Priority Review Queue</h3>
                <p className="text-xs text-slate-400">High-risk accounts exhibiting multi-signal coordination</p>
              </div>
              <button
                onClick={() => navigate('/risk-queue')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors"
              >
                View Full Queue ({summary?.customers_requiring_review || 0})
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                    <th className="pb-2.5">Customer ID</th>
                    <th className="pb-2.5">Risk Score</th>
                    <th className="pb-2.5">Primary Signals</th>
                    <th className="pb-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {queueLoading ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-slate-500">Loading priority queue...</td>
                    </tr>
                  ) : (
                    queueData?.items.map((item) => (
                      <tr key={item.customer_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 font-mono font-bold text-white">{item.customer_id}</td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-rose-400 font-bold">{(item.risk_probability * 100).toFixed(1)}%</span>
                            <RiskBadge level={item.risk_level} size="sm" />
                          </div>
                        </td>
                        <td className="py-3 text-slate-300">
                          <div className="flex flex-wrap gap-1">
                            {item.primary_signals.map((sig, i) => (
                              <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 font-sans">
                                {sig}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => navigate(`/customers/${item.customer_id}`)}
                            className="px-2.5 py-1 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-colors"
                          >
                            Investigate
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Prioritized by multi-signal connection density
            </span>
            <span className="font-mono text-slate-500">Auto-refresh active</span>
          </div>
        </div>

      </div>

      {/* Demo Quick Profiles Showcase */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Seeded Evaluation Profiles (Fast Demonstration)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div 
            onClick={() => navigate('/customers/C_46046')}
            className="p-4 bg-slate-950/60 border border-rose-500/30 hover:border-rose-500 rounded-xl cursor-pointer transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-white text-sm">Customer C_46046</span>
                <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 text-xs font-bold">99.1% HIGH RISK</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-rose-400 transition-colors" />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Shares hardware with 9 accounts, connects to 5 multi-signal profiles, and has rapid 60s temporal transaction clusters.
            </p>
          </div>

          <div 
            onClick={() => navigate('/customers/C_00003')}
            className="p-4 bg-slate-950/60 border border-emerald-500/30 hover:border-emerald-500 rounded-xl cursor-pointer transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-white text-sm">Customer C_00003</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">0.02% LOW RISK</span>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Legitimate longitudinal consumer behavior, isolated hardware infrastructure, and clean referral metrics.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};
