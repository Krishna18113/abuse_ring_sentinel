import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown, 
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

import { fetchRiskQueue } from '../services/api';
import { RiskBadge } from '../components/RiskBadge';

export const RiskQueue: React.FC = () => {
  const navigate = useNavigate();

  // Filters state
  const [search, setSearch] = useState('');
  const [riskLevel, setRiskLevel] = useState<string>('');
  const [reviewRequired, setReviewRequired] = useState<boolean | undefined>(undefined);
  const [sort, setSort] = useState<'desc' | 'asc'>('desc');
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ['risk-queue', page, limit, riskLevel, reviewRequired, search, sort],
    queryFn: () => fetchRiskQueue({
      limit,
      offset: page * limit,
      risk_level: riskLevel || undefined,
      review_required: reviewRequired,
      search: search || undefined,
      sort,
    }),
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(0); // Reset to page 0 on filter change
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Merchant Risk Review Queue</h1>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized customer triage queue ranked by model-estimated risk probabilities and coordination signals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Total in Queue:</span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-white font-mono font-bold text-xs border border-slate-700">
            {data?.total.toLocaleString() || '...'}
          </span>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[300px]">
          
          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by Customer ID (e.g. C_46...)"
              value={search}
              onChange={handleSearchChange}
              className="w-full bg-slate-950/80 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={riskLevel}
              onChange={(e) => { setRiskLevel(e.target.value); setPage(0); }}
              className="bg-slate-950/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Risk Tiers</option>
              <option value="HIGH">High Risk (≥ 70%)</option>
              <option value="MEDIUM">Medium Risk (30–70%)</option>
              <option value="LOW">Low Risk (&lt; 30%)</option>
            </select>
          </div>

          {/* Review Required Filter */}
          <select
            value={reviewRequired === undefined ? '' : reviewRequired ? 'true' : 'false'}
            onChange={(e) => {
              const val = e.target.value;
              setReviewRequired(val === '' ? undefined : val === 'true');
              setPage(0);
            }}
            className="bg-slate-950/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Review Statuses</option>
            <option value="true">Review Required Only (≥ 60%)</option>
            <option value="false">Clear Profiles Only</option>
          </select>
        </div>

        {/* Sort Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSort(sort === 'desc' ? 'asc' : 'desc')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span>Sort: {sort === 'desc' ? 'Highest Risk First' : 'Lowest Risk First'}</span>
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-3 px-4">Customer ID</th>
                <th className="py-3 px-4">Risk Probability</th>
                <th className="py-3 px-4">Risk Tier</th>
                <th className="py-3 px-4">Primary Observed Signals</th>
                <th className="py-3 px-4">Review Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading risk queue profiles...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No customers match the current filter criteria.
                  </td>
                </tr>
              ) : (
                data?.items.map((item) => (
                  <tr 
                    key={item.customer_id} 
                    onClick={() => navigate(`/customers/${item.customer_id}`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      {item.customer_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2 font-mono">
                        <span className={`font-bold ${item.risk_probability >= 0.70 ? 'text-rose-400' : item.risk_probability >= 0.30 ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {(item.risk_probability * 100).toFixed(2)}%
                        </span>
                        <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${item.risk_probability >= 0.70 ? 'bg-rose-500' : item.risk_probability >= 0.30 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                            style={{ width: `${Math.min(item.risk_probability * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <RiskBadge level={item.risk_level} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div className="flex flex-wrap gap-1">
                        {item.primary_signals.map((sig, i) => (
                          <span 
                            key={i} 
                            className={`px-2 py-0.5 rounded text-[10px] font-sans ${
                              sig.includes('Device') || sig.includes('Links') 
                                ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' 
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {sig}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {item.review_required ? (
                        <span className="inline-flex items-center gap-1 text-rose-400 text-xs font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Review Required
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-semibold">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Clear
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/customers/${item.customer_id}`);
                        }}
                        className="px-3 py-1 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-colors"
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

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="font-bold text-slate-200">{page * limit + 1}</span> to{' '}
            <span className="font-bold text-slate-200">{Math.min((page + 1) * limit, data?.total || 0)}</span> of{' '}
            <span className="font-bold text-slate-200">{data?.total.toLocaleString() || 0}</span> customers
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 text-xs font-medium border border-slate-700 flex items-center gap-1"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              Previous
            </button>
            <span className="px-2 text-slate-500 font-mono">
              Page {page + 1} of {Math.max(1, totalPages)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages - 1}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 text-xs font-medium border border-slate-700 flex items-center gap-1"
            >
              Next
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
