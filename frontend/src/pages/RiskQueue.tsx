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
  AlertTriangle,
  RotateCcw,
  Users,
  ShieldCheck,
  ChevronDown
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

  const isFiltered = search !== '' || riskLevel !== '' || reviewRequired !== undefined;

  const resetFilters = () => {
    setSearch('');
    setRiskLevel('');
    setReviewRequired(undefined);
    setSort('desc');
    setPage(0);
  };

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
    setPage(0);
  };

  return (
    <div className="space-y-6 pb-16">
      
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Merchant Risk Review Queue</h1>
          <p className="text-xs text-slate-400 mt-1">
            Prioritized operational triage queue ranked by GraphSAGE risk probabilities and coordinated graph signals.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Total in Scope:</span>
            <span className="font-mono font-bold text-white">
              {data?.total.toLocaleString() || '...'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Filter Controls Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          
          <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[320px]">
            {/* Search Box */}
            <div className="relative flex-1 min-w-[220px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search Customer ID (e.g. C_46046)"
                value={search}
                onChange={handleSearchChange}
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono transition-colors"
              />
            </div>

            {/* Risk Tier Filter */}
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={riskLevel}
                onChange={(e) => { setRiskLevel(e.target.value); setPage(0); }}
                className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
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
              className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="">All Review Statuses</option>
              <option value="true">Review Required Only (≥ 60%)</option>
              <option value="false">Clear Profiles Only (&lt; 60%)</option>
            </select>

            {/* Reset Filters Button */}
            {isFiltered && (
              <button
                onClick={resetFilters}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors border border-slate-700"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>

          {/* Sort Direction Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSort(sort === 'desc' ? 'asc' : 'desc')}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-950 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-indigo-400" />
              <span>Sort: {sort === 'desc' ? 'Highest Risk First' : 'Lowest Risk First'}</span>
            </button>
          </div>

        </div>
      </div>

      {/* 3. Main Data Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-3.5 px-5">Customer ID</th>
                <th className="py-3.5 px-5">Risk Probability</th>
                <th className="py-3.5 px-5">Risk Tier</th>
                <th className="py-3.5 px-5">Primary Graph Signals</th>
                <th className="py-3.5 px-5">Operational Status</th>
                <th className="py-3.5 px-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-slate-500">
                    <div className="space-y-2">
                      <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                      <p className="text-xs font-mono">Retrieving customer risk profiles...</p>
                    </div>
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                /* Empty State */
                <tr>
                  <td colSpan={6} className="py-16 text-center">
                    <div className="max-w-sm mx-auto space-y-3">
                      <div className="w-10 h-10 rounded-2xl bg-slate-800/80 flex items-center justify-center mx-auto text-slate-400">
                        <Users className="w-5 h-5" />
                      </div>
                      <h3 className="text-sm font-bold text-white">No Matching Customers Found</h3>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        No customer accounts match your current search and filter criteria. Try broadening your filter range or resetting filters.
                      </p>
                      {isFiltered && (
                        <button
                          onClick={resetFilters}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-colors shadow-sm"
                        >
                          Clear All Filters
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                data?.items.map((item) => (
                  <tr 
                    key={item.customer_id} 
                    onClick={() => navigate(`/customers/${item.customer_id}`)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-4 px-5 font-mono font-bold text-white group-hover:text-indigo-300 transition-colors">
                      {item.customer_id}
                    </td>
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2.5 font-mono">
                        <span className={`font-bold ${
                          item.risk_probability >= 0.70 
                            ? 'text-rose-400' 
                            : item.risk_probability >= 0.30 
                            ? 'text-amber-400' 
                            : 'text-emerald-400'
                        }`}>
                          {(item.risk_probability * 100).toFixed(2)}%
                        </span>
                        <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${
                              item.risk_probability >= 0.70 
                                ? 'bg-rose-500' 
                                : item.risk_probability >= 0.30 
                                ? 'bg-amber-500' 
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(item.risk_probability * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-5">
                      <RiskBadge level={item.risk_level} size="sm" />
                    </td>
                    <td className="py-4 px-5 text-slate-300">
                      <div className="flex flex-wrap gap-1.5">
                        {item.primary_signals.map((sig, i) => (
                          <span 
                            key={i} 
                            className={`px-2 py-0.5 rounded-md text-[10px] font-sans font-medium ${
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
                    <td className="py-4 px-5">
                      {item.review_required ? (
                        <span className="inline-flex items-center gap-1.5 text-rose-400 text-xs font-bold">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Review Required
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                          Routine Profile
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-5 text-right">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 group-hover:text-indigo-300 group-hover:translate-x-0.5 transition-all">
                        <span>Investigate</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 4. Pagination Footer */}
        {data && data.total > limit && (
          <div className="px-5 py-4 bg-slate-950/70 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="text-slate-400">
              Showing <span className="font-mono text-white">{page * limit + 1}</span> to{' '}
              <span className="font-mono text-white">{Math.min((page + 1) * limit, data.total)}</span> of{' '}
              <span className="font-mono text-white">{data.total.toLocaleString()}</span> customers
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700 transition-colors"
                title="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="text-slate-400 px-2 font-mono">
                Page <strong className="text-white">{page + 1}</strong> of <strong>{totalPages}</strong>
              </span>

              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700 transition-colors"
                title="Next Page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};
